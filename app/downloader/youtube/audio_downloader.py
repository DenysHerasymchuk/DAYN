import asyncio
import logging
import os
from typing import Callable, Optional

import imageio_ffmpeg
import yt_dlp

from app.config.constants import HttpConfig
from app.downloader.base import ProgressTracker

logger = logging.getLogger(__name__)


class YouTubeAudioDownloader:
    """Download YouTube audio."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def download(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        """Download audio only using yt-dlp with progress tracking."""
        tracker = ProgressTracker(progress_callback)

        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{self.temp_dir}/%(id)s_audio.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [tracker.hook],
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'http_headers': {
                    'User-Agent': HttpConfig.USER_AGENT,
                    'Accept': HttpConfig.ACCEPT,
                    'Accept-Language': HttpConfig.ACCEPT_LANGUAGE,
                },
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                'extractor_retries': 3
            }

            logger.info("Downloading YouTube audio")

            await tracker.start()

            loop = asyncio.get_event_loop()
            video_id = await loop.run_in_executor(
                None,
                lambda: self._download_with_ydl(url, ydl_opts)
            )

            await tracker.stop()

            # Find the downloaded file
            expected_filename = f"{self.temp_dir}/{video_id}_audio.mp3"
            if os.path.exists(expected_filename):
                return expected_filename

            for file in os.listdir(self.temp_dir):
                if video_id in file and file.endswith('.mp3'):
                    return f"{self.temp_dir}/{file}"

            raise Exception(f"Downloaded audio file not found for video {video_id}")

        except Exception as e:
            logger.error(f"YouTube audio error: {e}")
            raise

    def _download_with_ydl(self, url: str, ydl_opts: dict) -> str:
        """Helper to download synchronously and return video ID."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id', 'youtube')
            ydl.download([url])
            return video_id
