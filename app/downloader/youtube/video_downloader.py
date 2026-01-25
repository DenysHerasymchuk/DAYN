import os
import logging
import asyncio
import yt_dlp
import imageio_ffmpeg
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class YouTubeVideoDownloader:
    """Download YouTube videos."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def download(self, url: str, quality: int = 360, progress_callback: Optional[Callable] = None) -> str:
        """Download YouTube video using yt-dlp with progress tracking."""
        try:
            # Shared progress state between threads
            progress_state = {'percent': 0, 'downloading': True}

            # Progress hook runs in the download thread
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0%').strip('%')
                    try:
                        progress_state['percent'] = float(percent_str)
                    except:
                        pass
                elif d['status'] == 'finished':
                    progress_state['downloading'] = False

            # Background task to update progress
            async def update_progress_loop():
                last_percent = -1
                while progress_state['downloading']:
                    current_percent = progress_state['percent']
                    # Only update if changed by at least 20% to reduce overhead
                    if abs(current_percent - last_percent) >= 20:
                        try:
                            await progress_callback(current_percent)
                            last_percent = current_percent
                        except Exception as e:
                            logger.debug(f"Progress callback error: {e}")
                    await asyncio.sleep(0.5)  # Check every 0.5 seconds

            # Start progress updater if callback provided
            progress_task = None
            if progress_callback:
                progress_task = asyncio.create_task(update_progress_loop())

            # Get ffmpeg path from imageio-ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            # Format selector - get best video up to quality + best audio
            format_selector = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'

            ydl_opts = {
                'format': format_selector,
                'outtmpl': f'{self.temp_dir}/%(id)s_{quality}p.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'ffmpeg_location': ffmpeg_path,
                'progress_hooks': [progress_hook],
            }

            logger.info(f"Downloading YouTube video at {quality}p")

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
            expected_filename = f"{self.temp_dir}/{video_id}_{quality}p.mp4"
            if os.path.exists(expected_filename):
                return expected_filename

            # Fallback: look for any file with this video_id
            for file in os.listdir(self.temp_dir):
                if video_id in file and file.endswith('.mp4'):
                    return f"{self.temp_dir}/{file}"

            raise Exception(f"Downloaded file not found for video {video_id}")

        except Exception as e:
            logger.error(f"YouTube download error: {e}")
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