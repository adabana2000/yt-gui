"""Logging configuration and utilities"""
import logging
import logging.handlers
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config.settings import settings


def setup_logging(name: str = "youtube_downloader") -> logging.Logger:
    """Setup logging configuration

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console formatter (human readable)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    log_file = settings.LOG_DIR / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # Error log file
    error_log_file = settings.LOG_DIR / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    return logger


# Create default logger
logger = setup_logging()
