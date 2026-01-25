import os
import logging
from .base_client import TikTokBaseClient
from .musicaldown import TikTokPhotoDownloader
from .ytdlp_client import TikTokVideoDownloader
from .audio_extractor import TikTokAudioExtractor

logger = logging.getLogger(__name__)


class TikTokDownloader:
    """Facade that combines all TikTok downloader components."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        self.base = TikTokBaseClient(temp_dir)
        self.photos = TikTokPhotoDownloader(temp_dir)
        self.videos = TikTokVideoDownloader(temp_dir)
        self.audio = TikTokAudioExtractor(temp_dir)

    async def get_video_info(self, url: str):
        """Get TikTok video/photo info."""
        return await self.base.get_video_info(url)

    async def download_video(self, url: str, progress_callback=None):
        """Download TikTok video or photos."""
        info = await self.get_video_info(url)

        if info.get('content_type') == "photo":
            return await self.photos.download(url, info.get('video_id'), progress_callback)
        else:
            return await self.videos.download(url, info.get('video_id'), False, progress_callback)

    async def download_audio(self, url: str, progress_callback=None):
        """Download TikTok audio only."""
        return await self.audio.download(url, progress_callback)