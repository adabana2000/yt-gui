"""Application settings and configuration"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "YouTube Downloader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/youtube_downloader.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_CORS_ORIGINS: list = ["*"]

    # Download Settings
    MAX_CONCURRENT_DOWNLOADS: int = 5
    MAX_WORKERS: int = 10
    RETRY_COUNT: int = 3
    TIMEOUT: int = 300
    FRAGMENT_DOWNLOADS: int = 5

    # Schedule Settings
    ENABLE_SCHEDULER: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 10

    # GPU Encoding
    ENABLE_GPU: bool = True
    GPU_ENCODER: Optional[str] = None  # auto, nvenc, qsv, amf

    # Proxy
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    SOCKS_PROXY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
