"""Updater manager for yt-dlp auto-update"""
import asyncio
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path

from core.service_manager import BaseService, ServiceConfig
from config.settings import settings
from utils.logger import logger


class UpdaterManager(BaseService):
    """Updater manager service for yt-dlp"""

    def __init__(self, config: ServiceConfig, db_manager=None):
        """Initialize updater manager

        Args:
            config: Service configuration
            db_manager: Database manager instance (optional)
        """
        super().__init__(config, "UpdaterManager")
        self.db_manager = db_manager
        self._update_in_progress = False

    async def start(self) -> None:
        """Start the updater manager"""
        logger.info("Starting updater manager...")
        self.status = self.status.RUNNING

        # Check for updates on start if enabled
        if settings.CHECK_UPDATE_ON_START and settings.AUTO_UPDATE_YTDLP:
            asyncio.create_task(self.check_and_update())

    async def stop(self) -> None:
        """Stop the updater manager"""
        logger.info("Stopping updater manager...")
        self.status = self.status.STOPPED

    async def check_and_update(self, force: bool = False) -> Tuple[bool, str]:
        """Check for updates and update if needed

        Args:
            force: Force update check even if recently checked

        Returns:
            Tuple of (success, message)
        """
        if self._update_in_progress:
            return False, "更新チェック中です"

        try:
            self._update_in_progress = True

            # Check if we should update based on interval
            if not force and not self._should_check_update():
                last_check = self._get_last_update_check()
                return True, f"最終チェック: {last_check}"

            logger.info("Checking for yt-dlp updates...")

            # Check current version
            current_version = await self.get_current_version()
            logger.info(f"Current yt-dlp version: {current_version}")

            # Check if update is available
            update_available, latest_version = await self.check_update_available()

            if not update_available:
                self._save_last_update_check()
                return True, f"最新版です ({current_version})"

            logger.info(f"Update available: {current_version} -> {latest_version}")

            # Perform update
            success = await self.update_ytdlp()

            if success:
                self._save_last_update_check()
                new_version = await self.get_current_version()
                return True, f"更新完了: {current_version} -> {new_version}"
            else:
                return False, "更新に失敗しました"

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return False, f"エラー: {str(e)}"
        finally:
            self._update_in_progress = False

    def _should_check_update(self) -> bool:
        """Check if we should check for updates based on interval

        Returns:
            True if should check
        """
        last_check = self._get_last_update_check()
        if not last_check:
            return True

        try:
            last_check_date = datetime.fromisoformat(last_check)
            days_since_check = (datetime.now() - last_check_date).days

            return days_since_check >= settings.UPDATE_INTERVAL_DAYS
        except Exception as e:
            logger.error(f"Failed to parse last update check date: {e}")
            return True

    def _get_last_update_check(self) -> Optional[str]:
        """Get last update check datetime

        Returns:
            ISO format datetime string or None
        """
        if self.db_manager:
            return self.db_manager.get_setting('last_update_check')
        return settings.LAST_UPDATE_CHECK

    def _save_last_update_check(self):
        """Save last update check datetime"""
        now = datetime.now().isoformat()

        if self.db_manager:
            self.db_manager.set_setting('last_update_check', now)

        settings.LAST_UPDATE_CHECK = now

    async def get_current_version(self) -> str:
        """Get current yt-dlp version

        Returns:
            Version string
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "yt_dlp", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get yt-dlp version: {e}")
            return "unknown"

    async def check_update_available(self) -> Tuple[bool, Optional[str]]:
        """Check if yt-dlp update is available

        Returns:
            Tuple of (update_available, latest_version)
        """
        try:
            # Use yt-dlp's built-in update check
            result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "pip", "index", "versions", "yt-dlp"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                # Parse latest version from pip output
                output = result.stdout
                # Simple parsing - get first version listed (usually latest)
                for line in output.split('\n'):
                    if 'Available versions:' in line:
                        # Extract first version number
                        versions = line.split(':')[1].strip().split(',')
                        if versions:
                            latest = versions[0].strip()
                            current = await self.get_current_version()
                            return latest != current, latest

            return False, None

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return False, None

    async def update_ytdlp(self) -> bool:
        """Update yt-dlp to latest version

        Returns:
            True if successful
        """
        try:
            logger.info("Updating yt-dlp...")

            # Update using pip
            result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                logger.info("yt-dlp updated successfully")
                logger.debug(result.stdout)
                return True
            else:
                logger.error(f"Failed to update yt-dlp: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False

    async def update_ffmpeg(self) -> Tuple[bool, str]:
        """Check and update FFmpeg (if possible)

        Returns:
            Tuple of (success, message)

        Note:
            FFmpeg updates are platform-specific and may require manual intervention
        """
        try:
            # Check FFmpeg version
            result = await asyncio.to_thread(
                subprocess.run,
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, f"FFmpeg is installed: {version_line}"
            else:
                return False, "FFmpeg not found"

        except FileNotFoundError:
            return False, "FFmpeg not installed"
        except Exception as e:
            logger.error(f"FFmpeg check failed: {e}")
            return False, str(e)

    async def get_system_info(self) -> dict:
        """Get system information for diagnostics

        Returns:
            Dictionary with system info
        """
        info = {}

        try:
            # yt-dlp version
            info['yt-dlp'] = await self.get_current_version()

            # Python version
            info['python'] = sys.version.split()[0]

            # FFmpeg version
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["ffmpeg", "-version"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    ffmpeg_version = result.stdout.split('\n')[0].split('version')[1].split()[0]
                    info['ffmpeg'] = ffmpeg_version
                else:
                    info['ffmpeg'] = "Not found"
            except:
                info['ffmpeg'] = "Not found"

            # Platform
            import platform
            info['platform'] = f"{platform.system()} {platform.release()}"
            info['architecture'] = platform.machine()

        except Exception as e:
            logger.error(f"Failed to get system info: {e}")

        return info

    async def reinstall_ytdlp(self) -> Tuple[bool, str]:
        """Reinstall yt-dlp (useful if corrupted)

        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Reinstalling yt-dlp...")

            # Uninstall
            result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "pip", "uninstall", "-y", "yt-dlp"],
                capture_output=True,
                text=True,
                check=False
            )

            # Install
            result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "pip", "install", "yt-dlp"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                version = await self.get_current_version()
                return True, f"再インストール完了: {version}"
            else:
                return False, "再インストールに失敗しました"

        except Exception as e:
            logger.error(f"Reinstall failed: {e}")
            return False, str(e)
