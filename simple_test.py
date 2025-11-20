"""Simple test script for YouTube download functionality"""
import yt_dlp

def test_video_info():
    """Test video info extraction with new settings"""
    # Popular test video that should always work
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video

    print("=" * 80)
    print("Testing YouTube Video Info Extraction with iOS/Android client")
    print(f"URL: {test_url}")
    print("=" * 80)

    # Test with new settings
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,  # Skip SSL verification for testing
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }

    try:
        print("\n[1] Extracting video info with iOS/Android client settings...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

        print(f"✓ Title: {info.get('title', 'N/A')}")
        print(f"✓ Channel: {info.get('uploader', 'N/A')}")
        print(f"✓ Views: {info.get('view_count', 'N/A'):,}")
        print(f"✓ Duration: {info.get('duration', 'N/A')} seconds")
        print(f"✓ Upload Date: {info.get('upload_date', 'N/A')}")
        print(f"✓ Video ID: {info.get('id', 'N/A')}")

        # Check available formats
        formats = info.get('formats', [])
        print(f"✓ Available formats: {len(formats)}")

        if formats:
            # Show best quality video format
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            if video_formats:
                best_video = video_formats[-1]
                print(f"  - Best video format: {best_video.get('format')} "
                      f"({best_video.get('width')}x{best_video.get('height')}, "
                      f"{best_video.get('ext')})")

        print("\n" + "=" * 80)
        print("✅ Video info extraction test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_channel_videos():
    """Test channel video listing with new settings"""
    # Test with YouTube's official channel
    test_channel_url = "https://www.youtube.com/@YouTube/videos"

    print("\n" + "=" * 80)
    print("Testing Channel Video Listing with iOS/Android client")
    print(f"URL: {test_channel_url}")
    print("=" * 80)

    opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,  # Skip SSL verification for testing
        'playlist_items': '1-5',  # Only fetch first 5 videos
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }

    try:
        print("\n[1] Fetching first 5 videos from channel...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_channel_url, download=False)

        channel_title = info.get('title', 'Unknown')
        entries = info.get('entries', [])

        print(f"✓ Channel: {channel_title}")
        print(f"✓ Videos fetched: {len(entries)}")

        if entries:
            print("\nFirst few videos:")
            for i, entry in enumerate(entries[:5], 1):
                title = entry.get('title', 'N/A')
                video_id = entry.get('id', 'N/A')
                print(f"  {i}. {title}")
                print(f"     ID: {video_id}")

        print("\n" + "=" * 80)
        print("✅ Channel video listing test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_video():
    """Test with a different popular video"""
    # Test with a different video to ensure consistency
    test_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"  # PSY - GANGNAM STYLE

    print("\n" + "=" * 80)
    print("Testing with Popular Video (Gangnam Style)")
    print(f"URL: {test_url}")
    print("=" * 80)

    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Fast extraction
        'nocheckcertificate': True,  # Skip SSL verification for testing
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }

    try:
        print("\n[1] Quick video info extraction (extract_flat mode)...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

        print(f"✓ Title: {info.get('title', 'N/A')}")
        print(f"✓ Channel: {info.get('uploader', 'N/A')}")
        print(f"✓ Video ID: {info.get('id', 'N/A')}")
        print(f"✓ Duration: {info.get('duration', 'N/A')} seconds")

        print("\n" + "=" * 80)
        print("✅ Popular video test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("YouTube Download Fix - Testing Suite")
    print("Testing iOS/Android client configuration")
    print("=" * 80)

    results = []

    # Test 1: Basic video info
    result1 = test_video_info()
    results.append(("Basic Video Info", result1))

    # Test 2: Channel videos
    result2 = test_channel_videos()
    results.append(("Channel Video Listing", result2))

    # Test 3: Different video
    result3 = test_different_video()
    results.append(("Popular Video Test", result3))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = 0
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed:
            passed_count += 1

    print("\n" + "=" * 80)
    print(f"Results: {passed_count}/{len(results)} tests passed")
    if passed_count == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("\nThe iOS/Android client configuration is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease check the error messages above.")
    print("=" * 80)

    return passed_count == len(results)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
