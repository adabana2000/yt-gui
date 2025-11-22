"""Chrome authentication extractor for YouTube"""
from typing import Optional, Dict, Any
import json
import sqlite3
import shutil
from pathlib import Path
import platform
import tempfile
from datetime import datetime

from utils.logger import logger


class ChromeAuthExtractor:
    """Extract authentication data from Chrome browser"""

    def __init__(self):
        """Initialize Chrome auth extractor"""
        self.chrome_data_path = self._get_chrome_path()

    def _get_chrome_path(self) -> Optional[Path]:
        """Get Chrome user data directory path

        Returns:
            Path to Chrome user data directory
        """
        system = platform.system()

        if system == 'Windows':
            base_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'User Data'
        elif system == 'Darwin':  # macOS
            base_path = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
        elif system == 'Linux':
            base_path = Path.home() / '.config' / 'google-chrome'
        else:
            logger.error(f"Unsupported platform: {system}")
            return None

        if not base_path.exists():
            logger.warning(f"Chrome data directory not found: {base_path}")
            return None

        return base_path

    def _get_profile_path(self, profile: str = 'Default') -> Optional[Path]:
        """Get Chrome profile path

        Args:
            profile: Profile name (Default, Profile 1, etc.)

        Returns:
            Path to profile directory
        """
        if not self.chrome_data_path:
            return None

        profile_path = self.chrome_data_path / profile
        if not profile_path.exists():
            logger.warning(f"Chrome profile not found: {profile}")
            return None

        return profile_path

    def extract_youtube_cookies(self, profile: str = 'Default') -> Optional[Dict[str, str]]:
        """Extract YouTube cookies from Chrome

        Args:
            profile: Chrome profile name

        Returns:
            Dictionary of cookies or None
        """
        profile_path = self._get_profile_path(profile)
        if not profile_path:
            return None

        cookies_db = profile_path / 'Cookies'
        if not cookies_db.exists():
            # Try 'Network/Cookies' for newer Chrome versions
            cookies_db = profile_path / 'Network' / 'Cookies'
            if not cookies_db.exists():
                logger.error(f"Cookies database not found in {profile_path}")
                return None

        try:
            # Create temporary copy (Chrome locks the file)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                tmp_db = tmp_file.name

            shutil.copy2(cookies_db, tmp_db)

            # Connect to database
            conn = sqlite3.connect(tmp_db)
            cursor = conn.cursor()

            # Query YouTube cookies
            cursor.execute("""
                SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
                FROM cookies
                WHERE host_key LIKE '%youtube.com%' OR host_key LIKE '%google.com%'
                ORDER BY creation_utc DESC
            """)

            cookies = {}
            important_cookies = {'SID', 'HSID', 'SSID', 'APISID', 'SAPISID', 'LOGIN_INFO', '__Secure-1PSID', '__Secure-3PSID'}

            for row in cursor.fetchall():
                name, value, host_key, path, expires_utc, is_secure, is_httponly = row

                # Store important cookies
                if name in important_cookies:
                    cookies[name] = {
                        'value': value,
                        'domain': host_key,
                        'path': path,
                        'expires': expires_utc,
                        'secure': bool(is_secure),
                        'httponly': bool(is_httponly)
                    }
                    logger.debug(f"Found important cookie: {name}")

            conn.close()

            # Clean up temp file
            Path(tmp_db).unlink()

            if cookies:
                logger.info(f"✅ Extracted {len(cookies)} important cookies from Chrome")
                return cookies
            else:
                logger.warning("⚠️  No important YouTube cookies found in Chrome")
                logger.warning("💡 Make sure you are logged into YouTube in Chrome")
                return None

        except Exception as e:
            logger.error(f"Failed to extract cookies from Chrome: {e}")
            import traceback
            traceback.print_exc()
            return None

    def extract_oauth_tokens(self, profile: str = 'Default') -> Optional[Dict[str, str]]:
        """Extract OAuth tokens from Chrome's Local Storage

        Args:
            profile: Chrome profile name

        Returns:
            Dictionary of OAuth tokens or None
        """
        profile_path = self._get_profile_path(profile)
        if not profile_path:
            return None

        # Check for Local Storage
        local_storage_path = profile_path / 'Local Storage' / 'leveldb'
        if not local_storage_path.exists():
            logger.warning("Local Storage not found in Chrome profile")
            return None

        tokens = {}

        try:
            # Read leveldb files for YouTube tokens
            for file_path in local_storage_path.glob('*.log'):
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()

                        # Search for token patterns
                        data_str = data.decode('utf-8', errors='ignore')

                        # Look for access_token
                        if 'access_token' in data_str:
                            # Extract token (this is simplified, real implementation would parse properly)
                            import re
                            token_match = re.search(r'"access_token":"([^"]+)"', data_str)
                            if token_match:
                                tokens['access_token'] = token_match.group(1)
                                logger.info("Found OAuth access_token")

                        # Look for refresh_token
                        if 'refresh_token' in data_str:
                            token_match = re.search(r'"refresh_token":"([^"]+)"', data_str)
                            if token_match:
                                tokens['refresh_token'] = token_match.group(1)
                                logger.info("Found OAuth refresh_token")

                except Exception as e:
                    logger.debug(f"Could not read {file_path}: {e}")
                    continue

            if tokens:
                logger.info(f"✅ Extracted {len(tokens)} OAuth tokens from Chrome")
                return tokens
            else:
                logger.debug("No OAuth tokens found in Local Storage")
                return None

        except Exception as e:
            logger.error(f"Failed to extract OAuth tokens: {e}")
            return None

    def get_all_profiles(self) -> list:
        """Get list of all Chrome profiles

        Returns:
            List of profile names
        """
        if not self.chrome_data_path:
            return []

        profiles = ['Default']

        # Check for additional profiles (Profile 1, Profile 2, etc.)
        for i in range(1, 10):
            profile_name = f'Profile {i}'
            if (self.chrome_data_path / profile_name).exists():
                profiles.append(profile_name)

        logger.info(f"Found Chrome profiles: {profiles}")
        return profiles

    def extract_complete_auth(self, profile: str = 'Default') -> Optional[Dict[str, Any]]:
        """Extract complete authentication data (cookies + tokens)

        Args:
            profile: Chrome profile name

        Returns:
            Dictionary with cookies and tokens
        """
        result = {
            'cookies': None,
            'tokens': None,
            'profile': profile,
            'extracted_at': datetime.now().isoformat()
        }

        # Extract cookies
        cookies = self.extract_youtube_cookies(profile)
        if cookies:
            result['cookies'] = cookies

        # Extract OAuth tokens (best effort)
        tokens = self.extract_oauth_tokens(profile)
        if tokens:
            result['tokens'] = tokens

        if result['cookies'] or result['tokens']:
            logger.info("✅ Successfully extracted Chrome authentication data")
            return result
        else:
            logger.error("❌ Failed to extract any authentication data from Chrome")
            return None


# Fix import
import os
