"""Test Chrome authentication extraction and encryption"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_manager import ServiceConfig
from modules.auth_manager import AuthManager
from utils.logger import logger

async def test_chrome_auth():
    """Test Chrome authentication extraction"""
    print("=" * 80)
    print("Chrome Authentication Extraction Test")
    print("=" * 80)

    # Initialize auth manager
    config = ServiceConfig()
    auth_manager = AuthManager(config)

    print("\n[1] Checking Chrome profiles...")
    profiles = auth_manager.chrome_extractor.get_all_profiles()
    if profiles:
        print(f"✓ Found {len(profiles)} Chrome profile(s): {profiles}")
    else:
        print("✗ No Chrome profiles found")
        print("Make sure Chrome is installed")
        return False

    # Extract authentication
    print("\n[2] Extracting authentication from Chrome...")
    success = auth_manager.extract_and_save_chrome_auth('Default')

    if success:
        print("✓ Successfully extracted and encrypted Chrome authentication")

        # Verify loading
        print("\n[3] Verifying encrypted storage...")
        if auth_manager.encrypted_creds_file.exists():
            print(f"✓ Encrypted file exists: {auth_manager.encrypted_creds_file}")

            # Check file permissions
            import platform
            import os
            if platform.system() != 'Windows':
                file_mode = oct(os.stat(auth_manager.encrypted_creds_file).st_mode)[-3:]
                print(f"✓ File permissions: {file_mode} (should be 600)")

            # Try to load
            loaded = auth_manager._load_encrypted_chrome_auth()
            if loaded:
                print("✓ Successfully loaded and decrypted credentials")

                # Show what was extracted
                cookies = auth_manager.get_decrypted_chrome_cookies()
                if cookies:
                    print(f"✓ Cookies available: {len(cookies)}")
                    print(f"  Cookie names: {list(cookies.keys())}")

                if auth_manager.cookies.get('tokens'):
                    tokens = auth_manager.cookies['tokens']
                    print(f"✓ OAuth tokens available: {len(tokens)}")
                    print(f"  Token types: {list(tokens.keys())}")
            else:
                print("✗ Failed to load encrypted credentials")
                return False
        else:
            print("✗ Encrypted file was not created")
            return False

        print("\n" + "=" * 80)
        print("✅ All tests PASSED!")
        print("=" * 80)
        print("\nSecurity Notes:")
        print("• Credentials are encrypted using machine-specific key")
        print("• Encrypted file cannot be transferred to another computer")
        print("• File has restrictive permissions (read/write for owner only)")
        print("• Encryption uses Fernet (AES-128) with PBKDF2 key derivation")
        return True

    else:
        print("✗ Failed to extract Chrome authentication")
        print("\nPossible reasons:")
        print("• Chrome is not installed")
        print("• Not logged into YouTube in Chrome")
        print("• Chrome is currently running (close it and try again)")
        print("• Insufficient permissions to access Chrome data")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_chrome_auth())
    sys.exit(0 if success else 1)
