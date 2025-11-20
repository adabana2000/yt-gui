"""Test script for video download functionality"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_manager import ServiceConfig
from database.db_manager import DatabaseManager
from modules.download_manager import DownloadManager
from modules.auth_manager import AuthManager
from utils.logger import logger

async def test_video_info():
    """Test video info extraction"""
    # Popular test video that should always work
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video

    print("=" * 80)
    print("Testing video info extraction...")
    print(f"URL: {test_url}")
    print("=" * 80)

    try:
        # Initialize managers
        db_manager = DatabaseManager()
        config = ServiceConfig()
        auth_manager = AuthManager(config)
        download_manager = DownloadManager(config, db_manager, auth_manager)

        # Test video info extraction
        print("\n[1] Extracting video info (fast mode with extract_flat)...")
        info = await download_manager.get_video_info(test_url, use_cache=False, extract_flat=True)

        print(f"✓ Title: {info.get('title', 'N/A')}")
        print(f"✓ Channel: {info.get('uploader', 'N/A')}")
        print(f"✓ Duration: {info.get('duration', 'N/A')} seconds")
        print(f"✓ Video ID: {info.get('id', 'N/A')}")

        # Test detailed video info extraction
        print("\n[2] Extracting detailed video info...")
        detailed_info = await download_manager.get_video_info(test_url, use_cache=False, extract_flat=False)

        print(f"✓ Title: {detailed_info.get('title', 'N/A')}")
        print(f"✓ Channel: {detailed_info.get('uploader', 'N/A')}")
        print(f"✓ Views: {detailed_info.get('view_count', 'N/A')}")
        print(f"✓ Duration: {detailed_info.get('duration', 'N/A')} seconds")
        print(f"✓ Upload Date: {detailed_info.get('upload_date', 'N/A')}")
        print(f"✓ Description: {detailed_info.get('description', 'N/A')[:100]}...")

        # Check available formats
        formats = detailed_info.get('formats', [])
        print(f"✓ Available formats: {len(formats)}")
        if formats:
            print(f"  - Best format: {formats[-1].get('format', 'N/A')}")

        print("\n" + "=" * 80)
        print("✅ Video info extraction test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_channel_info():
    """Test channel info extraction"""
    # Test with a small channel
    test_channel_url = "https://www.youtube.com/@YouTube/videos"

    print("\n" + "=" * 80)
    print("Testing channel info extraction...")
    print(f"URL: {test_channel_url}")
    print("=" * 80)

    try:
        # Initialize managers
        db_manager = DatabaseManager()
        config = ServiceConfig()
        auth_manager = AuthManager(config)
        download_manager = DownloadManager(config, db_manager, auth_manager)

        # Test channel info extraction (just fetch a few videos)
        print("\n[1] Extracting channel videos (limited to first 5)...")

        import yt_dlp
        opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'playlist_items': '1-5',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_channel_url, download=False)

        channel_title = info.get('title', 'Unknown')
        entries = info.get('entries', [])

        print(f"✓ Channel: {channel_title}")
        print(f"✓ Videos found: {len(entries)}")

        if entries:
            print("\nFirst few videos:")
            for i, entry in enumerate(entries[:3], 1):
                print(f"  {i}. {entry.get('title', 'N/A')} (ID: {entry.get('id', 'N/A')})")

        print("\n" + "=" * 80)
        print("✅ Channel info extraction test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("YouTube Download Manager - Testing Suite")
    print("=" * 80)

    results = []

    # Test 1: Video info extraction
    result1 = await test_video_info()
    results.append(("Video Info Extraction", result1))

    # Small delay between tests
    await asyncio.sleep(2)

    # Test 2: Channel info extraction
    result2 = await test_channel_info()
    results.append(("Channel Info Extraction", result2))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
