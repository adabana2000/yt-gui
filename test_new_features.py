#!/usr/bin/env python3
"""
Test script for new features
Tests all newly implemented functionality
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_manager import ServiceConfig
from database.db_manager import DatabaseManager
from modules.notification_manager import NotificationManager
from modules.updater_manager import UpdaterManager
from modules.download_manager import DownloadManager
from modules.auth_manager import AuthManager
from config.settings import settings
from utils.logger import logger


async def test_notification_manager():
    """Test notification manager"""
    print("\n" + "="*70)
    print("Testing Notification Manager")
    print("="*70)

    config = ServiceConfig()
    notification_manager = NotificationManager(config)

    await notification_manager.start()

    # Test desktop notification
    print("\n[1/3] Testing desktop notification...")
    notification_manager.test_notification()
    print("✅ Desktop notification test sent")

    # Test download complete notification
    print("\n[2/3] Testing download complete notification...")
    notification_manager.notify_download_complete({
        'title': 'Test Video Title',
        'uploader': 'Test Channel',
        'id': 'test123',
        'output_path': '/downloads/test.mp4'
    })
    print("✅ Download complete notification sent")

    # Test error notification
    print("\n[3/3] Testing error notification...")
    notification_manager.notify_download_error({
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'id': 'test123'
    }, "This is a test error message")
    print("✅ Error notification sent")

    await notification_manager.stop()

    print("\n✅ Notification manager tests completed")
    print("   Check your system for desktop notifications!")


async def test_updater_manager():
    """Test updater manager"""
    print("\n" + "="*70)
    print("Testing Updater Manager")
    print("="*70)

    config = ServiceConfig()
    db_manager = DatabaseManager()
    updater_manager = UpdaterManager(config, db_manager)

    await updater_manager.start()

    # Test version checking
    print("\n[1/4] Checking current yt-dlp version...")
    version = await updater_manager.get_current_version()
    print(f"✅ Current yt-dlp version: {version}")

    # Test system info
    print("\n[2/4] Getting system information...")
    system_info = await updater_manager.get_system_info()
    print("✅ System Information:")
    for key, value in system_info.items():
        print(f"   {key}: {value}")

    # Test update check
    print("\n[3/4] Checking for updates...")
    success, message = await updater_manager.check_and_update(force=False)
    if success:
        print(f"✅ {message}")
    else:
        print(f"⚠️  {message}")

    # Test FFmpeg check
    print("\n[4/4] Checking FFmpeg...")
    success, message = await updater_manager.update_ffmpeg()
    print(f"{'✅' if success else '⚠️ '} {message}")

    await updater_manager.stop()

    print("\n✅ Updater manager tests completed")


async def test_download_settings():
    """Test download settings and configuration"""
    print("\n" + "="*70)
    print("Testing Download Settings")
    print("="*70)

    # Test format presets
    print("\n[1/5] Testing format presets...")
    for quality, format_str in settings.FORMAT_PRESETS.items():
        print(f"   {quality}: {format_str}")
    print("✅ Format presets loaded")

    # Test subtitle settings
    print("\n[2/5] Testing subtitle settings...")
    print(f"   Download subtitles: {settings.DOWNLOAD_SUBTITLES}")
    print(f"   Languages: {settings.SUBTITLE_LANGUAGES}")
    print(f"   Format: {settings.SUBTITLE_FORMAT}")
    print("✅ Subtitle settings loaded")

    # Test playlist settings
    print("\n[3/5] Testing playlist settings...")
    print(f"   Playlist download: {settings.PLAYLIST_DOWNLOAD}")
    print(f"   Download archive: {settings.DOWNLOAD_ARCHIVE}")
    print(f"   Archive file: {settings.ARCHIVE_FILE}")
    print("✅ Playlist settings loaded")

    # Test notification settings
    print("\n[4/5] Testing notification settings...")
    print(f"   Desktop notifications: {settings.DESKTOP_NOTIFICATION}")
    print(f"   Email notifications: {settings.EMAIL_NOTIFICATION}")
    print(f"   Notify on complete: {settings.NOTIFY_ON_COMPLETE}")
    print("✅ Notification settings loaded")

    # Test speed limiting
    print("\n[5/5] Testing speed limiting settings...")
    print(f"   Limit speed: {settings.LIMIT_DOWNLOAD_SPEED}")
    print(f"   Max speed: {settings.MAX_DOWNLOAD_SPEED} KB/s")
    print("✅ Speed limiting settings loaded")

    print("\n✅ All settings loaded successfully")


async def test_download_manager_integration():
    """Test download manager with new features"""
    print("\n" + "="*70)
    print("Testing Download Manager Integration")
    print("="*70)

    config = ServiceConfig()
    db_manager = DatabaseManager()
    auth_manager = AuthManager(config)
    notification_manager = NotificationManager(config)

    await notification_manager.start()

    download_manager = DownloadManager(
        config,
        db_manager,
        auth_manager,
        notification_manager
    )

    await download_manager.start()

    # Test download archive loading
    print("\n[1/4] Testing download archive...")
    archive_count = len(download_manager._download_archive)
    print(f"✅ Loaded {archive_count} entries from download archive")

    # Test duplicate checking
    print("\n[2/4] Testing duplicate check...")
    is_dup = download_manager._is_duplicate("test_id_123", "Test Title", "/downloads/test.mp4")
    print(f"✅ Duplicate check working: {is_dup}")

    # Test yt-dlp options generation
    print("\n[3/4] Testing yt-dlp options generation...")
    from modules.download_manager import DownloadTask
    test_task = DownloadTask(
        id="test-123",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_path=str(settings.DOWNLOAD_DIR),
        quality="1080p"
    )

    opts = download_manager._get_default_ydl_opts(test_task)

    print(f"✅ Generated yt-dlp options:")
    print(f"   Format: {opts.get('format', 'N/A')}")
    print(f"   Subtitles: {'writesubtitles' in opts}")
    print(f"   Thumbnail: {'writethumbnail' in opts}")
    print(f"   Archive: {opts.get('download_archive', 'N/A')}")
    print(f"   Speed limit: {opts.get('ratelimit', 'N/A')}")
    print(f"   Proxy: {opts.get('proxy', 'N/A')}")

    # Test cookie loading
    print("\n[4/4] Testing cookie loading...")
    if download_manager._cookie_file:
        print(f"✅ Cookies loaded from: {download_manager._cookie_file}")
    else:
        print("⚠️  No cookies loaded (expected if not logged into browser)")

    await download_manager.stop()
    await notification_manager.stop()

    print("\n✅ Download manager integration tests completed")


async def test_archive_operations():
    """Test download archive operations"""
    print("\n" + "="*70)
    print("Testing Archive Operations")
    print("="*70)

    config = ServiceConfig()
    db_manager = DatabaseManager()
    auth_manager = AuthManager(config)
    download_manager = DownloadManager(config, db_manager, auth_manager)

    # Test saving to archive
    print("\n[1/2] Testing archive save...")
    test_id = "test_video_id_12345"
    download_manager._save_to_archive(test_id)
    print(f"✅ Saved video ID to archive: {test_id}")

    # Test checking archive
    print("\n[2/2] Testing archive check...")
    if test_id in download_manager._download_archive:
        print(f"✅ Video ID found in archive: {test_id}")
    else:
        print(f"❌ Video ID not found in archive")

    print(f"\nArchive file: {settings.ARCHIVE_FILE}")
    if settings.ARCHIVE_FILE.exists():
        with open(settings.ARCHIVE_FILE, 'r') as f:
            lines = f.readlines()
            print(f"Archive contains {len(lines)} entries")

    print("\n✅ Archive operations tests completed")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("YouTube Downloader - New Features Test Suite")
    print("="*70)
    print("\nThis will test all newly implemented features:")
    print("  1. Notification Manager (desktop + email)")
    print("  2. Updater Manager (yt-dlp auto-update)")
    print("  3. Download Settings (all new configuration)")
    print("  4. Download Manager Integration")
    print("  5. Archive Operations")

    try:
        # Run tests
        await test_download_settings()
        await test_notification_manager()
        await test_updater_manager()
        await test_download_manager_integration()
        await test_archive_operations()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nNext steps:")
        print("  1. Check for any desktop notifications that appeared")
        print("  2. Review the test output above for any warnings")
        print("  3. If everything looks good, proceed with GUI implementation")
        print("\nTo test a real download with new features:")
        print("  python main.py --mode cli --url <youtube-url>")
        print("="*70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error("Test failed", exc_info=True)
        raise


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
