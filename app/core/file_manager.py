"""
File management utilities for the application.
"""
import os
import asyncio
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
import uuid
import time

from app.config.settings import settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for the application."""

    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        self.ensure_temp_dir()

    def ensure_temp_dir(self) -> None:
        """Ensure temp directory exists."""
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.debug(f"Temp directory ensured: {self.temp_dir}")

    async def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file and return audio file path."""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Generate output filename
            video_name = Path(video_path).stem
            audio_path = os.path.join(self.temp_dir, f"{video_name}_audio.mp3")

            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-q:a', '0',
                '-map', 'a',
                audio_path,
                '-y'  # Overwrite if exists
            ]

            # Run ffmpeg in executor
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True)
            )

            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {process.stderr}")

            if not os.path.exists(audio_path):
                raise Exception("Audio extraction failed - no output file")

            logger.info(f"Audio extracted: {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            raise

    async def cleanup_file(self, file_path: str) -> bool:
        """Clean up a file. Returns True if successful."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
        return False

    async def cleanup_files(self, file_paths: List[str]) -> int:
        """Clean up multiple files. Returns number of successfully deleted files."""
        deleted = 0
        for file_path in file_paths:
            if await self.cleanup_file(file_path):
                deleted += 1
        return deleted

    async def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    async def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB."""
        size_bytes = await self.get_file_size(file_path)
        return size_bytes / (1024 * 1024)

    async def is_file_too_large(self, file_path: str, max_size: Optional[int] = None) -> bool:
        """Check if file exceeds maximum size."""
        if max_size is None:
            max_size = settings.MAX_FILE_SIZE

        size = await self.get_file_size(file_path)
        return size > max_size

    def create_temp_filename(self, prefix: str = "file", extension: str = "mp4") -> str:
        """Create a unique temporary filename."""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}.{extension}"
        return os.path.join(self.temp_dir, filename)

    async def convert_video_format(
            self,
            input_path: str,
            output_format: str = "mp4",
            codec: str = "copy"
    ) -> str:
        """Convert video to different format."""
        try:
            output_path = os.path.join(
                self.temp_dir,
                f"{Path(input_path).stem}.{output_format}"
            )

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c', codec,
                '-y',
                output_path
            ]

            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True)
            )

            if process.returncode != 0:
                raise Exception(f"FFmpeg conversion error: {process.stderr}")

            if not os.path.exists(output_path):
                raise Exception("Conversion failed - no output file")

            logger.info(f"Video converted: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video conversion error: {e}")
            raise

    async def get_temp_dir_size(self) -> Tuple[float, int]:
        """
        Get temp directory size.

        Returns:
            Tuple of (size_in_mb, file_count)
        """
        total_size = 0
        file_count = 0

        for dirpath, dirnames, filenames in os.walk(self.temp_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
                file_count += 1

        return total_size / (1024 * 1024), file_count

    async def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.

        Returns:
            Number of files deleted
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted = 0

        for dirpath, dirnames, filenames in os.walk(self.temp_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    file_mtime = os.path.getmtime(filepath)
                    if current_time - file_mtime > max_age_seconds:
                        if await self.cleanup_file(filepath):
                            deleted += 1
                except OSError:
                    continue

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old temp files (> {max_age_hours} hours)")

        return deleted


# Global file manager instance
file_manager = FileManager()


# Legacy async functions for backward compatibility
async def extract_audio_from_video(video_path: str) -> str:
    return await file_manager.extract_audio_from_video(video_path)


async def cleanup_file(file_path: str) -> bool:
    return await file_manager.cleanup_file(file_path)


async def get_file_size(file_path: str) -> int:
    return await file_manager.get_file_size(file_path)


async def is_file_too_large(file_path: str, max_size: Optional[int] = None) -> bool:
    return await file_manager.is_file_too_large(file_path, max_size)


async def create_temp_filename(prefix: str = "file", extension: str = "mp4") -> str:
    return file_manager.create_temp_filename(prefix, extension)