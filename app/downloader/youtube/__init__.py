import os
import logging
from .info_extractor import YouTubeInfoExtractor
from .video_downloader import YouTubeVideoDownloader
from .audio_downloader import YouTubeAudioDownloader

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Facade that combines all YouTube downloader components."""

    def __init__(self, temp_dir: str = "temp", max_file_size: int = 50 * 1024 * 1024, is_premium: bool = False):
        self.temp_dir = temp_dir
        self.max_file_size = max_file_size
        self.is_premium = is_premium
        os.makedirs(temp_dir, exist_ok=True)
        self.info_extractor = YouTubeInfoExtractor(max_file_size, is_premium)
        self.video_downloader = YouTubeVideoDownloader(temp_dir)
        self.audio_downloader = YouTubeAudioDownloader(temp_dir)

    async def get_video_info(self, url: str):
        """Get YouTube video info."""
        return await self.info_extractor.get_video_info(url)

    async def download_video(self, url: str, quality: int = 360, progress_callback=None):
        """Download YouTube video."""
        return await self.video_downloader.download(url, quality, progress_callback)

    async def download_audio(self, url: str, progress_callback=None):
        """Download YouTube audio."""
        return await self.audio_downloader.download(url, progress_callback)