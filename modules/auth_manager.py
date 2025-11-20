"""Authentication manager for Google OAuth and cookie management"""
from typing import Optional, Dict, Any
import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from core.service_manager import BaseService, ServiceConfig
from config.settings import settings
from utils.logger import logger


class AuthManager(BaseService):
    """Authentication manager"""

    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

    def __init__(self, config: ServiceConfig):
        """Initialize auth manager

        Args:
            config: Service configuration
        """
        super().__init__(config, "AuthManager")
        self.credentials: Optional[Credentials] = None
        self.token_file = settings.DATA_DIR / 'token.pickle'
        self.cookies: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start auth manager"""
        logger.info("Starting Auth Manager...")
        # Auto-load credentials if available
        if self.token_file.exists():
            self._load_credentials()

    async def stop(self) -> None:
        """Stop auth manager"""
        logger.info("Stopping Auth Manager...")

    def _load_credentials(self) -> bool:
        """Load credentials from file

        Returns:
            True if successful
        """
        try:
            with open(self.token_file, 'rb') as token:
                self.credentials = pickle.load(token)
            logger.info("Loaded saved credentials")
            return True
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False

    def _save_credentials(self) -> bool:
        """Save credentials to file

        Returns:
            True if successful
        """
        try:
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.info("Saved credentials")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    async def authenticate_google(self, client_secrets_file: str) -> bool:
        """Authenticate with Google OAuth

        Args:
            client_secrets_file: Path to client secrets JSON file

        Returns:
            True if successful
        """
        creds = None

        # Load existing credentials
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Google credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                # New authentication flow
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file,
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Completed Google authentication")
                except Exception as e:
                    logger.error(f"Failed to authenticate: {e}")
                    return False

            # Save credentials
            self._save_credentials()

        self.credentials = creds
        return True

    def get_cookies_for_ytdlp(self) -> Optional[str]:
        """Get cookies for yt-dlp from browser

        Returns:
            Cookie file path or None
        """
        try:
            import browser_cookie3

            cookie_file = settings.DATA_DIR / 'youtube_cookies.txt'

            # Try to get cookies from Chrome
            try:
                cookies = browser_cookie3.chrome(domain_name='youtube.com')
                self._save_cookies_netscape(cookies, cookie_file)
                logger.info("Loaded cookies from Chrome")
                return str(cookie_file)
            except:
                pass

            # Try Firefox
            try:
                cookies = browser_cookie3.firefox(domain_name='youtube.com')
                self._save_cookies_netscape(cookies, cookie_file)
                logger.info("Loaded cookies from Firefox")
                return str(cookie_file)
            except:
                pass

            # Try Edge
            try:
                cookies = browser_cookie3.edge(domain_name='youtube.com')
                self._save_cookies_netscape(cookies, cookie_file)
                logger.info("Loaded cookies from Edge")
                return str(cookie_file)
            except:
                pass

            logger.warning("Could not load cookies from any browser")
            return None

        except ImportError:
            logger.error("browser_cookie3 not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to get cookies: {e}")
            return None

    def _save_cookies_netscape(self, cookies, filename: Path) -> None:
        """Save cookies in Netscape format for yt-dlp

        Args:
            cookies: Cookie jar
            filename: Output file path
        """
        with open(filename, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                if 'youtube.com' in cookie.domain:
                    f.write(f"{cookie.domain}\t"
                           f"{'TRUE' if cookie.domain.startswith('.') else 'FALSE'}\t"
                           f"{cookie.path}\t"
                           f"{'TRUE' if cookie.secure else 'FALSE'}\t"
                           f"{cookie.expires if cookie.expires else 0}\t"
                           f"{cookie.name}\t"
                           f"{cookie.value}\n")

    def is_authenticated(self) -> bool:
        """Check if authenticated

        Returns:
            True if authenticated
        """
        return self.credentials is not None and self.credentials.valid

    def logout(self) -> None:
        """Logout and clear credentials"""
        self.credentials = None
        if self.token_file.exists():
            self.token_file.unlink()
        logger.info("Logged out")
