"""Notification manager for desktop and email notifications"""
import asyncio
import smtplib
import platform
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from core.service_manager import BaseService, ServiceConfig
from config.settings import settings
from utils.logger import logger


class NotificationManager(BaseService):
    """Notification manager service"""

    def __init__(self, config: ServiceConfig):
        """Initialize notification manager

        Args:
            config: Service configuration
        """
        super().__init__(config, "NotificationManager")
        self._desktop_notifier = None
        self._initialize_desktop_notifier()

    def _initialize_desktop_notifier(self):
        """Initialize desktop notification system"""
        if not settings.ENABLE_NOTIFICATIONS or not settings.DESKTOP_NOTIFICATION:
            return

        try:
            # Try to import platform-specific notification libraries
            system = platform.system()

            if system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    self._desktop_notifier = ToastNotifier()
                    logger.info("Initialized Windows 10 toast notifications")
                except ImportError:
                    logger.warning("win10toast not installed. Install with: pip install win10toast")
                    # Fallback to plyer
                    self._try_plyer_notifier()
            elif system == "Darwin":  # macOS
                self._try_plyer_notifier()
            elif system == "Linux":
                self._try_plyer_notifier()
            else:
                logger.warning(f"Unsupported platform for notifications: {system}")

        except Exception as e:
            logger.error(f"Failed to initialize desktop notifier: {e}")

    def _try_plyer_notifier(self):
        """Try to use plyer for cross-platform notifications"""
        try:
            from plyer import notification
            self._desktop_notifier = notification
            logger.info("Initialized cross-platform notifications (plyer)")
        except ImportError:
            logger.warning("plyer not installed. Install with: pip install plyer")

    async def start(self) -> None:
        """Start the notification manager"""
        logger.info("Starting notification manager...")
        self.status = self.status.RUNNING

    async def stop(self) -> None:
        """Stop the notification manager"""
        logger.info("Stopping notification manager...")
        self.status = self.status.STOPPED

    def notify_download_start(self, task_info: Dict[str, Any]):
        """Notify when download starts

        Args:
            task_info: Download task information
        """
        if not settings.NOTIFY_ON_START:
            return

        title = "ダウンロード開始"
        message = f"📥 {task_info.get('title', 'Unknown')}\nチャンネル: {task_info.get('uploader', 'Unknown')}"

        self._send_notification(title, message)

    def notify_download_complete(self, task_info: Dict[str, Any]):
        """Notify when download completes

        Args:
            task_info: Download task information
        """
        if not settings.NOTIFY_ON_COMPLETE:
            return

        title = "ダウンロード完了"
        message = f"✅ {task_info.get('title', 'Unknown')}\n保存先: {task_info.get('output_path', 'Unknown')}"

        self._send_notification(title, message)

        # Send email if enabled
        if settings.EMAIL_NOTIFICATION:
            asyncio.create_task(self._send_email_notification(title, message, task_info))

    def notify_download_error(self, task_info: Dict[str, Any], error: str):
        """Notify when download fails

        Args:
            task_info: Download task information
            error: Error message
        """
        if not settings.NOTIFY_ON_ERROR:
            return

        title = "ダウンロードエラー"
        message = f"❌ {task_info.get('title', 'Unknown')}\nエラー: {error}"

        self._send_notification(title, message)

        # Send email if enabled
        if settings.EMAIL_NOTIFICATION:
            asyncio.create_task(self._send_email_notification(title, message, task_info))

    def notify_batch_complete(self, total: int, succeeded: int, failed: int):
        """Notify when batch download completes

        Args:
            total: Total downloads
            succeeded: Successful downloads
            failed: Failed downloads
        """
        if not settings.NOTIFY_ON_COMPLETE:
            return

        title = "一括ダウンロード完了"
        message = f"✅ 完了: {succeeded}/{total}\n❌ 失敗: {failed}/{total}"

        self._send_notification(title, message)

    def _send_notification(self, title: str, message: str, icon: Optional[str] = None):
        """Send desktop notification

        Args:
            title: Notification title
            message: Notification message
            icon: Icon path (optional)
        """
        if not settings.ENABLE_NOTIFICATIONS or not settings.DESKTOP_NOTIFICATION:
            return

        try:
            system = platform.system()

            if system == "Windows" and self._desktop_notifier:
                # Windows 10 Toast Notification
                if hasattr(self._desktop_notifier, 'show_toast'):
                    self._desktop_notifier.show_toast(
                        title,
                        message,
                        duration=5,
                        threaded=True
                    )
                else:
                    # Plyer fallback
                    self._desktop_notifier.notify(
                        title=title,
                        message=message,
                        app_name=settings.APP_NAME,
                        timeout=5
                    )
            elif self._desktop_notifier:
                # Cross-platform with plyer
                self._desktop_notifier.notify(
                    title=title,
                    message=message,
                    app_name=settings.APP_NAME,
                    timeout=5
                )
            else:
                logger.warning("Desktop notifier not available")

            # Play sound if enabled
            if settings.NOTIFICATION_SOUND:
                self._play_notification_sound()

        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")

    def _play_notification_sound(self):
        """Play notification sound"""
        try:
            system = platform.system()

            if system == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif system == "Darwin":  # macOS
                import subprocess
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
            elif system == "Linux":
                import subprocess
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], check=False)
        except Exception as e:
            logger.debug(f"Could not play notification sound: {e}")

    async def _send_email_notification(self, title: str, message: str, task_info: Dict[str, Any]):
        """Send email notification

        Args:
            title: Email subject
            message: Email message
            task_info: Task information for detailed email
        """
        if not settings.EMAIL_NOTIFICATION:
            return

        if not all([settings.EMAIL_SMTP_SERVER, settings.EMAIL_FROM, settings.EMAIL_TO]):
            logger.warning("Email notification enabled but configuration incomplete")
            return

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{settings.APP_NAME} - {title}"
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = settings.EMAIL_TO
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

            # Create detailed HTML email
            html_body = self._create_email_html(title, message, task_info)
            text_body = message  # Plain text fallback

            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            await asyncio.to_thread(self._send_smtp_email, msg)

            logger.info(f"Email notification sent to {settings.EMAIL_TO}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def _send_smtp_email(self, msg: MIMEMultipart):
        """Send email via SMTP (blocking, use in thread)

        Args:
            msg: Email message
        """
        with smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()

            if settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)

            server.send_message(msg)

    def _create_email_html(self, title: str, message: str, task_info: Dict[str, Any]) -> str:
        """Create HTML email body

        Args:
            title: Email title
            message: Email message
            task_info: Task information

        Returns:
            HTML email body
        """
        status_icon = "✅" if "完了" in title else "❌" if "エラー" in title else "📥"
        status_color = "#4CAF50" if "完了" in title else "#F44336" if "エラー" in title else "#2196F3"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 20px; }}
        .info-row {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 4px; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ color: #333; }}
        .footer {{ padding: 20px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{status_icon} {title}</h1>
        </div>
        <div class="content">
            <div class="info-row">
                <div class="label">動画タイトル</div>
                <div class="value">{task_info.get('title', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="label">チャンネル</div>
                <div class="value">{task_info.get('uploader', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="label">動画ID</div>
                <div class="value">{task_info.get('id', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="label">保存先</div>
                <div class="value">{task_info.get('output_path', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="label">完了時刻</div>
                <div class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
        </div>
        <div class="footer">
            {settings.APP_NAME} v{settings.APP_VERSION}
        </div>
    </div>
</body>
</html>
"""
        return html

    def test_notification(self):
        """Test notification system"""
        logger.info("Testing notification system...")

        test_info = {
            'title': 'テスト動画タイトル',
            'uploader': 'テストチャンネル',
            'id': 'test123',
            'output_path': '/downloads/test.mp4'
        }

        if settings.DESKTOP_NOTIFICATION:
            self._send_notification(
                "通知テスト",
                f"✅ デスクトップ通知が正常に動作しています\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if settings.EMAIL_NOTIFICATION:
            asyncio.create_task(
                self._send_email_notification(
                    "通知テスト",
                    "メール通知が正常に動作しています",
                    test_info
                )
            )
