import logging
import os

from .audio_extractor import TikTokAudioExtractor
from .base_client import TikTokBaseClient
from .musicaldown import TikTokPhotoDownloader
from .ytdlp_client import TikTokVideoDownloader

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
        """Get TikTok video/photo info including estimated file size."""
        base_info = await self.base.get_video_info(url)

        # For videos, get size estimate from yt-dlp
        if base_info.get('content_type') != 'photo':
            try:
                ytdlp_info = await self.videos.get_info(url)
                base_info['estimated_size'] = ytdlp_info.get('filesize', 0)
                base_info['size_is_estimated'] = ytdlp_info.get('is_estimated', True)
                if ytdlp_info.get('duration'):
                    base_info['duration'] = ytdlp_info['duration']
            except Exception as e:
                logger.warning(f"Could not get size estimate: {e}")
                base_info['estimated_size'] = 0
                base_info['size_is_estimated'] = True

        return base_info

    async def download_video(self, url: str, progress_callback=None, photo_progress_callback=None):
        """Download TikTok video or photos.

        Args:
            url: TikTok URL
            progress_callback: Callback(percent: float) for video progress
            photo_progress_callback: Callback(current: int, total: int) for photo progress
        """
        info = await self.get_video_info(url)

        if info.get('content_type') == "photo":
            return await self.photos.download(
                url,
                info.get('video_id'),
                progress_callback,
                photo_progress_callback
            )
        else:
            return await self.videos.download(url, info.get('video_id'), False, progress_callback)

    async def download_audio(self, url: str, progress_callback=None):
        """Download TikTok audio only."""
        return await self.audio.download(url, progress_callback)
