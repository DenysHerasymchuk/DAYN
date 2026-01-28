import asyncio
import logging
import os
from typing import Callable, Optional

import imageio_ffmpeg
import yt_dlp

logger = logging.getLogger(__name__)


class TikTokVideoDownloader:
    """Download TikTok videos using yt-dlp."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def download(self, url: str, video_id: str, extract_audio: bool = False,
                       progress_callback: Optional[Callable] = None) -> str:
        """Download TikTok video or audio using yt-dlp."""
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

            # Common anti-block options
            common_opts = {
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

            # yt-dlp options
            if extract_audio:
                # Download audio only
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
                    'progress_hooks': [progress_hook],
                    **common_opts,
                }
            else:
                # Download video
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(self.temp_dir, '%(id)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': ffmpeg_path,
                    'progress_hooks': [progress_hook],
                    **common_opts,
                }

            logger.info(f"Downloading TikTok {'audio' if extract_audio else 'video'} using yt-dlp: {url}")

            # Run download in executor
            loop = asyncio.get_event_loop()

            def download_with_ydlp():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Get info first to know video ID
                    info = ydl.extract_info(url, download=False)
                    video_id_from_info = info.get('id', 'tiktok')

                    # Then download
                    ydl.download([url])
                    return video_id_from_info, info.get('extractor', 'tiktok')

            downloaded_id, extractor = await loop.run_in_executor(None, download_with_ydlp)

            # Mark download as complete and wait for progress task
            progress_state['downloading'] = False
            if progress_task:
                try:
                    await asyncio.wait_for(progress_task, timeout=1.0)
                except asyncio.TimeoutError:
                    progress_task.cancel()

            # Find the downloaded file
            if extract_audio:
                # Look for audio files
                for file in os.listdir(self.temp_dir):
                    if downloaded_id in file and file.endswith('.mp3'):
                        file_path = os.path.join(self.temp_dir, file)
                        logger.info(f"Downloaded TikTok audio: {file_path}")
                        return file_path

                # Also check for other audio extensions
                audio_extensions = ['.m4a', '.aac', '.opus', '.flac', '.wav']
                for ext in audio_extensions:
                    for file in os.listdir(self.temp_dir):
                        if downloaded_id in file and file.endswith(ext):
                            file_path = os.path.join(self.temp_dir, file)
                            logger.info(f"Downloaded TikTok audio ({ext}): {file_path}")
                            return file_path
            else:
                # Look for video files
                for file in os.listdir(self.temp_dir):
                    if downloaded_id in file and (
                            file.endswith('.mp4') or file.endswith('.mkv') or file.endswith('.webm')):
                        file_path = os.path.join(self.temp_dir, file)

                        # If not mp4, convert to mp4
                        if not file.endswith('.mp4'):
                            mp4_path = os.path.join(self.temp_dir, f"{downloaded_id}.mp4")
                            await self._convert_to_mp4(file_path, mp4_path)
                            os.remove(file_path)
                            file_path = mp4_path

                        logger.info(f"Downloaded TikTok video: {file_path}")
                        return file_path

            raise Exception("Downloaded file not found for TikTok")

        except Exception as e:
            logger.error(f"yt-dlp TikTok download error: {e}")
            raise

    async def _convert_to_mp4(self, input_path: str, output_path: str):
        """Convert video to mp4 format using ffmpeg."""
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            process = await asyncio.create_subprocess_exec(
                ffmpeg_path,
                '-i', input_path,
                '-c', 'copy',  # Copy streams without re-encoding
                '-y',
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Conversion failed")
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            raise
