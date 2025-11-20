"""Database models for YouTube Downloader"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Float,
    Text, Boolean, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json


Base = declarative_base()


class DownloadHistory(Base):
    """Download history model"""
    __tablename__ = 'download_history'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, index=True, unique=True)
    title = Column(String)
    description = Column(Text)

    # Channel info
    channel_name = Column(String)
    channel_id = Column(String, index=True)
    channel_url = Column(String)

    # File info
    file_path = Column(String)
    file_size = Column(Integer)  # bytes
    duration = Column(Integer)  # seconds
    format = Column(String)
    resolution = Column(String)
    fps = Column(Integer)
    vcodec = Column(String)
    acodec = Column(String)

    # Download info
    download_date = Column(DateTime, default=datetime.now, index=True)
    download_speed = Column(Float)  # bytes/sec
    download_time = Column(Float)  # seconds

    # Metadata
    upload_date = Column(DateTime)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    thumbnail_url = Column(String)
    tags = Column(Text)  # JSON array
    categories = Column(Text)  # JSON array

    # Full metadata JSON
    video_metadata = Column(Text)  # JSON string

    # Indexes
    __table_args__ = (
        Index('idx_channel_date', 'channel_id', 'download_date'),
        Index('idx_title', 'title'),
    )

    def set_metadata(self, meta_dict: dict):
        """Set metadata from dictionary"""
        self.video_metadata = json.dumps(meta_dict, ensure_ascii=False)

    def get_metadata(self) -> dict:
        """Get metadata as dictionary"""
        if self.video_metadata:
            return json.loads(self.video_metadata)
        return {}


class Channel(Base):
    """Channel model for subscription management"""
    __tablename__ = 'channels'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    channel_id = Column(String, unique=True, index=True)

    # Settings
    auto_download = Column(Boolean, default=False)
    download_path = Column(String)
    format_preference = Column(String)  # JSON string
    quality_preference = Column(String)  # 1080p, 720p, etc.

    # Metadata
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    thumbnail_url = Column(String)

    # Status
    last_checked = Column(DateTime)
    last_video_date = Column(DateTime)
    enabled = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    scheduled_tasks = relationship("ScheduledTask", back_populates="channel")

    def set_format_preference(self, pref_dict: dict):
        """Set format preference from dictionary"""
        self.format_preference = json.dumps(pref_dict, ensure_ascii=False)

    def get_format_preference(self) -> dict:
        """Get format preference as dictionary"""
        if self.format_preference:
            return json.loads(self.format_preference)
        return {}


class ScheduledTask(Base):
    """Scheduled task model"""
    __tablename__ = 'scheduled_tasks'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Task configuration
    task_type = Column(String, nullable=False)  # channel_download, playlist_download, etc.
    cron_expression = Column(String)
    parameters = Column(Text)  # JSON string

    # Status
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime, index=True)
    last_status = Column(String)  # success, failed, running
    last_error = Column(Text)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Association
    channel_id = Column(String, ForeignKey('channels.id'))

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    channel = relationship("Channel", back_populates="scheduled_tasks")

    def set_parameters(self, param_dict: dict):
        """Set parameters from dictionary"""
        self.parameters = json.dumps(param_dict, ensure_ascii=False)

    def get_parameters(self) -> dict:
        """Get parameters as dictionary"""
        if self.parameters:
            return json.loads(self.parameters)
        return {}


class Playlist(Base):
    """Playlist model"""
    __tablename__ = 'playlists'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    playlist_id = Column(String, unique=True, index=True)

    # Metadata
    description = Column(Text)
    channel_name = Column(String)
    channel_id = Column(String)
    video_count = Column(Integer)
    thumbnail_url = Column(String)

    # Download settings
    auto_download = Column(Boolean, default=False)
    download_path = Column(String)

    # Status
    last_checked = Column(DateTime)
    last_video_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DownloadQueue(Base):
    """Download queue model for tracking pending downloads"""
    __tablename__ = 'download_queue'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False)

    # Status
    status = Column(String, default='pending', index=True)  # pending, downloading, completed, failed, cancelled
    priority = Column(Integer, default=5, index=True)  # 1-10, higher is more important

    # Progress
    progress = Column(Float, default=0.0)  # 0-100
    speed = Column(Float)  # bytes/sec
    eta = Column(Integer)  # seconds
    downloaded_bytes = Column(Integer)
    total_bytes = Column(Integer)

    # Error info
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Settings
    output_path = Column(String)
    format_id = Column(String)
    quality = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Metadata reference
    video_metadata = Column(Text)  # JSON string

    def set_metadata(self, meta_dict: dict):
        """Set metadata from dictionary"""
        self.video_metadata = json.dumps(meta_dict, ensure_ascii=False)

    def get_metadata(self) -> dict:
        """Get metadata as dictionary"""
        if self.video_metadata:
            return json.loads(self.video_metadata)
        return {}


class Settings(Base):
    """Application settings model"""
    __tablename__ = 'settings'

    key = Column(String, primary_key=True)
    value = Column(Text)  # JSON string
    value_type = Column(String)  # string, int, bool, json
    description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def set_value(self, val):
        """Set value with automatic type detection"""
        if isinstance(val, (dict, list)):
            self.value = json.dumps(val, ensure_ascii=False)
            self.value_type = 'json'
        elif isinstance(val, bool):
            self.value = str(val)
            self.value_type = 'bool'
        elif isinstance(val, int):
            self.value = str(val)
            self.value_type = 'int'
        else:
            self.value = str(val)
            self.value_type = 'string'

    def get_value(self):
        """Get value with automatic type conversion"""
        if self.value_type == 'json':
            return json.loads(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() == 'true'
        elif self.value_type == 'int':
            return int(self.value)
        else:
            return self.value
