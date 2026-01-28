import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TikTokAudioExtractor:
    """Extract audio from TikTok videos/photos."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir

    async def download(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        """Download TikTok audio only using yt-dlp directly."""
        try:
            from .base_client import TikTokBaseClient
            from .ytdlp_client import TikTokVideoDownloader

            base_client = TikTokBaseClient(self.temp_dir)
            video_downloader = TikTokVideoDownloader(self.temp_dir)

            # Resolve URL and get info
            url = await base_client._resolve_url(url)
            username, video_id, content_type = base_client._extract_video_id(url)

            logger.info(f"TikTok audio download: user=@{username}, id={video_id}, type={content_type}")

            # For photo posts, we need to convert the URL to video format
            if content_type == "photo":
                # Convert photo URL to video URL for yt-dlp
                video_url = await base_client._convert_photo_to_video_url(url)
                logger.info(f"Converted photo URL to video URL for audio extraction: {video_url}")

                # Try to download audio from the video URL
                result = await video_downloader.download(video_url, video_id, True, progress_callback)
            else:
                # For video posts, use the original URL
                result = await video_downloader.download(url, video_id, True, progress_callback)

            if result:
                return result
            else:
                raise Exception("Failed to download audio via yt-dlp")

        except Exception as e:
            logger.error(f"TikTok audio error: {e}")
            # Try alternative method if yt-dlp fails
            logger.info("Trying alternative audio extraction method...")
            return await self._download_audio_alternative(url, progress_callback)

    async def _download_audio_alternative(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        """Alternative method to extract audio if yt-dlp fails."""
        try:
            import asyncio
            import os

            import imageio_ffmpeg

            from .ytdlp_client import TikTokVideoDownloader

            video_downloader = TikTokVideoDownloader(self.temp_dir)

            # Try to extract video first, then extract audio from it
            logger.info("Trying alternative: download video then extract audio...")

            # Download the video
            video_path = await video_downloader.download(url, "temp_video", False, progress_callback)

            if isinstance(video_path, list):
                raise Exception("Cannot extract audio from photos directly")

            # Extract audio using ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            video_id = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.temp_dir, f"{video_id}_audio.mp3")

            # Update progress for audio extraction
            if progress_callback:
                await progress_callback(80)

            # Run ffmpeg to extract audio
            process = await asyncio.create_subprocess_exec(
                ffmpeg_path,
                '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',
                audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            # Clean up video file
            if os.path.exists(video_path):
                os.remove(video_path)

            if progress_callback:
                await progress_callback(100)

            if os.path.exists(audio_path):
                logger.info(f"Audio extracted via alternative method: {audio_path}")
                return audio_path
            else:
                raise Exception("Alternative audio extraction failed")

        except Exception as e:
            logger.error(f"Alternative audio extraction error: {e}")
            raise Exception(f"Audio extraction failed: {str(e)}") from e
