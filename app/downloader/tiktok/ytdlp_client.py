import asyncio
import logging
import os
from typing import Callable, Optional

import aiofiles.os
import imageio_ffmpeg
import yt_dlp

from app.config.constants import HttpConfig
from app.config.settings import settings
from app.downloader.base import ProgressTracker

logger = logging.getLogger(__name__)


class TikTokVideoDownloader:
    """Download TikTok videos using yt-dlp."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def get_info(self, url: str) -> dict:
        """Extract video info without downloading. Returns estimated filesize."""
        loop = asyncio.get_event_loop()

        def extract():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'http_headers': {'User-Agent': HttpConfig.USER_AGENT},
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, extract)

        return {
            'filesize': info.get('filesize') or info.get('filesize_approx') or 0,
            'filesize_approx': info.get('filesize_approx'),
            'duration': info.get('duration') or 0,
            'title': info.get('title'),
            'is_estimated': info.get('filesize') is None,
        }

    async def download(self, url: str, video_id: str, extract_audio: bool = False,
                       progress_callback: Optional[Callable] = None) -> str:
        """Download TikTok video or audio using yt-dlp."""
        tracker = ProgressTracker(progress_callback)

        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            common_opts = {
                'concurrent_fragment_downloads': settings.CONCURRENT_FRAGMENT_DOWNLOADS,
                'http_headers': {
                    'User-Agent': HttpConfig.USER_AGENT,
                    'Accept': HttpConfig.ACCEPT,
                    'Accept-Language': HttpConfig.ACCEPT_LANGUAGE,
                },
                'socket_timeout': 30,
                'nocheckcertificate': True,
                'retries': 3,
                'fragment_retries': 3,
                'extractor_retries': 3
            }

            if extract_audio:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.temp_dir, '%(id)s_audio.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'ffmpeg_location': ffmpeg_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [tracker.hook],
                    **common_opts,
                }
            else:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(self.temp_dir, '%(id)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': ffmpeg_path,
                    'progress_hooks': [tracker.hook],
                    **common_opts,
                }

            logger.info(f"Downloading TikTok {'audio' if extract_audio else 'video'} using yt-dlp: {url}")

            await tracker.start()

            loop = asyncio.get_event_loop()

            def download_with_ydlp():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if 'entries' in info:
                        info = info['entries'][0]
                    return info.get('id', 'tiktok')

            downloaded_id = await loop.run_in_executor(None, download_with_ydlp)

            await tracker.stop()

            # Find the downloaded file
            if extract_audio:
                return self._find_audio_file(downloaded_id)
            else:
                return await self._find_video_file(downloaded_id)

        except Exception as e:
            logger.error(f"yt-dlp TikTok download error: {e}")
            raise

    def _find_audio_file(self, downloaded_id: str) -> str:
        """Find downloaded audio file."""
        for file in os.listdir(self.temp_dir):
            if downloaded_id in file and file.endswith('.mp3'):
                file_path = os.path.join(self.temp_dir, file)
                logger.info(f"Downloaded TikTok audio: {file_path}")
                return file_path

        audio_extensions = ['.m4a', '.aac', '.opus', '.flac', '.wav']
        for ext in audio_extensions:
            for file in os.listdir(self.temp_dir):
                if downloaded_id in file and file.endswith(ext):
                    file_path = os.path.join(self.temp_dir, file)
                    logger.info(f"Downloaded TikTok audio ({ext}): {file_path}")
                    return file_path

        raise Exception("Downloaded audio file not found for TikTok")

    async def _find_video_file(self, downloaded_id: str) -> str:
        """Find downloaded video file, converting to mp4 if needed."""
        for file in os.listdir(self.temp_dir):
            if downloaded_id in file and (
                    file.endswith('.mp4') or file.endswith('.mkv') or file.endswith('.webm')):
                file_path = os.path.join(self.temp_dir, file)

                if not file.endswith('.mp4'):
                    mp4_path = os.path.join(self.temp_dir, f"{downloaded_id}.mp4")
                    await self._convert_to_mp4(file_path, mp4_path)
                    await aiofiles.os.remove(file_path)
                    file_path = mp4_path

                logger.info(f"Downloaded TikTok video: {file_path}")
                return file_path

        raise Exception("Downloaded video file not found for TikTok")

    async def _convert_to_mp4(self, input_path: str, output_path: str):
        """Convert video to mp4 format using ffmpeg."""
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            process = await asyncio.create_subprocess_exec(
                ffmpeg_path,
                '-i', input_path,
                '-c', 'copy',
                '-y',
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            if await aiofiles.os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Conversion failed")
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            raise
