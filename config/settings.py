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

    # Directory Organization
    ORGANIZE_BY_CHANNEL: bool = True  # チャンネル別にディレクトリ作成
    DIRECTORY_STRUCTURE: str = "channel"  # "channel", "date", "channel_date", "flat", "custom"
    FILENAME_TEMPLATE: str = "{title}"  # テンプレート変数: {title}, {channel}, {id}, {date}

    # Custom Output Template (yt-dlp format)
    # 利用可能な変数: https://github.com/yt-dlp/yt-dlp#output-template
    # 例: "%(uploader)s/%(upload_date>%Y-%m)s/%(title)s.%(ext)s"
    #     "%(uploader)s/[%(id)s] %(title)s.%(ext)s"
    #     "%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s [%(id)s].%(ext)s"
    CUSTOM_OUTPUT_TEMPLATE: str = "%(uploader)s/%(title)s.%(ext)s"

    # Output Template Presets
    OUTPUT_TEMPLATE_PRESETS: dict = {
        "channel": "%(uploader)s/%(title)s.%(ext)s",
        "date": "%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s.%(ext)s",
        "channel_date": "%(uploader)s/%(upload_date>%Y-%m)s/%(title)s.%(ext)s",
        "channel_type": "%(uploader)s/%(playlist_title|)s/%(title)s.%(ext)s",
        "flat": "%(title)s.%(ext)s",
        "detailed": "%(uploader)s/[%(id)s] %(title)s - %(upload_date>%Y%m%d)s.%(ext)s",
        "quality": "%(uploader)s/%(resolution)s/%(title)s.%(ext)s",
    }

    # Format/Quality Settings
    VIDEO_QUALITY: str = "best"  # "best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "worst", "audio_only"
    VIDEO_FORMAT: str = "mp4"  # "mp4", "webm", "mkv", "any"
    AUDIO_QUALITY: str = "best"  # "best", "320k", "256k", "192k", "128k", "worst"
    AUDIO_FORMAT: str = "m4a"  # "m4a", "mp3", "opus", "wav", "best"
    DOWNLOAD_VIDEO: bool = True
    DOWNLOAD_AUDIO: bool = True
    PREFER_FREE_FORMATS: bool = False  # Prefer free formats (webm, opus) over proprietary (mp4, m4a)

    # Format Selection Presets
    FORMAT_PRESETS: dict = {
        "best": "bestvideo*+bestaudio/best",
        "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "worst": "worstvideo+worstaudio/worst",
        "audio_only": "bestaudio/best",
    }

    # Subtitle Settings
    DOWNLOAD_SUBTITLES: bool = False
    DOWNLOAD_AUTO_SUBTITLES: bool = False  # 自動生成字幕もダウンロード
    SUBTITLE_LANGUAGES: list = ["ja", "en"]  # 優先順位順
    SUBTITLE_FORMAT: str = "srt"  # "srt", "vtt", "ass", "best"
    EMBED_SUBTITLES: bool = False  # 字幕を動画ファイルに埋め込む
    CONVERT_SUBTITLES: str = "srt"  # 字幕を指定形式に変換

    # Future: Transcription & Translation
    ENABLE_TRANSCRIPTION: bool = False  # 文字起こし機能（将来実装）
    TRANSCRIPTION_SERVICE: str = "whisper"  # "whisper", "google", "azure"
    ENABLE_TRANSLATION: bool = False  # 字幕翻訳機能（将来実装）
    TRANSLATION_TARGET: str = "ja"  # 翻訳先言語

    # Playlist/Channel Download Settings
    PLAYLIST_DOWNLOAD: bool = False  # プレイリスト全体をダウンロード
    PLAYLIST_START: int = 1  # 開始番号
    PLAYLIST_END: Optional[int] = None  # 終了番号（Noneで最後まで）
    PLAYLIST_ITEMS: Optional[str] = None  # "1-5,7,10-15" などの指定
    DOWNLOAD_ARCHIVE: bool = True  # ダウンロード済みを記録
    ARCHIVE_FILE: Path = DATA_DIR / "download_archive.txt"
    MAX_DOWNLOADS: Optional[int] = None  # 最大ダウンロード数
    DATE_BEFORE: Optional[str] = None  # この日付より前の動画のみ (YYYYMMDD)
    DATE_AFTER: Optional[str] = None  # この日付より後の動画のみ (YYYYMMDD)
    MIN_VIEWS: Optional[int] = None  # 最小再生回数
    MAX_VIEWS: Optional[int] = None  # 最大再生回数
    MIN_DURATION: Optional[int] = None  # 最小動画長（秒）
    MAX_DURATION: Optional[int] = None  # 最大動画長（秒）

    # Duplicate Check Settings
    SKIP_DUPLICATES: bool = True  # 重複をスキップ
    CHECK_BY_VIDEO_ID: bool = True  # 動画IDでチェック
    CHECK_BY_FILENAME: bool = True  # ファイル名でチェック
    CHECK_BY_FILE_HASH: bool = False  # ファイルハッシュでチェック（重い）
    DUPLICATE_ACTION: str = "skip"  # "skip", "rename", "overwrite"

    # Thumbnail Settings
    DOWNLOAD_THUMBNAIL: bool = True  # サムネイルをダウンロード
    EMBED_THUMBNAIL: bool = False  # サムネイルを動画に埋め込む
    THUMBNAIL_FORMAT: str = "jpg"  # "jpg", "png", "webp"
    WRITE_ALL_THUMBNAILS: bool = False  # すべてのサムネイルをダウンロード

    # Metadata Settings
    WRITE_METADATA: bool = True  # メタデータをファイルに書き込む
    WRITE_INFO_JSON: bool = False  # info.jsonを保存
    WRITE_DESCRIPTION: bool = False  # 説明文を.descriptionファイルに保存
    WRITE_ANNOTATIONS: bool = False  # アノテーションを保存

    # Notification Settings
    ENABLE_NOTIFICATIONS: bool = True
    DESKTOP_NOTIFICATION: bool = True  # デスクトップ通知（Windows/macOS/Linux）
    NOTIFICATION_SOUND: bool = True  # サウンド通知
    EMAIL_NOTIFICATION: bool = False
    EMAIL_SMTP_SERVER: Optional[str] = None  # "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USE_TLS: bool = True
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None  # 暗号化して保存すべき
    EMAIL_FROM: Optional[str] = None
    EMAIL_TO: Optional[str] = None
    NOTIFY_ON_START: bool = False  # ダウンロード開始時に通知
    NOTIFY_ON_COMPLETE: bool = True  # ダウンロード完了時に通知
    NOTIFY_ON_ERROR: bool = True  # エラー時に通知

    # Speed Limiting
    LIMIT_DOWNLOAD_SPEED: bool = False
    MAX_DOWNLOAD_SPEED: Optional[int] = None  # KB/s (例: 1024 = 1MB/s)
    THROTTLED_RATE: Optional[int] = None  # 最小速度 KB/s

    # Auto-Update Settings
    AUTO_UPDATE_YTDLP: bool = True  # yt-dlpの自動更新
    CHECK_UPDATE_ON_START: bool = True  # 起動時に更新チェック
    UPDATE_INTERVAL_DAYS: int = 7  # 更新チェック間隔（日）
    LAST_UPDATE_CHECK: Optional[str] = None  # 最終チェック日時

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
    ENABLE_PROXY: bool = False
    PROXY_TYPE: str = "http"  # "http", "https", "socks5"
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    SOCKS_PROXY: Optional[str] = None
    PROXY_USERNAME: Optional[str] = None
    PROXY_PASSWORD: Optional[str] = None

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
