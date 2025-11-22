"""Database manager for YouTube Downloader"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from database.models import (
    Base, DownloadHistory, Channel, ScheduledTask,
    Playlist, DownloadQueue, Settings
)
from config.settings import settings
from utils.logger import logger


class DatabaseManager:
    """Database manager class"""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize database manager

        Args:
            db_url: Database URL (default: from settings)
        """
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(
            self.db_url,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # Prevent DetachedInstanceError when accessing objects after commit
        )
        self._create_tables()

    def _create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    @contextmanager
    def get_session(self) -> Session:
        """Get database session context manager

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    # ===== Download History =====

    def add_download_history(self, download_info: Dict[str, Any]) -> DownloadHistory:
        """Add download history

        Args:
            download_info: Download information dictionary

        Returns:
            Created download history record
        """
        with self.get_session() as session:
            history = DownloadHistory(
                id=download_info['id'],
                url=download_info['url'],
                title=download_info.get('title'),
                description=download_info.get('description'),
                channel_name=download_info.get('uploader'),
                channel_id=download_info.get('channel_id'),
                channel_url=download_info.get('channel_url'),
                file_path=download_info.get('file_path'),
                file_size=download_info.get('filesize'),
                duration=download_info.get('duration'),
                format=download_info.get('format'),
                resolution=download_info.get('resolution'),
                fps=download_info.get('fps'),
                vcodec=download_info.get('vcodec'),
                acodec=download_info.get('acodec'),
                thumbnail_url=download_info.get('thumbnail'),
                view_count=download_info.get('view_count'),
                like_count=download_info.get('like_count'),
            )
            history.set_metadata(download_info)
            session.add(history)
            session.flush()
            logger.info(f"Added download history: {download_info.get('title')}")
            return history

    def check_duplicate(self, url: str) -> bool:
        """Check if URL already downloaded

        Args:
            url: Video URL

        Returns:
            True if duplicate exists
        """
        with self.get_session() as session:
            exists = session.query(DownloadHistory).filter_by(url=url).first() is not None
            return exists

    def get_download_history(
        self,
        skip: int = 0,
        limit: int = 100,
        channel_id: Optional[str] = None,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DownloadHistory]:
        """Get download history with filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            channel_id: Filter by channel ID
            search_query: Search in title and description
            start_date: Filter from date
            end_date: Filter to date

        Returns:
            List of download history records
        """
        with self.get_session() as session:
            query = session.query(DownloadHistory)

            # Apply filters
            if channel_id:
                query = query.filter(DownloadHistory.channel_id == channel_id)

            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        DownloadHistory.title.like(search_pattern),
                        DownloadHistory.description.like(search_pattern)
                    )
                )

            if start_date:
                query = query.filter(DownloadHistory.download_date >= start_date)

            if end_date:
                query = query.filter(DownloadHistory.download_date <= end_date)

            # Order and paginate
            query = query.order_by(desc(DownloadHistory.download_date))
            query = query.offset(skip).limit(limit)

            return query.all()

    def get_download_stats(self) -> Dict[str, Any]:
        """Get download statistics

        Returns:
            Dictionary with statistics
        """
        with self.get_session() as session:
            total_count = session.query(func.count(DownloadHistory.id)).scalar()
            total_size = session.query(func.sum(DownloadHistory.file_size)).scalar() or 0
            total_duration = session.query(func.sum(DownloadHistory.duration)).scalar() or 0

            # Last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            week_count = session.query(func.count(DownloadHistory.id)).filter(
                DownloadHistory.download_date >= week_ago
            ).scalar()

            # Top channels
            top_channels = session.query(
                DownloadHistory.channel_name,
                func.count(DownloadHistory.id).label('count')
            ).group_by(DownloadHistory.channel_name).order_by(desc('count')).limit(10).all()

            return {
                'total_downloads': total_count,
                'total_size_bytes': total_size,
                'total_duration_seconds': total_duration,
                'downloads_last_week': week_count,
                'top_channels': [{'name': ch, 'count': cnt} for ch, cnt in top_channels]
            }

    # ===== Channel Management =====

    def add_channel(self, channel_info: Dict[str, Any]) -> Channel:
        """Add or update channel

        Args:
            channel_info: Channel information dictionary

        Returns:
            Channel record
        """
        with self.get_session() as session:
            channel = session.query(Channel).filter_by(
                channel_id=channel_info['channel_id']
            ).first()

            if channel:
                # Update existing
                channel.name = channel_info.get('name', channel.name)
                channel.description = channel_info.get('description', channel.description)
                channel.subscriber_count = channel_info.get('subscriber_count', channel.subscriber_count)
                channel.video_count = channel_info.get('video_count', channel.video_count)
                channel.thumbnail_url = channel_info.get('thumbnail', channel.thumbnail_url)
                channel.updated_at = datetime.now()
                logger.info(f"Updated channel: {channel.name}")
            else:
                # Create new
                channel = Channel(
                    id=channel_info.get('id', channel_info['channel_id']),
                    name=channel_info['name'],
                    url=channel_info['url'],
                    channel_id=channel_info['channel_id'],
                    description=channel_info.get('description'),
                    subscriber_count=channel_info.get('subscriber_count'),
                    video_count=channel_info.get('video_count'),
                    thumbnail_url=channel_info.get('thumbnail')
                )
                session.add(channel)
                logger.info(f"Added channel: {channel.name}")

            session.flush()
            return channel

    def get_channels(self, auto_download_only: bool = False) -> List[Channel]:
        """Get channels

        Args:
            auto_download_only: Filter only auto-download enabled channels

        Returns:
            List of channels
        """
        with self.get_session() as session:
            query = session.query(Channel)

            if auto_download_only:
                query = query.filter(Channel.auto_download == True)

            return query.order_by(Channel.name).all()

    def update_channel_settings(
        self,
        channel_id: str,
        auto_download: Optional[bool] = None,
        download_path: Optional[str] = None,
        quality_preference: Optional[str] = None
    ) -> Optional[Channel]:
        """Update channel settings

        Args:
            channel_id: Channel ID
            auto_download: Auto download flag
            download_path: Download path
            quality_preference: Quality preference

        Returns:
            Updated channel or None
        """
        with self.get_session() as session:
            channel = session.query(Channel).filter_by(channel_id=channel_id).first()

            if channel:
                if auto_download is not None:
                    channel.auto_download = auto_download
                if download_path is not None:
                    channel.download_path = download_path
                if quality_preference is not None:
                    channel.quality_preference = quality_preference
                channel.updated_at = datetime.now()
                session.flush()
                logger.info(f"Updated channel settings: {channel.name}")

            return channel

    # ===== Scheduled Tasks =====

    def add_scheduled_task(self, task_info: Dict[str, Any]) -> ScheduledTask:
        """Add scheduled task

        Args:
            task_info: Task information dictionary

        Returns:
            Created scheduled task
        """
        with self.get_session() as session:
            task = ScheduledTask(
                id=task_info['id'],
                name=task_info['name'],
                description=task_info.get('description'),
                task_type=task_info['task_type'],
                cron_expression=task_info['cron_expression'],
                channel_id=task_info.get('channel_id'),
                enabled=task_info.get('enabled', True)
            )
            task.set_parameters(task_info.get('parameters', {}))
            session.add(task)
            session.flush()
            logger.info(f"Added scheduled task: {task.name}")
            return task

    def get_scheduled_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """Get scheduled tasks

        Args:
            enabled_only: Filter only enabled tasks

        Returns:
            List of scheduled tasks
        """
        with self.get_session() as session:
            query = session.query(ScheduledTask)

            if enabled_only:
                query = query.filter(ScheduledTask.enabled == True)

            return query.order_by(ScheduledTask.next_run).all()

    def update_task_status(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ) -> Optional[ScheduledTask]:
        """Update scheduled task status

        Args:
            task_id: Task ID
            status: Task status (success, failed, running)
            error: Error message if failed

        Returns:
            Updated task or None
        """
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter_by(id=task_id).first()

            if task:
                task.last_run = datetime.now()
                task.last_status = status
                task.last_error = error
                task.run_count += 1

                if status == 'success':
                    task.success_count += 1
                elif status == 'failed':
                    task.failure_count += 1

                session.flush()

            return task

    # ===== Download Queue =====

    def add_to_queue(self, queue_info: Dict[str, Any]) -> DownloadQueue:
        """Add item to download queue

        Args:
            queue_info: Queue item information

        Returns:
            Created queue item
        """
        with self.get_session() as session:
            queue_item = DownloadQueue(
                id=queue_info['id'],
                url=queue_info['url'],
                priority=queue_info.get('priority', 5),
                output_path=queue_info.get('output_path'),
                format_id=queue_info.get('format_id'),
                quality=queue_info.get('quality')
            )
            if 'metadata' in queue_info:
                queue_item.set_metadata(queue_info['metadata'])
            session.add(queue_item)
            session.flush()
            return queue_item

    def get_queue_items(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DownloadQueue]:
        """Get queue items

        Args:
            status: Filter by status
            limit: Maximum number of items

        Returns:
            List of queue items
        """
        with self.get_session() as session:
            query = session.query(DownloadQueue)

            if status:
                query = query.filter(DownloadQueue.status == status)

            query = query.order_by(desc(DownloadQueue.priority), DownloadQueue.created_at)

            if limit:
                query = query.limit(limit)

            return query.all()

    def update_queue_status(
        self,
        queue_id: str,
        status: str,
        **kwargs
    ) -> Optional[DownloadQueue]:
        """Update queue item status

        Args:
            queue_id: Queue item ID
            status: New status
            **kwargs: Additional fields to update

        Returns:
            Updated queue item or None
        """
        with self.get_session() as session:
            item = session.query(DownloadQueue).filter_by(id=queue_id).first()

            if item:
                item.status = status

                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                if status == 'downloading' and not item.started_at:
                    item.started_at = datetime.now()
                elif status in ('completed', 'failed', 'cancelled'):
                    item.completed_at = datetime.now()

                session.flush()

            return item

    # ===== Settings =====

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value
        """
        with self.get_session() as session:
            setting = session.query(Settings).filter_by(key=key).first()
            if setting:
                return setting.get_value()
            return default

    def set_setting(self, key: str, value: Any, description: str = "") -> Settings:
        """Set setting value

        Args:
            key: Setting key
            value: Setting value
            description: Setting description

        Returns:
            Setting record
        """
        with self.get_session() as session:
            setting = session.query(Settings).filter_by(key=key).first()

            if setting:
                setting.set_value(value)
                setting.updated_at = datetime.now()
            else:
                setting = Settings(key=key, description=description)
                setting.set_value(value)
                session.add(setting)

            session.flush()
            return setting
