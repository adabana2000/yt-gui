"""Metadata manager for handling video metadata and file organization"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import re
from datetime import datetime
import aiofiles

from core.service_manager import BaseService, ServiceConfig
from database.db_manager import DatabaseManager
from utils.logger import logger


class MetadataManager(BaseService):
    """Metadata manager for file organization and metadata"""

    def __init__(self, config: ServiceConfig, db_manager: DatabaseManager):
        """Initialize metadata manager

        Args:
            config: Service configuration
            db_manager: Database manager instance
        """
        super().__init__(config, "MetadataManager")
        self.db_manager = db_manager

    async def start(self) -> None:
        """Start metadata manager"""
        logger.info("Starting Metadata Manager...")

    async def stop(self) -> None:
        """Stop metadata manager"""
        logger.info("Stopping Metadata Manager...")

    def generate_filename(
        self,
        metadata: Dict[str, Any],
        template: str = "{title}",
        max_length: int = 200
    ) -> str:
        """Generate filename from metadata

        Args:
            metadata: Video metadata
            template: Filename template
            max_length: Maximum filename length

        Returns:
            Generated filename
        """
        # Available template variables
        variables = {
            'title': metadata.get('title', 'Unknown'),
            'channel': metadata.get('uploader', 'Unknown'),
            'channel_id': metadata.get('channel_id', ''),
            'id': metadata.get('id', ''),
            'date': metadata.get('upload_date', ''),
            'ext': metadata.get('ext', 'mp4'),
            'resolution': metadata.get('resolution', ''),
            'fps': metadata.get('fps', ''),
        }

        # Format date if available
        if variables['date']:
            try:
                date_obj = datetime.strptime(variables['date'], '%Y%m%d')
                variables['date'] = date_obj.strftime('%Y-%m-%d')
            except:
                pass

        # Replace template variables
        filename = template
        for key, value in variables.items():
            filename = filename.replace(f"{{{key}}}", str(value))

        # Sanitize filename
        filename = self._sanitize_filename(filename)

        # Truncate if too long
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}" if ext else name

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '_', filename)

        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')

        return filename

    def generate_directory_path(
        self,
        metadata: Dict[str, Any],
        base_path: str,
        structure: str = "channel"
    ) -> Path:
        """Generate directory path based on metadata

        Args:
            metadata: Video metadata
            base_path: Base directory path
            structure: Directory structure (channel, date, playlist, custom)

        Returns:
            Generated directory path
        """
        base = Path(base_path)

        if structure == "channel":
            channel = self._sanitize_filename(metadata.get('uploader', 'Unknown'))
            return base / channel

        elif structure == "date":
            upload_date = metadata.get('upload_date', '')
            if upload_date:
                try:
                    date_obj = datetime.strptime(upload_date, '%Y%m%d')
                    return base / date_obj.strftime('%Y') / date_obj.strftime('%m')
                except:
                    pass
            return base / "Unknown_Date"

        elif structure == "playlist":
            playlist = metadata.get('playlist', 'No_Playlist')
            playlist = self._sanitize_filename(playlist)
            return base / playlist

        elif structure == "channel_date":
            channel = self._sanitize_filename(metadata.get('uploader', 'Unknown'))
            upload_date = metadata.get('upload_date', '')
            if upload_date:
                try:
                    date_obj = datetime.strptime(upload_date, '%Y%m%d')
                    return base / channel / date_obj.strftime('%Y-%m')
                except:
                    pass
            return base / channel

        else:
            return base

    async def save_metadata(
        self,
        metadata: Dict[str, Any],
        output_path: Path,
        format: str = "json"
    ) -> bool:
        """Save metadata to file

        Args:
            metadata: Metadata dictionary
            output_path: Output file path
            format: Output format (json, txt)

        Returns:
            True if successful
        """
        try:
            output_path = Path(output_path)

            if format == "json":
                async with aiofiles.open(output_path.with_suffix('.info.json'), 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))

            elif format == "txt":
                async with aiofiles.open(output_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    lines = [
                        f"Title: {metadata.get('title', 'N/A')}",
                        f"Channel: {metadata.get('uploader', 'N/A')}",
                        f"Upload Date: {metadata.get('upload_date', 'N/A')}",
                        f"Duration: {metadata.get('duration', 'N/A')} seconds",
                        f"Views: {metadata.get('view_count', 'N/A')}",
                        f"Likes: {metadata.get('like_count', 'N/A')}",
                        f"Description:\n{metadata.get('description', 'N/A')}",
                    ]
                    await f.write('\n'.join(lines))

            logger.info(f"Saved metadata to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False

    async def download_thumbnail(
        self,
        metadata: Dict[str, Any],
        output_path: Path
    ) -> Optional[str]:
        """Download video thumbnail

        Args:
            metadata: Video metadata
            output_path: Output directory path

        Returns:
            Downloaded thumbnail path or None
        """
        try:
            import aiohttp

            thumbnails = metadata.get('thumbnails', [])
            if not thumbnails:
                return None

            # Get highest resolution thumbnail
            thumbnail_url = thumbnails[-1]['url']

            output_file = Path(output_path).with_suffix('.jpg')

            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(output_file, 'wb') as f:
                            await f.write(await response.read())

                        logger.info(f"Downloaded thumbnail: {output_file}")
                        return str(output_file)

        except Exception as e:
            logger.error(f"Failed to download thumbnail: {e}")
            return None

    async def download_subtitles(
        self,
        metadata: Dict[str, Any],
        output_path: Path,
        languages: Optional[List[str]] = None
    ) -> List[str]:
        """Download subtitles

        Args:
            metadata: Video metadata
            output_path: Output directory path
            languages: List of language codes (None for all)

        Returns:
            List of downloaded subtitle file paths
        """
        try:
            subtitles = metadata.get('subtitles', {})
            if not subtitles:
                logger.info("No subtitles available")
                return []

            downloaded = []

            for lang, subs in subtitles.items():
                if languages and lang not in languages:
                    continue

                for sub in subs:
                    if sub.get('ext') == 'vtt':
                        sub_url = sub['url']
                        sub_file = Path(output_path).with_suffix(f'.{lang}.vtt')

                        try:
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                async with session.get(sub_url) as response:
                                    if response.status == 200:
                                        async with aiofiles.open(sub_file, 'wb') as f:
                                            await f.write(await response.read())
                                        downloaded.append(str(sub_file))
                                        logger.info(f"Downloaded subtitle: {sub_file}")
                                        break
                        except:
                            pass

            return downloaded

        except Exception as e:
            logger.error(f"Failed to download subtitles: {e}")
            return []

    async def extract_chapters(
        self,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract video chapters

        Args:
            metadata: Video metadata

        Returns:
            List of chapter dictionaries
        """
        chapters = metadata.get('chapters', [])
        return [
            {
                'title': chapter.get('title', f"Chapter {i+1}"),
                'start_time': chapter.get('start_time', 0),
                'end_time': chapter.get('end_time', 0)
            }
            for i, chapter in enumerate(chapters)
        ]

    async def organize_file(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        base_path: Optional[str] = None,
        structure: str = "channel",
        filename_template: str = "{title}"
    ) -> Optional[str]:
        """Organize file into structured directory

        Args:
            file_path: Current file path
            metadata: File metadata
            base_path: Base directory for organization
            structure: Directory structure
            filename_template: Filename template

        Returns:
            New file path or None
        """
        try:
            source = Path(file_path)
            if not source.exists():
                logger.error(f"File not found: {file_path}")
                return None

            # Generate destination path
            base = Path(base_path) if base_path else source.parent
            dest_dir = self.generate_directory_path(metadata, str(base), structure)
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = self.generate_filename(metadata, filename_template)
            dest_file = dest_dir / filename

            # Move file
            source.rename(dest_file)
            logger.info(f"Organized file: {source} -> {dest_file}")

            return str(dest_file)

        except Exception as e:
            logger.error(f"Failed to organize file: {e}")
            return None

    def get_metadata_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata summary

        Args:
            metadata: Full metadata

        Returns:
            Summary dictionary
        """
        return {
            'title': metadata.get('title', 'Unknown'),
            'channel': metadata.get('uploader', 'Unknown'),
            'duration': metadata.get('duration', 0),
            'upload_date': metadata.get('upload_date'),
            'view_count': metadata.get('view_count', 0),
            'like_count': metadata.get('like_count', 0),
            'comment_count': metadata.get('comment_count', 0),
            'resolution': metadata.get('resolution'),
            'fps': metadata.get('fps'),
            'filesize': metadata.get('filesize', 0),
        }
