"""Add multiple test history records"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import uuid

# Initialize database
db_manager = DatabaseManager()

print("=" * 80)
print("Adding Test History Data")
print("=" * 80)

# Test data samples
test_videos = [
    {
        'title': '【プログラミング入門】Python基礎講座',
        'uploader': 'プログラミング学習チャンネル',
        'channel_id': 'UCprogramming123',
        'duration': 1800,
        'filesize': 52428800,  # 50 MB
        'view_count': 50000,
    },
    {
        'title': '【料理】簡単！美味しいパスタの作り方',
        'uploader': 'クッキングチャンネル',
        'channel_id': 'UCcooking456',
        'duration': 600,
        'filesize': 31457280,  # 30 MB
        'view_count': 120000,
    },
    {
        'title': '【音楽】癒しのピアノメドレー 1時間',
        'uploader': 'リラックスミュージック',
        'channel_id': 'UCmusic789',
        'duration': 3600,
        'filesize': 104857600,  # 100 MB
        'view_count': 300000,
    },
    {
        'title': '【ゲーム実況】最新RPGゲームプレイ Part 1',
        'uploader': 'ゲーム実況者ABC',
        'channel_id': 'UCgaming012',
        'duration': 2400,
        'filesize': 73400320,  # 70 MB
        'view_count': 85000,
    },
    {
        'title': 'Daily Vlog - 東京散歩',
        'uploader': 'Vlogger XYZ',
        'channel_id': 'UCvlog345',
        'duration': 900,
        'filesize': 41943040,  # 40 MB
        'view_count': 25000,
    },
]

added = 0
skipped = 0

for i, video in enumerate(test_videos):
    video_id = f'test{i+1:03d}'
    url = f'https://www.youtube.com/watch?v={video_id}'

    # Check if already exists
    if db_manager.check_duplicate(url):
        print(f"Skipping (already exists): {video['title']}")
        skipped += 1
        continue

    # Create download history data
    download_info = {
        'id': str(uuid.uuid4()),
        'url': url,
        'title': video['title'],
        'uploader': video['uploader'],
        'channel_id': video['channel_id'],
        'channel_url': f'https://www.youtube.com/@{video["uploader"]}',
        'file_path': f'/downloads/{video["title"][:20]}.mp4',
        'filesize': video['filesize'],
        'duration': video['duration'],
        'format': 'bestvideo+bestaudio',
        'resolution': '1080p',
        'view_count': video['view_count'],
        'fps': 30,
        'vcodec': 'h264',
        'acodec': 'aac',
    }

    try:
        db_manager.add_download_history(download_info)
        print(f"✓ Added: {video['title']}")
        added += 1
    except Exception as e:
        print(f"✗ Failed to add {video['title']}: {e}")

print("\n" + "=" * 80)
print(f"Summary: Added {added}, Skipped {skipped}")
print("=" * 80)

# Show all history
print("\nAll history records:")
history = db_manager.get_download_history(limit=20)
for i, item in enumerate(history, 1):
    size_mb = item.file_size / 1024 / 1024 if item.file_size else 0
    print(f"{i}. {item.title}")
    print(f"   Channel: {item.channel_name}")
    print(f"   Date: {item.download_date}")
    print(f"   Size: {size_mb:.1f} MB")
    print()

# Show stats
print("=" * 80)
print("Statistics:")
stats = db_manager.get_download_stats()
print(f"Total downloads: {stats.get('total_downloads', 0)}")
print(f"Total size: {stats.get('total_size_bytes', 0) / 1024 / 1024 / 1024:.2f} GB")
print(f"Last week: {stats.get('downloads_last_week', 0)}")
print("=" * 80)
