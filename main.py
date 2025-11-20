"""Main entry point for YouTube Downloader"""
import sys
import argparse
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def run_gui():
    """Run GUI application"""
    from gui.main_window import main
    main()


def run_api():
    """Run API server"""
    from api.main import run_server
    run_server()


def run_cli(args):
    """Run CLI application"""
    import asyncio
    from core.service_manager import service_manager, ServiceConfig
    from database.db_manager import DatabaseManager
    from modules.download_manager import DownloadManager
    from modules.auth_manager import AuthManager

    async def download_url(url: str):
        # Initialize
        db_manager = DatabaseManager()
        config = ServiceConfig()
        auth_manager = AuthManager(config)
        download_manager = DownloadManager(config, db_manager, auth_manager)

        service_manager.register_service("download", download_manager)
        await service_manager.start_all()

        # Add download
        print(f"Downloading: {url}")
        task = await download_manager.add_download(url)

        # Wait for completion
        while task.status.value in ['pending', 'downloading', 'processing']:
            await asyncio.sleep(1)
            status = download_manager.get_download_status(task.id)
            if status:
                print(f"Progress: {status['progress']:.1f}% - Speed: {status['speed']/1024/1024:.2f} MB/s")

        print(f"Download completed: {task.status.value}")

        # Cleanup
        await service_manager.stop_all()

    if args.url:
        asyncio.run(download_url(args.url))
    else:
        print("Please provide a URL with --url parameter")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="YouTube Downloader - yt-dlpベースの高機能ダウンローダー"
    )

    parser.add_argument(
        '--mode',
        choices=['gui', 'api', 'cli'],
        default='gui',
        help='実行モード (デフォルト: gui)'
    )

    parser.add_argument(
        '--url',
        type=str,
        help='ダウンロードするURL (CLIモード時)'
    )

    args = parser.parse_args()

    if args.mode == 'gui':
        run_gui()
    elif args.mode == 'api':
        run_api()
    elif args.mode == 'cli':
        run_cli(args)


if __name__ == "__main__":
    main()
