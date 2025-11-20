"""Encode manager for video/audio processing with FFmpeg"""
from typing import Optional, Dict, Any, List
import subprocess
import asyncio
from pathlib import Path
import ffmpeg

from core.service_manager import BaseService, ServiceConfig
from config.settings import settings
from utils.logger import logger


class EncodeManager(BaseService):
    """Encode manager for video/audio processing"""

    def __init__(self, config: ServiceConfig):
        """Initialize encode manager

        Args:
            config: Service configuration
        """
        super().__init__(config, "EncodeManager")
        self.gpu_available = {}
        self.ffmpeg_path = None

    async def start(self) -> None:
        """Start encode manager"""
        logger.info("Starting Encode Manager...")
        self._check_ffmpeg()
        if settings.ENABLE_GPU:
            self.gpu_available = await self._check_gpu_availability()
        logger.info(f"Encode Manager started - GPU: {self.gpu_available}")

    async def stop(self) -> None:
        """Stop encode manager"""
        logger.info("Stopping Encode Manager...")

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed

        Returns:
            True if available
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            self.ffmpeg_path = 'ffmpeg'
            logger.info("FFmpeg is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False

    async def _check_gpu_availability(self) -> Dict[str, bool]:
        """Check GPU availability for hardware encoding

        Returns:
            Dictionary of available GPUs
        """
        availability = {
            'nvidia': False,
            'intel': False,
            'amd': False
        }

        # Check NVIDIA GPU
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                check=True
            )
            availability['nvidia'] = True
            logger.info("NVIDIA GPU detected")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check Intel QuickSync (via FFmpeg encoders)
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True
            )
            if 'h264_qsv' in result.stdout:
                availability['intel'] = True
                logger.info("Intel QuickSync detected")
        except:
            pass

        # Check AMD
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True
            )
            if 'h264_amf' in result.stdout:
                availability['amd'] = True
                logger.info("AMD GPU detected")
        except:
            pass

        return availability

    def _get_encoder(self, codec: str = 'h264', use_gpu: bool = True) -> str:
        """Get appropriate encoder based on codec and GPU availability

        Args:
            codec: Video codec (h264, h265, vp9)
            use_gpu: Whether to use GPU acceleration

        Returns:
            Encoder name
        """
        if not use_gpu or not settings.ENABLE_GPU:
            return {
                'h264': 'libx264',
                'h265': 'libx265',
                'vp9': 'libvpx-vp9'
            }.get(codec, 'libx264')

        # GPU encoder selection
        if self.gpu_available.get('nvidia'):
            return {
                'h264': 'h264_nvenc',
                'h265': 'hevc_nvenc'
            }.get(codec, 'h264_nvenc')

        elif self.gpu_available.get('intel'):
            return {
                'h264': 'h264_qsv',
                'h265': 'hevc_qsv'
            }.get(codec, 'h264_qsv')

        elif self.gpu_available.get('amd'):
            return {
                'h264': 'h264_amf',
                'h265': 'hevc_amf'
            }.get(codec, 'h264_amf')

        # Fallback to software encoding
        return 'libx264'

    async def encode_video(
        self,
        input_file: str,
        output_file: str,
        codec: str = 'h264',
        preset: str = 'medium',
        bitrate: Optional[str] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        use_gpu: bool = True,
        audio_codec: str = 'aac',
        audio_bitrate: str = '128k'
    ) -> bool:
        """Encode video file

        Args:
            input_file: Input file path
            output_file: Output file path
            codec: Video codec
            preset: Encoding preset
            bitrate: Video bitrate
            resolution: Output resolution (e.g., '1920:1080')
            fps: Output FPS
            use_gpu: Use GPU acceleration
            audio_codec: Audio codec
            audio_bitrate: Audio bitrate

        Returns:
            True if successful
        """
        try:
            logger.info(f"Encoding video: {input_file} -> {output_file}")

            # Get encoder
            encoder = self._get_encoder(codec, use_gpu)

            # Build FFmpeg command
            stream = ffmpeg.input(input_file)

            # Video filters
            video_args = {}
            if resolution:
                stream = ffmpeg.filter(stream, 'scale', resolution)
            if fps:
                stream = ffmpeg.filter(stream, 'fps', fps=fps)

            # Encoding parameters
            output_params = {
                'c:v': encoder,
                'c:a': audio_codec,
                'b:a': audio_bitrate,
            }

            # Preset handling
            if 'nvenc' in encoder:
                output_params['preset'] = 'p4'  # NVENC preset
            else:
                output_params['preset'] = preset

            if bitrate:
                output_params['b:v'] = bitrate

            # Output
            stream = ffmpeg.output(stream, output_file, **output_params)

            # Execute
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
            )

            logger.info(f"Video encoding completed: {output_file}")
            return True

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return False

    async def extract_audio(
        self,
        input_file: str,
        output_file: str,
        format: str = 'mp3',
        bitrate: str = '192k'
    ) -> bool:
        """Extract audio from video

        Args:
            input_file: Input file path
            output_file: Output file path
            format: Audio format (mp3, aac, flac, opus)
            bitrate: Audio bitrate

        Returns:
            True if successful
        """
        try:
            logger.info(f"Extracting audio: {input_file} -> {output_file}")

            codec_map = {
                'mp3': 'libmp3lame',
                'aac': 'aac',
                'flac': 'flac',
                'opus': 'libopus',
                'ogg': 'libvorbis'
            }

            stream = ffmpeg.input(input_file)
            stream = ffmpeg.output(
                stream,
                output_file,
                acodec=codec_map.get(format, 'libmp3lame'),
                audio_bitrate=bitrate,
                vn=None  # No video
            )

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True)
            )

            logger.info(f"Audio extraction completed: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return False

    async def merge_video_audio(
        self,
        video_file: str,
        audio_file: str,
        output_file: str
    ) -> bool:
        """Merge separate video and audio files

        Args:
            video_file: Video file path
            audio_file: Audio file path
            output_file: Output file path

        Returns:
            True if successful
        """
        try:
            logger.info(f"Merging video and audio: {video_file} + {audio_file}")

            video = ffmpeg.input(video_file)
            audio = ffmpeg.input(audio_file)

            stream = ffmpeg.output(
                video,
                audio,
                output_file,
                vcodec='copy',
                acodec='copy'
            )

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True)
            )

            logger.info(f"Merge completed: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return False

    async def trim_video(
        self,
        input_file: str,
        output_file: str,
        start_time: str,
        end_time: Optional[str] = None,
        duration: Optional[str] = None
    ) -> bool:
        """Trim video

        Args:
            input_file: Input file path
            output_file: Output file path
            start_time: Start time (HH:MM:SS or seconds)
            end_time: End time (HH:MM:SS or seconds)
            duration: Duration (HH:MM:SS or seconds)

        Returns:
            True if successful
        """
        try:
            logger.info(f"Trimming video: {input_file}")

            stream = ffmpeg.input(input_file, ss=start_time)

            if duration:
                stream = ffmpeg.output(stream, output_file, t=duration, c='copy')
            elif end_time:
                stream = ffmpeg.output(stream, output_file, to=end_time, c='copy')
            else:
                stream = ffmpeg.output(stream, output_file, c='copy')

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True)
            )

            logger.info(f"Trim completed: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Trim failed: {e}")
            return False

    async def get_video_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get video file information

        Args:
            file_path: Video file path

        Returns:
            Video information dictionary or None
        """
        try:
            probe = ffmpeg.probe(file_path)
            video_info = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            audio_info = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )

            return {
                'format': probe['format'],
                'video': video_info,
                'audio': audio_info
            }

        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
