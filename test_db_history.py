"""Test database and history display"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from database.models import DownloadHistory
from datetime import datetime
import uuid

# Initialize database
db_manager = DatabaseManager()

print("=" * 80)
print("Database History Test")
print("=" * 80)

# Check existing history
print("\n[1] Checking existing history...")
history = db_manager.get_download_history(limit=10)
print(f"Found {len(history)} history records in database")

if history:
    print("\nExisting records:")
    for i, item in enumerate(history[:5], 1):
        print(f"{i}. Title: {item.title}")
        print(f"   Channel: {item.channel_name}")
        print(f"   Date: {item.download_date}")
        print(f"   File: {item.file_path}")
        print(f"   Size: {item.file_size} bytes")
        print()
else:
    print("No history records found. Adding test data...")

    # Add test data
    test_data = {
        'id': str(uuid.uuid4()),
        'url': 'https://www.youtube.com/watch?v=test123',
        'title': 'テスト動画 - Test Video',
        'uploader': 'テストチャンネル',
        'channel_id': 'UCtest123',
        'channel_url': 'https://www.youtube.com/@testchannel',
        'file_path': '/downloads/test_video.mp4',
        'filesize': 10485760,  # 10 MB
        'duration': 300,
        'format': 'best',
        'resolution': '1080p',
        'view_count': 1000,
    }

    try:
        db_manager.add_download_history(test_data)
        print("✓ Test data added successfully")

        # Check again
        history = db_manager.get_download_history(limit=10)
        print(f"✓ Now found {len(history)} history records")

        if history:
            item = history[0]
            print(f"\nTest record:")
            print(f"  Title: {item.title}")
            print(f"  Channel: {item.channel_name}")
            print(f"  Date: {item.download_date}")
            print(f"  File: {item.file_path}")
            print(f"  Size: {item.file_size} bytes")
    except Exception as e:
        print(f"✗ Failed to add test data: {e}")
        import traceback
        traceback.print_exc()

# Test stats
print("\n[2] Testing statistics...")
try:
    stats = db_manager.get_download_stats()
    print(f"Total downloads: {stats.get('total_downloads', 0)}")
    print(f"Total size: {stats.get('total_size_bytes', 0) / 1024 / 1024:.2f} MB")
    print(f"Last week: {stats.get('downloads_last_week', 0)}")
except Exception as e:
    print(f"✗ Failed to get stats: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test completed")
print("=" * 80)
