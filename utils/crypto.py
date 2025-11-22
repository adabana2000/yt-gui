"""Cryptography utilities for secure credential storage"""
from typing import Optional
import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import platform
import uuid

from utils.logger import logger


class CredentialEncryption:
    """Secure encryption for sensitive credentials"""

    def __init__(self, key_file: Path):
        """Initialize encryption with key file

        Args:
            key_file: Path to encryption key file
        """
        self.key_file = key_file
        self._fernet: Optional[Fernet] = None
        self._ensure_key()

    def _get_machine_id(self) -> bytes:
        """Get unique machine identifier for key derivation

        Returns:
            Machine-specific identifier
        """
        try:
            # Try to get machine-specific ID
            if platform.system() == 'Linux':
                # Use machine-id on Linux
                machine_id_file = Path('/etc/machine-id')
                if machine_id_file.exists():
                    return machine_id_file.read_bytes().strip()

                # Fallback to /var/lib/dbus/machine-id
                dbus_id_file = Path('/var/lib/dbus/machine-id')
                if dbus_id_file.exists():
                    return dbus_id_file.read_bytes().strip()

            elif platform.system() == 'Darwin':  # macOS
                # Use IOPlatformUUID
                import subprocess
                result = subprocess.run(
                    ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        uuid_str = line.split('"')[3]
                        return uuid_str.encode()

            elif platform.system() == 'Windows':
                # Use Windows UUID
                import subprocess
                result = subprocess.run(
                    ['wmic', 'csproduct', 'get', 'UUID'],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip().encode()

            # Fallback: use hostname + username
            import socket
            import getpass
            fallback_id = f"{socket.gethostname()}-{getpass.getuser()}"
            logger.warning("Using fallback machine ID (hostname-username)")
            return fallback_id.encode()

        except Exception as e:
            logger.error(f"Failed to get machine ID: {e}")
            # Last resort: generate and save a UUID
            fallback_uuid = str(uuid.uuid4())
            logger.warning(f"Generated fallback UUID: {fallback_uuid}")
            return fallback_uuid.encode()

    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password and salt

        Args:
            password: Password bytes
            salt: Salt bytes

        Returns:
            Derived key
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def _ensure_key(self):
        """Ensure encryption key exists, create if needed"""
        if self.key_file.exists():
            # Load existing key
            try:
                key_data = self.key_file.read_bytes()
                # Key file contains: salt (16 bytes) + encrypted_key
                if len(key_data) < 16:
                    logger.error("Invalid key file format")
                    self._generate_new_key()
                else:
                    salt = key_data[:16]
                    machine_id = self._get_machine_id()
                    derived_key = self._derive_key(machine_id, salt)
                    self._fernet = Fernet(derived_key)
                    logger.info("Loaded existing encryption key")
            except Exception as e:
                logger.error(f"Failed to load key: {e}")
                self._generate_new_key()
        else:
            self._generate_new_key()

    def _generate_new_key(self):
        """Generate new encryption key"""
        try:
            # Generate random salt
            salt = os.urandom(16)

            # Get machine-specific password
            machine_id = self._get_machine_id()

            # Derive key from machine ID
            derived_key = self._derive_key(machine_id, salt)

            # Save salt (we'll need it to derive the key again)
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            self.key_file.write_bytes(salt)

            # Set restrictive permissions
            if platform.system() != 'Windows':
                os.chmod(self.key_file, 0o600)

            self._fernet = Fernet(derived_key)
            logger.info("Generated new encryption key")
            logger.warning("⚠️  Encryption key is machine-specific")
            logger.warning("⚠️  Encrypted data cannot be transferred to another machine")

        except Exception as e:
            logger.error(f"Failed to generate key: {e}")
            raise

    def encrypt(self, data: str) -> str:
        """Encrypt string data

        Args:
            data: Plain text string

        Returns:
            Encrypted string (base64 encoded)
        """
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")

        try:
            encrypted_bytes = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data

        Args:
            encrypted_data: Encrypted string (base64 encoded)

        Returns:
            Decrypted plain text string
        """
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt dictionary values

        Args:
            data: Dictionary with string values

        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt dictionary values

        Args:
            encrypted_data: Dictionary with encrypted values

        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        for key, value in encrypted_data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except:
                    # Not encrypted, use as-is
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted
