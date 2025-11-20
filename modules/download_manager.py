"""Download manager for handling YouTube downloads"""
import asyncio
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

from core.service_manager import BaseService, ServiceConfig
from database.db_manager import DatabaseManager
from config.settings import settings
from utils.logger import logger
from modules.metadata_manager import MetadataManager


class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class DownloadTask:
    """Download task data class"""
    id: str
    url: str
    output_path: str
    format_id: Optional[str] = None
    quality: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    speed: float = 0.0
    eta: Optional[int] = None
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'output_path': self.output_path,
            'format_id': self.format_id,
            'quality': self.quality,
            'status': self.status.value,
            'progress': self.progress,
            'speed': self.speed,
            'eta': self.eta,
            'downloaded_bytes': self.downloaded_bytes,
            'total_bytes': self.total_bytes,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'priority': self.priority,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class DownloadManager(BaseService):
    """Download manager service"""

    def __init__(
        self,
        config: ServiceConfig,
        db_manager: DatabaseManager,
        auth_manager=None
    ):
        """Initialize download manager

        Args:
            config: Service configuration
            db_manager: Database manager instance
            auth_manager: Authentication manager instance (optional)
        """
        super().__init__(config, "DownloadManager")
        self.db_manager = db_manager
        self.metadata_manager = MetadataManager(config, db_manager)
        self.auth_manager = auth_manager
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.paused_downloads: Dict[str, DownloadTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.workers: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        self._cookie_file = None
        self._load_browser_cookies()

    def _load_browser_cookies(self):
        """Load cookies from browser for yt-dlp"""
        if self.auth_manager:
            try:
                cookie_file = self.auth_manager.get_cookies_for_ytdlp()
                if cookie_file:
                    self._cookie_file = cookie_file
                    logger.info(f"Loaded browser cookies from: {cookie_file}")
                else:
                    logger.info("No browser cookies found, downloading may fail for age-restricted or members-only content")
            except Exception as e:
                logger.warning(f"Failed to load browser cookies: {e}")

    def _get_default_ydl_opts(self, task: DownloadTask) -> Dict[str, Any]:
        """Get default yt-dlp options

        Args:
            task: Download task

        Returns:
            yt-dlp options dictionary
        """
        # Build output template based on settings
        base_path = Path(task.output_path)

        if settings.ORGANIZE_BY_CHANNEL and settings.DIRECTORY_STRUCTURE == "channel":
            # チャンネル別ディレクトリ: downloads/ChannelName/VideoTitle.ext
            output_template = str(base_path / '%(uploader)s' / '%(title)s.%(ext)s')
        elif settings.DIRECTORY_STRUCTURE == "date":
            # 日付別ディレクトリ: downloads/2025/01/VideoTitle.ext
            output_template = str(base_path / '%(upload_date>%Y)s' / '%(upload_date>%m)s' / '%(title)s.%(ext)s')
        elif settings.DIRECTORY_STRUCTURE == "channel_date":
            # チャンネル・日付別: downloads/ChannelName/2025-01/VideoTitle.ext
            output_template = str(base_path / '%(uploader)s' / '%(upload_date>%Y-%m)s' / '%(title)s.%(ext)s')
        else:
            # フラット構造: downloads/VideoTitle.ext
            output_template = str(base_path / '%(title)s.%(ext)s')

        # More flexible format selection
        if task.format_id:
            format_str = task.format_id
        else:
            # Default: best quality with fallbacks
            format_str = 'bestvideo+bestaudio/best'

        opts = {
            'format': format_str,
            'outtmpl': output_template,
            'progress_hooks': [lambda d: self._progress_hook(task.id, d)],
            'postprocessor_hooks': [lambda d: self._postprocessor_hook(task.id, d)],
            'concurrent_fragment_downloads': settings.FRAGMENT_DOWNLOADS,
            'nocheckcertificate': True,
            'quiet': not settings.DEBUG,
            'no_warnings': not settings.DEBUG,
            'extract_flat': False,
            'ignoreerrors': False,
            'retries': self.config.retry_count,
            'fragment_retries': self.config.retry_count,
            'socket_timeout': self.config.timeout,
            'merge_output_format': 'mp4',  # Merge to mp4 if needed
            'restrictfilenames': False,  # Allow Unicode characters
            'windowsfilenames': True,  # Safe filenames for Windows
        }

        # Add proxy if configured
        if settings.HTTP_PROXY:
            opts['proxy'] = settings.HTTP_PROXY

        # Add cookies from browser if available
        if self._cookie_file:
            opts['cookiefile'] = self._cookie_file
            logger.debug(f"Using cookie file: {self._cookie_file}")

        return opts

    def _progress_hook(self, task_id: str, d: Dict[str, Any]) -> None:
        """Progress hook for yt-dlp

        Args:
            task_id: Task ID
            d: Progress data
        """
        if task_id not in self.active_downloads:
            return

        task = self.active_downloads[task_id]

        if d['status'] == 'downloading':
            task.downloaded_bytes = d.get('downloaded_bytes', 0)
            task.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

            if task.total_bytes > 0:
                task.progress = (task.downloaded_bytes / task.total_bytes) * 100

            task.speed = d.get('speed', 0) or 0
            task.eta = d.get('eta')

            # Emit progress event
            self.emit_event('progress', {
                'task_id': task_id,
                'progress': task.progress,
                'speed': task.speed,
                'eta': task.eta,
                'downloaded_bytes': task.downloaded_bytes,
                'total_bytes': task.total_bytes,
            })

        elif d['status'] == 'finished':
            task.progress = 100.0
            task.status = DownloadStatus.PROCESSING
            logger.info(f"Download finished, now processing: {task.metadata.get('title', task.url)}")

    def _postprocessor_hook(self, task_id: str, d: Dict[str, Any]) -> None:
        """Post-processor hook for yt-dlp

        Args:
            task_id: Task ID
            d: Post-processor data
        """
        if task_id not in self.active_downloads:
            return

        task = self.active_downloads[task_id]

        if d['status'] == 'processing':
            logger.info(f"Post-processing: {d.get('postprocessor', 'unknown')}")

    async def start(self) -> None:
        """Start download manager"""
        logger.info("Starting Download Manager...")

        # Start worker tasks
        for i in range(self.config.max_workers):
            worker = asyncio.create_task(self._download_worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info(f"Started {self.config.max_workers} download workers")

    async def stop(self) -> None:
        """Stop download manager"""
        logger.info("Stopping Download Manager...")
        self._shutdown_event.set()

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("Download Manager stopped")

    async def add_download(
        self,
        url: str,
        output_path: Optional[str] = None,
        format_id: Optional[str] = None,
        quality: Optional[str] = None,
        priority: int = 5
    ) -> DownloadTask:
        """Add download to queue

        Args:
            url: Video URL
            output_path: Output directory path
            format_id: Format ID
            quality: Quality preference
            priority: Download priority (1-10, higher is more important)

        Returns:
            Created download task
        """
        # Check for duplicates
        if self.db_manager.check_duplicate(url):
            logger.warning(f"URL already downloaded: {url}")
            raise ValueError("This video has already been downloaded")

        # Create task
        task = DownloadTask(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path or str(settings.DOWNLOAD_DIR),
            format_id=format_id,
            quality=quality,
            priority=priority
        )

        # Add to database queue
        self.db_manager.add_to_queue({
            'id': task.id,
            'url': task.url,
            'priority': task.priority,
            'output_path': task.output_path,
            'format_id': task.format_id,
            'quality': task.quality
        })

        # Add to queue (priority queue uses negative priority for max-heap)
        await self.queue.put((-priority, task.created_at, task))

        logger.info(f"Added download to queue: {url} (priority: {priority})")
        self.emit_event('download:added', task.to_dict())

        return task

    async def _download_worker(self, worker_id: str) -> None:
        """Download worker task

        Args:
            worker_id: Worker ID
        """
        logger.info(f"Worker {worker_id} started")

        while not self._shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                try:
                    _, _, task = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process task
                self.active_downloads[task.id] = task
                task.status = DownloadStatus.DOWNLOADING
                task.started_at = datetime.now()

                logger.info(f"Worker {worker_id} processing: {task.url}")

                # Update database
                self.db_manager.update_queue_status(
                    task.id,
                    'downloading',
                    started_at=task.started_at
                )

                # Execute download
                await self._execute_download(task)

                # Remove from active downloads
                if task.id in self.active_downloads:
                    del self.active_downloads[task.id]

                # Mark queue task as done
                self.queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")

    async def _execute_download(self, task: DownloadTask) -> None:
        """Execute download task

        Args:
            task: Download task
        """
        try:
            opts = self._get_default_ydl_opts(task)

            # Extract info first
            with yt_dlp.YoutubeDL(opts) as ydl:
                logger.info(f"Extracting info for: {task.url}")
                info = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    ydl.extract_info,
                    task.url,
                    False  # download=False
                )

                task.metadata = info
                logger.info(f"Extracted info: {info.get('title', 'Unknown')}")

                # Download
                logger.info(f"Starting download: {info.get('title', task.url)}")
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    ydl.download,
                    [task.url]
                )

            # Mark as completed
            task.status = DownloadStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0

            logger.info(f"Download completed: {task.metadata.get('title', task.url)}")

            # Update database
            self.db_manager.update_queue_status(
                task.id,
                'completed',
                completed_at=task.completed_at,
                progress=100.0
            )

            # Add to history
            download_info = task.metadata.copy()
            download_info.update({
                'id': task.id,
                'url': task.url,
                'file_path': task.output_path,
            })
            self.db_manager.add_download_history(download_info)

            # Emit completion event
            self.emit_event('download:completed', task.to_dict())

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            task.retry_count += 1

            logger.error(f"Download failed: {task.url} - {e}")

            # Update database
            self.db_manager.update_queue_status(
                task.id,
                'failed',
                completed_at=task.completed_at,
                error_message=task.error_message
            )

            # Emit failure event
            self.emit_event('download:failed', task.to_dict())

            # Retry if not exceeded
            if task.retry_count < self.config.retry_count:
                logger.info(f"Retrying download ({task.retry_count}/{self.config.retry_count}): {task.url}")
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                await self.queue.put((-task.priority, task.created_at, task))

    async def pause_download(self, task_id: str) -> bool:
        """Pause a download

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        if task_id in self.active_downloads:
            task = self.active_downloads[task_id]
            task.status = DownloadStatus.PAUSED
            self.paused_downloads[task_id] = task
            del self.active_downloads[task_id]

            self.db_manager.update_queue_status(task_id, 'paused')
            logger.info(f"Paused download: {task_id}")
            return True

        return False

    async def resume_download(self, task_id: str) -> bool:
        """Resume a paused download

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        if task_id in self.paused_downloads:
            task = self.paused_downloads[task_id]
            task.status = DownloadStatus.PENDING
            del self.paused_downloads[task_id]

            await self.queue.put((-task.priority, task.created_at, task))
            self.db_manager.update_queue_status(task_id, 'pending')

            logger.info(f"Resumed download: {task_id}")
            return True

        return False

    async def cancel_download(self, task_id: str) -> bool:
        """Cancel a download

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        # Check active downloads
        if task_id in self.active_downloads:
            task = self.active_downloads[task_id]
            task.status = DownloadStatus.CANCELLED
            del self.active_downloads[task_id]

            self.db_manager.update_queue_status(task_id, 'cancelled')
            logger.info(f"Cancelled active download: {task_id}")
            return True

        # Check paused downloads
        if task_id in self.paused_downloads:
            del self.paused_downloads[task_id]
            self.db_manager.update_queue_status(task_id, 'cancelled')
            logger.info(f"Cancelled paused download: {task_id}")
            return True

        return False

    def get_active_downloads(self) -> List[Dict[str, Any]]:
        """Get active downloads

        Returns:
            List of active download dictionaries
        """
        return [task.to_dict() for task in self.active_downloads.values()]

    def get_download_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get download status

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None
        """
        if task_id in self.active_downloads:
            return self.active_downloads[task_id].to_dict()

        if task_id in self.paused_downloads:
            return self.paused_downloads[task_id].to_dict()

        return None

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading

        Args:
            url: Video URL

        Returns:
            Video information dictionary
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                ydl.extract_info,
                url,
                False
            )

        return info

    async def add_channel_download(
        self,
        channel_url: str,
        output_path: Optional[str] = None,
        format_id: Optional[str] = None,
        quality: Optional[str] = None,
        priority: int = 5,
        playlist_items: Optional[str] = None
    ) -> List[DownloadTask]:
        """Add all videos from a channel to download queue

        Args:
            channel_url: Channel URL
            output_path: Output directory path
            format_id: Format ID
            quality: Quality preference
            priority: Download priority
            playlist_items: Playlist items range (e.g., "1-10,15,20-25")

        Returns:
            List of created download tasks
        """
        logger.info(f"Fetching channel videos: {channel_url}")

        # Normalize channel URL (remove /videos, /shorts, etc.)
        import re
        normalized_url = re.sub(r'/(videos|shorts|streams|playlists|community|about).*$', '', channel_url)
        logger.info(f"Normalized channel URL: {normalized_url}")

        # Get channel videos
        opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
        }

        if playlist_items:
            opts['playlist_items'] = playlist_items

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    ydl.extract_info,
                    normalized_url + '/videos',  # Explicitly request videos tab
                    False
                )

            if not info:
                raise ValueError("Failed to fetch channel information")

            # Get all video entries
            entries = info.get('entries', [])
            if not entries:
                raise ValueError("No videos found in channel")

            logger.info(f"Found {len(entries)} videos in channel: {info.get('title', 'Unknown')}")

            # Add each video to download queue
            tasks = []
            for i, entry in enumerate(entries):
                try:
                    # Construct proper video URL from ID
                    video_id = entry.get('id')
                    if not video_id:
                        logger.warning(f"Skipping entry without ID: {entry.get('title')}")
                        continue

                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    if self.db_manager.check_duplicate(video_url):
                        logger.debug(f"Skipping already downloaded: {entry.get('title')}")
                        continue

                    task = await self.add_download(
                        url=video_url,
                        output_path=output_path,
                        format_id=format_id,
                        quality=quality,
                        priority=priority
                    )
                    tasks.append(task)
                    logger.info(f"Added video {i+1}/{len(entries)}: {entry.get('title')}")
                except ValueError as e:
                    # Skip duplicates
                    logger.debug(f"Skipping duplicate: {entry.get('title')}")
                except Exception as e:
                    logger.error(f"Failed to add video {entry.get('title')}: {e}")

            logger.info(f"Added {len(tasks)} videos to download queue")
            self.emit_event('channel:added', {
                'channel_url': channel_url,
                'channel_title': info.get('title'),
                'total_videos': len(entries),
                'added_videos': len(tasks)
            })

            return tasks

        except Exception as e:
            logger.error(f"Failed to add channel download: {e}")
            raise

    async def add_playlist_download(
        self,
        playlist_url: str,
        output_path: Optional[str] = None,
        format_id: Optional[str] = None,
        quality: Optional[str] = None,
        priority: int = 5,
        playlist_items: Optional[str] = None
    ) -> List[DownloadTask]:
        """Add all videos from a playlist to download queue

        Args:
            playlist_url: Playlist URL
            output_path: Output directory path
            format_id: Format ID
            quality: Quality preference
            priority: Download priority
            playlist_items: Playlist items range (e.g., "1-10,15,20-25")

        Returns:
            List of created download tasks
        """
        logger.info(f"Fetching playlist videos: {playlist_url}")

        # Get playlist videos
        opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
        }

        if playlist_items:
            opts['playlist_items'] = playlist_items

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    ydl.extract_info,
                    playlist_url,
                    False
                )

            if not info:
                raise ValueError("Failed to fetch playlist information")

            # Get all video entries
            entries = info.get('entries', [])
            if not entries:
                raise ValueError("No videos found in playlist")

            logger.info(f"Found {len(entries)} videos in playlist: {info.get('title', 'Unknown')}")

            # Add each video to download queue
            tasks = []
            for i, entry in enumerate(entries):
                try:
                    # Construct proper video URL from ID
                    video_id = entry.get('id')
                    if not video_id:
                        logger.warning(f"Skipping entry without ID: {entry.get('title')}")
                        continue

                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    if self.db_manager.check_duplicate(video_url):
                        logger.debug(f"Skipping already downloaded: {entry.get('title')}")
                        continue

                    task = await self.add_download(
                        url=video_url,
                        output_path=output_path,
                        format_id=format_id,
                        quality=quality,
                        priority=priority
                    )
                    tasks.append(task)
                    logger.info(f"Added video {i+1}/{len(entries)}: {entry.get('title')}")
                except ValueError as e:
                    # Skip duplicates
                    logger.debug(f"Skipping duplicate: {entry.get('title')}")
                except Exception as e:
                    logger.error(f"Failed to add video {entry.get('title')}: {e}")

            logger.info(f"Added {len(tasks)} videos to download queue")
            self.emit_event('playlist:added', {
                'playlist_url': playlist_url,
                'playlist_title': info.get('title'),
                'total_videos': len(entries),
                'added_videos': len(tasks)
            })

            return tasks

        except Exception as e:
            logger.error(f"Failed to add playlist download: {e}")
            raise
