"""Authentication manager for Google OAuth and cookie management"""
from typing import Optional, Dict, Any
import os
import pickle
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from core.service_manager import BaseService, ServiceConfig
from config.settings import settings
from utils.logger import logger
from utils.crypto import CredentialEncryption
from utils.chrome_auth import ChromeAuthExtractor


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

        # Initialize encryption for secure credential storage
        encryption_key_file = settings.DATA_DIR / '.encryption_key'
        self.encryption = CredentialEncryption(encryption_key_file)

        # Initialize Chrome auth extractor
        self.chrome_extractor = ChromeAuthExtractor()

        # Encrypted credentials file
        self.encrypted_creds_file = settings.DATA_DIR / 'chrome_auth.encrypted'

    async def start(self) -> None:
        """Start auth manager"""
        logger.info("Starting Auth Manager...")
        # Auto-load credentials if available
        if self.token_file.exists():
            self._load_credentials()

        # Try to load encrypted Chrome credentials
        self._load_encrypted_chrome_auth()

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

    def extract_and_save_chrome_auth(self, profile: str = 'Default') -> bool:
        """Extract authentication from Chrome and save securely

        Args:
            profile: Chrome profile name

        Returns:
            True if successful
        """
        logger.info(f"🔐 Extracting authentication from Chrome profile: {profile}")

        try:
            # Extract complete authentication data
            auth_data = self.chrome_extractor.extract_complete_auth(profile)

            if not auth_data:
                logger.error("❌ Failed to extract Chrome authentication")
                return False

            # Encrypt and save
            encrypted_data = {}

            # Encrypt cookies
            if auth_data.get('cookies'):
                encrypted_data['cookies'] = {}
                for cookie_name, cookie_data in auth_data['cookies'].items():
                    encrypted_value = self.encryption.encrypt(cookie_data['value'])
                    encrypted_data['cookies'][cookie_name] = {
                        'value': encrypted_value,
                        'domain': cookie_data['domain'],
                        'path': cookie_data['path'],
                        'expires': cookie_data['expires'],
                        'secure': cookie_data['secure'],
                        'httponly': cookie_data['httponly']
                    }
                logger.info(f"🔒 Encrypted {len(auth_data['cookies'])} cookies")

            # Encrypt tokens
            if auth_data.get('tokens'):
                encrypted_data['tokens'] = {}
                for token_name, token_value in auth_data['tokens'].items():
                    encrypted_data['tokens'][token_name] = self.encryption.encrypt(token_value)
                logger.info(f"🔒 Encrypted {len(auth_data['tokens'])} OAuth tokens")

            # Save metadata
            encrypted_data['profile'] = profile
            encrypted_data['extracted_at'] = auth_data['extracted_at']
            encrypted_data['_encrypted'] = True  # Marker

            # Write to file
            self.encrypted_creds_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.encrypted_creds_file, 'w') as f:
                json.dump(encrypted_data, f, indent=2)

            # Set restrictive permissions
            import platform
            if platform.system() != 'Windows':
                os.chmod(self.encrypted_creds_file, 0o600)

            logger.info(f"✅ Successfully saved encrypted Chrome authentication")
            logger.info(f"📁 Saved to: {self.encrypted_creds_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to extract and save Chrome auth: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _load_encrypted_chrome_auth(self) -> bool:
        """Load encrypted Chrome authentication

        Returns:
            True if successful
        """
        if not self.encrypted_creds_file.exists():
            logger.debug("No encrypted Chrome credentials found")
            return False

        try:
            with open(self.encrypted_creds_file, 'r') as f:
                encrypted_data = json.load(f)

            if not encrypted_data.get('_encrypted'):
                logger.warning("Credential file is not marked as encrypted")
                return False

            # Decrypt cookies
            if encrypted_data.get('cookies'):
                for cookie_name, cookie_data in encrypted_data['cookies'].items():
                    try:
                        decrypted_value = self.encryption.decrypt(cookie_data['value'])
                        cookie_data['value'] = decrypted_value
                    except Exception as e:
                        logger.error(f"Failed to decrypt cookie {cookie_name}: {e}")

            # Decrypt tokens
            if encrypted_data.get('tokens'):
                for token_name, encrypted_token in encrypted_data['tokens'].items():
                    try:
                        encrypted_data['tokens'][token_name] = self.encryption.decrypt(encrypted_token)
                    except Exception as e:
                        logger.error(f"Failed to decrypt token {token_name}: {e}")

            # Store decrypted data
            self.cookies = encrypted_data

            logger.info(f"✅ Loaded encrypted Chrome authentication")
            logger.info(f"📅 Extracted on: {encrypted_data.get('extracted_at')}")
            return True

        except Exception as e:
            logger.error(f"Failed to load encrypted credentials: {e}")
            return False

    def get_decrypted_chrome_cookies(self) -> Optional[Dict[str, str]]:
        """Get decrypted Chrome cookies for use

        Returns:
            Dictionary of cookie name -> value
        """
        if not self.cookies or not self.cookies.get('cookies'):
            return None

        simple_cookies = {}
        for cookie_name, cookie_data in self.cookies['cookies'].items():
            simple_cookies[cookie_name] = cookie_data['value']

        return simple_cookies

    def refresh_chrome_auth(self, profile: str = 'Default') -> bool:
        """Refresh Chrome authentication data

        Args:
            profile: Chrome profile name

        Returns:
            True if successful
        """
        logger.info("🔄 Refreshing Chrome authentication...")
        return self.extract_and_save_chrome_auth(profile)
