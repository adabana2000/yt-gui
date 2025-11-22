"""Test enhanced YouTube download configuration"""
import yt_dlp

def test_single_video():
    """Test single video download with enhanced settings"""
    # Use a popular, publicly available video
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video

    print("=" * 80)
    print("Testing Enhanced YouTube Configuration")
    print(f"URL: {test_url}")
    print("=" * 80)

    opts = {
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'format': 'bestvideo*+bestaudio/best',
        'nocheckcertificate': True,
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 3,
        # Enhanced headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        # Enhanced client configuration
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'mweb', 'android', 'tv_embedded'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'sleep_interval': 1,
        'max_sleep_interval': 5,
        'sleep_interval_requests': 1,
        'sleep_interval_subtitles': 1,
    }

    try:
        print("\n[1] Extracting video info with enhanced configuration...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

        if info:
            print(f"✓ Title: {info.get('title', 'N/A')}")
            print(f"✓ Channel: {info.get('uploader', 'N/A')}")
            print(f"✓ Duration: {info.get('duration', 'N/A')} seconds")
            print(f"✓ Views: {info.get('view_count', 'N/A'):,}")

            formats = info.get('formats', [])
            print(f"✓ Available formats: {len(formats)}")

            if formats:
                print("\n  Top 5 formats:")
                for i, fmt in enumerate(formats[-5:], 1):
                    ext = fmt.get('ext', 'N/A')
                    quality = fmt.get('format_note', 'N/A')
                    size = fmt.get('filesize', 0)
                    size_mb = size / 1024 / 1024 if size else 0
                    print(f"  {i}. {ext} - {quality} - {size_mb:.1f} MB")

            print("\n" + "=" * 80)
            print("✅ Enhanced configuration test PASSED!")
            print("=" * 80)
            return True
        else:
            print("✗ Failed to extract video info")
            return False

    except Exception as e:
        print(f"\n❌ Test FAILED with error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

        # Check for specific error patterns
        error_str = str(e)
        if "not available on this app" in error_str.lower():
            print("\n⚠️  Still getting 'not available on this app' error")
            print("This may require additional configuration such as:")
            print("  - Using cookies from browser")
            print("  - Using po_token and visitor_data")
            print("  - Trying different video URLs")
        elif "requested format is not available" in error_str.lower():
            print("\n⚠️  Format selection issue")
            print("The requested format may not exist for this video")

        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_problematic_video():
    """Test with a video that might have restrictions"""
    test_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"  # Gangnam Style

    print("\n" + "=" * 80)
    print("Testing with Popular Video (may have more restrictions)")
    print(f"URL: {test_url}")
    print("=" * 80)

    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Just get basic info
        'nocheckcertificate': True,
        'retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'mweb', 'android', 'tv_embedded'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }

    try:
        print("\n[1] Quick video info extraction...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

        if info:
            print(f"✓ Title: {info.get('title', 'N/A')}")
            print(f"✓ Channel: {info.get('uploader', 'N/A')}")
            print(f"✓ Video ID: {info.get('id', 'N/A')}")

            print("\n" + "=" * 80)
            print("✅ Popular video test PASSED!")
            print("=" * 80)
            return True
        else:
            return False

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("Enhanced YouTube Download Configuration - Test Suite")
    print("Testing improved client configuration and headers")
    print("=" * 80)

    results = []

    # Test 1: Basic video
    result1 = test_single_video()
    results.append(("Enhanced Configuration Test", result1))

    # Test 2: Popular video
    result2 = test_problematic_video()
    results.append(("Popular Video Test", result2))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe enhanced configuration is working correctly!")
        print("\nKey improvements:")
        print("  • Multiple client fallback: ios → mweb → android → tv_embedded")
        print("  • Enhanced HTTP headers with modern User-Agent")
        print("  • Increased retry attempts (10x)")
        print("  • Better format selection with wildcards")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nIf 'not available on this app' errors persist:")
        print("  1. Try using browser cookies (--cookies-from-browser chrome)")
        print("  2. Update yt-dlp to the absolute latest version")
        print("  3. Some videos may require po_token/visitor_data (advanced)")

    print("=" * 80)

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
