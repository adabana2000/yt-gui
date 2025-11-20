"""FastAPI main application"""
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uvicorn

from core.service_manager import service_manager, ServiceConfig
from database.db_manager import DatabaseManager
from modules.download_manager import DownloadManager
from modules.schedule_manager import ScheduleManager
from modules.auth_manager import AuthManager
from modules.encode_manager import EncodeManager
from modules.metadata_manager import MetadataManager
from core.event_bus import event_bus
from config.settings import settings
from utils.logger import logger


# Pydantic models for API
class DownloadRequest(BaseModel):
    url: str
    output_path: Optional[str] = None
    format_id: Optional[str] = None
    quality: Optional[str] = None
    priority: int = 5


class ScheduleTaskRequest(BaseModel):
    name: str
    cron_expression: str
    task_type: str
    parameters: Dict[str, Any]
    channel_id: Optional[str] = None
    description: Optional[str] = None


class EncodeRequest(BaseModel):
    input_file: str
    output_file: str
    codec: str = "h264"
    preset: str = "medium"
    bitrate: Optional[str] = None
    resolution: Optional[str] = None
    use_gpu: bool = True


class AudioExtractRequest(BaseModel):
    input_file: str
    output_file: str
    format: str = "mp3"
    bitrate: str = "192k"


# Create FastAPI app
app = FastAPI(
    title="YouTube Downloader API",
    description="API for YouTube Downloader application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers (initialized on startup)
db_manager: DatabaseManager = None
download_manager: DownloadManager = None
schedule_manager: ScheduleManager = None
auth_manager: AuthManager = None
encode_manager: EncodeManager = None
metadata_manager: MetadataManager = None

# WebSocket connections
websocket_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db_manager, download_manager, schedule_manager
    global auth_manager, encode_manager, metadata_manager

    logger.info("Starting YouTube Downloader API...")

    # Initialize managers
    db_manager = DatabaseManager()

    config = ServiceConfig(
        max_workers=settings.MAX_WORKERS,
        retry_count=settings.RETRY_COUNT,
        timeout=settings.TIMEOUT
    )

    download_manager = DownloadManager(config, db_manager)
    schedule_manager = ScheduleManager(config, db_manager, download_manager)
    auth_manager = AuthManager(config)
    encode_manager = EncodeManager(config)
    metadata_manager = MetadataManager(config, db_manager)

    # Register services
    service_manager.register_service("download", download_manager)
    service_manager.register_service("schedule", schedule_manager)
    service_manager.register_service("auth", auth_manager)
    service_manager.register_service("encode", encode_manager)
    service_manager.register_service("metadata", metadata_manager)

    # Register event listeners for WebSocket broadcasts
    event_bus.on("download:progress", broadcast_event, is_async=True)
    event_bus.on("download:completed", broadcast_event, is_async=True)
    event_bus.on("download:failed", broadcast_event, is_async=True)

    # Start all services
    await service_manager.start_all()

    logger.info("API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API...")
    await service_manager.stop_all()
    logger.info("API shutdown complete")


async def broadcast_event(data: Any):
    """Broadcast event to all WebSocket connections"""
    if websocket_connections:
        message = {"event": "update", "data": data}
        disconnected = []

        for ws in websocket_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            websocket_connections.remove(ws)


# ===== Download Endpoints =====

@app.post("/api/downloads", response_model=Dict[str, Any])
async def create_download(request: DownloadRequest):
    """Create a new download task"""
    try:
        task = await download_manager.add_download(
            url=request.url,
            output_path=request.output_path or str(settings.DOWNLOAD_DIR),
            format_id=request.format_id,
            quality=request.quality,
            priority=request.priority
        )
        return {"success": True, "task": task.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/downloads", response_model=Dict[str, Any])
async def get_downloads():
    """Get active downloads"""
    try:
        active = download_manager.get_active_downloads()
        queue_size = download_manager.queue.qsize()
        return {
            "success": True,
            "active": active,
            "queue_size": queue_size
        }
    except Exception as e:
        logger.error(f"Failed to get downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/downloads/{task_id}", response_model=Dict[str, Any])
async def get_download_status(task_id: str):
    """Get download status"""
    status = download_manager.get_download_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task": status}


@app.post("/api/downloads/{task_id}/pause")
async def pause_download(task_id: str):
    """Pause a download"""
    success = await download_manager.pause_download(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be paused")
    return {"success": True}


@app.post("/api/downloads/{task_id}/resume")
async def resume_download(task_id: str):
    """Resume a download"""
    success = await download_manager.resume_download(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be resumed")
    return {"success": True}


@app.delete("/api/downloads/{task_id}")
async def cancel_download(task_id: str):
    """Cancel a download"""
    success = await download_manager.cancel_download(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


@app.get("/api/downloads/info")
async def get_video_info(url: str):
    """Get video information without downloading"""
    try:
        info = await download_manager.get_video_info(url)
        return {"success": True, "info": info}
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== History Endpoints =====

@app.get("/api/history", response_model=Dict[str, Any])
async def get_history(
    skip: int = 0,
    limit: int = 100,
    channel_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get download history"""
    try:
        history = db_manager.get_download_history(
            skip=skip,
            limit=limit,
            channel_id=channel_id,
            search_query=search
        )
        return {
            "success": True,
            "history": [
                {
                    "id": h.id,
                    "url": h.url,
                    "title": h.title,
                    "channel_name": h.channel_name,
                    "file_path": h.file_path,
                    "download_date": h.download_date.isoformat() if h.download_date else None
                }
                for h in history
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get download statistics"""
    try:
        stats = db_manager.get_download_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Schedule Endpoints =====

@app.post("/api/schedules", response_model=Dict[str, Any])
async def create_schedule(request: ScheduleTaskRequest):
    """Create a new scheduled task"""
    try:
        task = await schedule_manager.add_scheduled_task(
            name=request.name,
            cron_expression=request.cron_expression,
            task_type=request.task_type,
            parameters=request.parameters,
            channel_id=request.channel_id,
            description=request.description
        )
        return {"success": True, "task": task}
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedules", response_model=Dict[str, Any])
async def get_schedules():
    """Get all scheduled tasks"""
    try:
        tasks = schedule_manager.get_tasks()
        return {"success": True, "tasks": tasks}
    except Exception as e:
        logger.error(f"Failed to get schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/schedules/{task_id}")
async def remove_schedule(task_id: str):
    """Remove a scheduled task"""
    success = await schedule_manager.remove_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


# ===== Encode Endpoints =====

@app.post("/api/encode/video")
async def encode_video(request: EncodeRequest, background_tasks: BackgroundTasks):
    """Encode video file"""
    background_tasks.add_task(
        encode_manager.encode_video,
        input_file=request.input_file,
        output_file=request.output_file,
        codec=request.codec,
        preset=request.preset,
        bitrate=request.bitrate,
        resolution=request.resolution,
        use_gpu=request.use_gpu
    )
    return {"success": True, "message": "Encoding started"}


@app.post("/api/encode/audio")
async def extract_audio(request: AudioExtractRequest, background_tasks: BackgroundTasks):
    """Extract audio from video"""
    background_tasks.add_task(
        encode_manager.extract_audio,
        input_file=request.input_file,
        output_file=request.output_file,
        format=request.format,
        bitrate=request.bitrate
    )
    return {"success": True, "message": "Audio extraction started"}


# ===== WebSocket Endpoint =====

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back
            await websocket.send_json({"echo": data})

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


# ===== Health Check =====

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": service_manager.get_service_status()
    }


# ===== Run Server =====

def run_server():
    """Run the API server"""
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    run_server()
