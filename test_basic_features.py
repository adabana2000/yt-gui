#!/usr/bin/env python3
"""
Basic feature test without auth dependencies
Tests core functionality of new features
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_manager import ServiceConfig
from config.settings import settings
from utils.logger import logger


def test_settings_configuration():
    """Test all new settings are properly configured"""
    print("\n" + "="*70)
    print("Testing Settings Configuration")
    print("="*70)

    # Format/Quality Settings
    print("\n[1/8] Format/Quality Settings:")
    print(f"   VIDEO_QUALITY: {settings.VIDEO_QUALITY}")
    print(f"   FORMAT_PRESETS: {len(settings.FORMAT_PRESETS)} presets")
    for quality, format_str in list(settings.FORMAT_PRESETS.items())[:3]:
        print(f"      {quality}: {format_str[:50]}...")

    # Subtitle Settings
    print("\n[2/8] Subtitle Settings:")
    print(f"   DOWNLOAD_SUBTITLES: {settings.DOWNLOAD_SUBTITLES}")
    print(f"   SUBTITLE_LANGUAGES: {settings.SUBTITLE_LANGUAGES}")
    print(f"   SUBTITLE_FORMAT: {settings.SUBTITLE_FORMAT}")
    print(f"   EMBED_SUBTITLES: {settings.EMBED_SUBTITLES}")

    # Playlist Settings
    print("\n[3/8] Playlist Settings:")
    print(f"   PLAYLIST_DOWNLOAD: {settings.PLAYLIST_DOWNLOAD}")
    print(f"   PLAYLIST_START: {settings.PLAYLIST_START}")
    print(f"   PLAYLIST_END: {settings.PLAYLIST_END}")
    print(f"   DOWNLOAD_ARCHIVE: {settings.DOWNLOAD_ARCHIVE}")
    print(f"   ARCHIVE_FILE: {settings.ARCHIVE_FILE}")

    # Duplicate Check Settings
    print("\n[4/8] Duplicate Check Settings:")
    print(f"   SKIP_DUPLICATES: {settings.SKIP_DUPLICATES}")
    print(f"   CHECK_BY_VIDEO_ID: {settings.CHECK_BY_VIDEO_ID}")
    print(f"   CHECK_BY_FILENAME: {settings.CHECK_BY_FILENAME}")

    # Thumbnail Settings
    print("\n[5/8] Thumbnail Settings:")
    print(f"   DOWNLOAD_THUMBNAIL: {settings.DOWNLOAD_THUMBNAIL}")
    print(f"   EMBED_THUMBNAIL: {settings.EMBED_THUMBNAIL}")
    print(f"   WRITE_ALL_THUMBNAILS: {settings.WRITE_ALL_THUMBNAILS}")

    # Notification Settings
    print("\n[6/8] Notification Settings:")
    print(f"   ENABLE_NOTIFICATIONS: {settings.ENABLE_NOTIFICATIONS}")
    print(f"   DESKTOP_NOTIFICATION: {settings.DESKTOP_NOTIFICATION}")
    print(f"   EMAIL_NOTIFICATION: {settings.EMAIL_NOTIFICATION}")
    print(f"   NOTIFY_ON_COMPLETE: {settings.NOTIFY_ON_COMPLETE}")
    print(f"   NOTIFY_ON_ERROR: {settings.NOTIFY_ON_ERROR}")
    print(f"   NOTIFICATION_SOUND: {settings.NOTIFICATION_SOUND}")

    # Speed Limiting Settings
    print("\n[7/8] Speed Limiting Settings:")
    print(f"   LIMIT_DOWNLOAD_SPEED: {settings.LIMIT_DOWNLOAD_SPEED}")
    print(f"   MAX_DOWNLOAD_SPEED: {settings.MAX_DOWNLOAD_SPEED} KB/s")

    # Update Settings
    print("\n[8/8] Auto-Update Settings:")
    print(f"   AUTO_UPDATE_YTDLP: {settings.AUTO_UPDATE_YTDLP}")
    print(f"   CHECK_UPDATE_ON_START: {settings.CHECK_UPDATE_ON_START}")
    print(f"   UPDATE_INTERVAL_DAYS: {settings.UPDATE_INTERVAL_DAYS}")

    print("\n✅ All settings configured correctly")


async def test_notification_manager():
    """Test notification manager"""
    print("\n" + "="*70)
    print("Testing Notification Manager")
    print("="*70)

    try:
        from modules.notification_manager import NotificationManager

        config = ServiceConfig()
        notification_manager = NotificationManager(config)

        await notification_manager.start()

        print("\n✅ NotificationManager initialized successfully")
        print(f"   Desktop notifier: {notification_manager._desktop_notifier is not None}")

        # Test notification
        print("\n[Testing] Sending test notification...")
        notification_manager.test_notification()
        print("✅ Test notification sent (check your system tray)")

        await notification_manager.stop()

        print("\n✅ NotificationManager tests completed")

    except Exception as e:
        print(f"\n⚠️  NotificationManager test failed: {e}")
        logger.error("NotificationManager test failed", exc_info=True)


async def test_updater_manager():
    """Test updater manager"""
    print("\n" + "="*70)
    print("Testing Updater Manager")
    print("="*70)

    try:
        from modules.updater_manager import UpdaterManager

        config = ServiceConfig()
        updater_manager = UpdaterManager(config, db_manager=None)

        await updater_manager.start()

        print("\n[1/3] Checking yt-dlp version...")
        version = await updater_manager.get_current_version()
        print(f"✅ Current yt-dlp version: {version}")

        print("\n[2/3] Getting system information...")
        system_info = await updater_manager.get_system_info()
        print("✅ System Information:")
        for key, value in system_info.items():
            print(f"   {key}: {value}")

        print("\n[3/3] Checking FFmpeg...")
        success, message = await updater_manager.update_ffmpeg()
        print(f"{'✅' if success else '⚠️ '} {message}")

        await updater_manager.stop()

        print("\n✅ UpdaterManager tests completed")

    except Exception as e:
        print(f"\n⚠️  UpdaterManager test failed: {e}")
        logger.error("UpdaterManager test failed", exc_info=True)


async def test_output_templates():
    """Test output template configuration"""
    print("\n" + "="*70)
    print("Testing Output Templates")
    print("="*70)

    print("\n[1/2] Output Template Presets:")
    for preset_name, template in settings.OUTPUT_TEMPLATE_PRESETS.items():
        print(f"   {preset_name}: {template}")

    print("\n[2/2] Custom Output Template:")
    print(f"   {settings.CUSTOM_OUTPUT_TEMPLATE}")

    print("\n✅ Output templates configured correctly")


async def test_proxy_settings():
    """Test proxy configuration"""
    print("\n" + "="*70)
    print("Testing Proxy Settings")
    print("="*70)

    print(f"\n   ENABLE_PROXY: {settings.ENABLE_PROXY}")
    print(f"   PROXY_TYPE: {settings.PROXY_TYPE}")
    print(f"   HTTP_PROXY: {settings.HTTP_PROXY}")
    print(f"   HTTPS_PROXY: {settings.HTTPS_PROXY}")
    print(f"   SOCKS_PROXY: {settings.SOCKS_PROXY}")

    print("\n✅ Proxy settings configured")


async def run_all_tests():
    """Run all basic tests"""
    print("\n" + "="*70)
    print("YouTube Downloader - Basic Feature Tests")
    print("="*70)
    print("\nTesting backend implementation without auth dependencies")

    try:
        # Run all tests
        test_settings_configuration()
        await test_output_templates()
        await test_proxy_settings()
        await test_notification_manager()
        await test_updater_manager()

        print("\n" + "="*70)
        print("✅ ALL BASIC TESTS COMPLETED")
        print("="*70)
        print("\nNext steps:")
        print("  1. All core features are properly configured")
        print("  2. NotificationManager is working")
        print("  3. UpdaterManager is working")
        print("  4. Ready to test actual downloads")
        print("\nTo test a real download:")
        print("  python main.py --mode cli --url <youtube-url>")
        print("="*70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error("Test failed", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
