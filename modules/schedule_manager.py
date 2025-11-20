"""Schedule manager for automated download tasks"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import uuid
import yt_dlp

from core.service_manager import BaseService, ServiceConfig
from database.db_manager import DatabaseManager
from utils.logger import logger


class ScheduleManager(BaseService):
    """Schedule manager for automated tasks"""

    def __init__(
        self,
        config: ServiceConfig,
        db_manager: DatabaseManager,
        download_manager: Any  # Avoid circular import
    ):
        """Initialize schedule manager

        Args:
            config: Service configuration
            db_manager: Database manager instance
            download_manager: Download manager instance
        """
        super().__init__(config, "ScheduleManager")
        self.db_manager = db_manager
        self.download_manager = download_manager
        self.scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        """Start schedule manager"""
        logger.info("Starting Schedule Manager...")

        # Load scheduled tasks from database
        tasks = self.db_manager.get_scheduled_tasks(enabled_only=True)

        for task in tasks:
            await self._register_task(task)

        # Start scheduler
        self.scheduler.start()
        logger.info(f"Schedule Manager started with {len(tasks)} tasks")

    async def stop(self) -> None:
        """Stop schedule manager"""
        logger.info("Stopping Schedule Manager...")
        self.scheduler.shutdown()
        logger.info("Schedule Manager stopped")

    async def _register_task(self, task: Any) -> None:
        """Register a scheduled task

        Args:
            task: Scheduled task model
        """
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)

            self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[task],
                id=task.id,
                name=task.name,
                replace_existing=True
            )

            logger.info(f"Registered scheduled task: {task.name}")

        except Exception as e:
            logger.error(f"Failed to register task {task.name}: {e}")

    async def add_scheduled_task(
        self,
        name: str,
        cron_expression: str,
        task_type: str,
        parameters: Dict[str, Any],
        channel_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new scheduled task

        Args:
            name: Task name
            cron_expression: Cron expression
            task_type: Task type (channel_download, playlist_download, etc.)
            parameters: Task parameters
            channel_id: Associated channel ID
            description: Task description

        Returns:
            Created task dictionary
        """
        task_id = str(uuid.uuid4())

        # Add to database
        task = self.db_manager.add_scheduled_task({
            'id': task_id,
            'name': name,
            'description': description,
            'cron_expression': cron_expression,
            'task_type': task_type,
            'parameters': parameters,
            'channel_id': channel_id
        })

        # Register with scheduler
        await self._register_task(task)

        logger.info(f"Added scheduled task: {name}")
        return self._task_to_dict(task)

    async def _execute_task(self, task: Any) -> None:
        """Execute a scheduled task

        Args:
            task: Scheduled task model
        """
        logger.info(f"Executing scheduled task: {task.name}")

        try:
            # Update status to running
            self.db_manager.update_task_status(task.id, 'running')

            params = task.get_parameters()

            # Execute based on task type
            if task.task_type == 'channel_download':
                await self._download_channel_updates(params)
            elif task.task_type == 'playlist_download':
                await self._download_playlist(params)
            elif task.task_type == 'check_updates':
                await self._check_channel_updates(params)

            # Update status to success
            self.db_manager.update_task_status(task.id, 'success')
            logger.info(f"Task completed successfully: {task.name}")

            # Emit event
            self.emit_event('task:completed', {
                'task_id': task.id,
                'task_name': task.name
            })

        except Exception as e:
            logger.error(f"Task failed: {task.name} - {e}")
            self.db_manager.update_task_status(task.id, 'failed', str(e))

            # Emit event
            self.emit_event('task:failed', {
                'task_id': task.id,
                'task_name': task.name,
                'error': str(e)
            })

    async def _download_channel_updates(self, params: Dict[str, Any]) -> None:
        """Download new videos from channel

        Args:
            params: Task parameters
        """
        channel_url = params.get('channel_url')
        last_check = params.get('last_check')

        if not channel_url:
            raise ValueError("channel_url parameter is required")

        # Get channel videos
        opts = {
            'extract_flat': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

            if not info:
                return

            entries = info.get('entries', [])

            # Filter new videos
            if last_check:
                last_check_date = datetime.fromisoformat(last_check) if isinstance(last_check, str) else last_check
            else:
                last_check_date = datetime.now() - timedelta(days=1)

            new_videos = []
            for entry in entries:
                upload_date_str = entry.get('upload_date')
                if upload_date_str:
                    upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                    if upload_date > last_check_date:
                        new_videos.append(entry)

            logger.info(f"Found {len(new_videos)} new videos from channel")

            # Add to download queue
            for video in new_videos:
                try:
                    await self.download_manager.add_download(
                        url=video['url'],
                        output_path=params.get('output_path'),
                        quality=params.get('quality'),
                        priority=params.get('priority', 5)
                    )
                except Exception as e:
                    logger.error(f"Failed to add video to queue: {e}")

    async def _download_playlist(self, params: Dict[str, Any]) -> None:
        """Download playlist

        Args:
            params: Task parameters
        """
        playlist_url = params.get('playlist_url')
        playlist_items = params.get('playlist_items')  # e.g., "1-10,15,20-25"

        if not playlist_url:
            raise ValueError("playlist_url parameter is required")

        # Get playlist videos
        opts = {
            'extract_flat': True,
            'quiet': True,
        }

        if playlist_items:
            opts['playlist_items'] = playlist_items

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

            if not info:
                return

            entries = info.get('entries', [])
            logger.info(f"Found {len(entries)} videos in playlist")

            # Add to download queue
            for entry in entries:
                try:
                    await self.download_manager.add_download(
                        url=entry['url'],
                        output_path=params.get('output_path'),
                        quality=params.get('quality'),
                        priority=params.get('priority', 5)
                    )
                except Exception as e:
                    logger.error(f"Failed to add video to queue: {e}")

    async def _check_channel_updates(self, params: Dict[str, Any]) -> None:
        """Check for channel updates and notify

        Args:
            params: Task parameters
        """
        channel_url = params.get('channel_url')

        if not channel_url:
            raise ValueError("channel_url parameter is required")

        # Get latest video
        opts = {
            'extract_flat': True,
            'quiet': True,
            'playlistend': 1,  # Only get latest video
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

            if info and info.get('entries'):
                latest_video = info['entries'][0]

                # Emit notification event
                self.emit_event('new_video', {
                    'channel': info.get('channel', 'Unknown'),
                    'video_title': latest_video.get('title'),
                    'video_url': latest_video.get('url'),
                    'upload_date': latest_video.get('upload_date')
                })

    async def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        try:
            # Remove from scheduler
            self.scheduler.remove_job(task_id)

            # Remove from database (mark as disabled)
            with self.db_manager.get_session() as session:
                task = session.query(self.db_manager.db_manager.models.ScheduledTask).filter_by(id=task_id).first()
                if task:
                    task.enabled = False
                    session.commit()

            logger.info(f"Removed scheduled task: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove task {task_id}: {e}")
            return False

    async def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        with self.db_manager.get_session() as session:
            task = session.query(self.db_manager.db_manager.models.ScheduledTask).filter_by(id=task_id).first()
            if task:
                task.enabled = True
                session.commit()
                await self._register_task(task)
                logger.info(f"Enabled task: {task_id}")
                return True

        return False

    async def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        try:
            self.scheduler.pause_job(task_id)

            with self.db_manager.get_session() as session:
                task = session.query(self.db_manager.db_manager.models.ScheduledTask).filter_by(id=task_id).first()
                if task:
                    task.enabled = False
                    session.commit()

            logger.info(f"Disabled task: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to disable task {task_id}: {e}")
            return False

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all scheduled tasks

        Returns:
            List of task dictionaries
        """
        tasks = self.db_manager.get_scheduled_tasks()
        return [self._task_to_dict(task) for task in tasks]

    def _task_to_dict(self, task: Any) -> Dict[str, Any]:
        """Convert task model to dictionary

        Args:
            task: Task model

        Returns:
            Task dictionary
        """
        return {
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'task_type': task.task_type,
            'cron_expression': task.cron_expression,
            'parameters': task.get_parameters(),
            'enabled': task.enabled,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'last_status': task.last_status,
            'run_count': task.run_count,
            'success_count': task.success_count,
            'failure_count': task.failure_count,
        }
