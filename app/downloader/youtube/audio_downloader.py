import asyncio
import logging
import os
from typing import Callable, Optional

import imageio_ffmpeg
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeAudioDownloader:
    """Download YouTube audio."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def download(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        """Download audio only using yt-dlp with progress tracking."""
        try:
            # Shared progress state between threads
            progress_state = {'percent': 0, 'downloading': True}

            # Progress hook runs in the download thread
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0%').strip('%')
                    try:
                        progress_state['percent'] = float(percent_str)
                    except ValueError:
                        pass
                elif d['status'] == 'finished':
                    progress_state['downloading'] = False

            # Background task to update progress
            async def update_progress_loop():
                last_percent = -1
                while progress_state['downloading']:
                    current_percent = progress_state['percent']
                    # Update every 2% change - callback handles rate limiting
                    if abs(current_percent - last_percent) >= 2:
                        try:
                            await progress_callback(current_percent)
                            last_percent = current_percent
                        except Exception as e:
                            logger.debug(f"Progress callback error: {e}")
                    await asyncio.sleep(0.3)  # Check every 0.3 seconds

            # Start progress updater if callback provided
            progress_task = None
            if progress_callback:
                progress_task = asyncio.create_task(update_progress_loop())

            # Get ffmpeg path from imageio-ffmpeg
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
                'progress_hooks': [progress_hook],
                # Use Android client to bypass 403 restrictions
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                # Anti-block options
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                'extractor_retries': 3,
                'nocheckcertificate': True,
            }

            logger.info("Downloading YouTube audio")

            # Run download in executor
            loop = asyncio.get_event_loop()
            video_id = await loop.run_in_executor(
                None,
                lambda: self._download_with_ydl(url, ydl_opts)
            )

            # Mark download as complete and wait for progress task
            progress_state['downloading'] = False
            if progress_task:
                try:
                    await asyncio.wait_for(progress_task, timeout=1.0)
                except asyncio.TimeoutError:
                    progress_task.cancel()

            # Find the downloaded file
            expected_filename = f"{self.temp_dir}/{video_id}_audio.mp3"
            if os.path.exists(expected_filename):
                return expected_filename

            # Fallback: look for any file with this video_id and .mp3
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
            # Get info first to know video ID
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id', 'youtube')

            # Then download
            ydl.download([url])

            return video_id
