import re
import logging
import aiohttp
from typing import Dict

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


class TikTokBaseClient:
    """Base TikTok client for URL handling and info extraction."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir

    def _extract_video_id(self, url: str) -> tuple:
        """Extract username, video_id, and content_type from TikTok URL."""
        username_pattern = r"@([A-Za-z0-9_.]+)"
        content_type_pattern = r"/(video|photo)/(\d+)"

        username_match = re.search(username_pattern, url)
        username = username_match.group(1) if username_match else "unknown"

        content_type_match = re.search(content_type_pattern, url)
        if content_type_match:
            content_type = content_type_match.group(1)
            video_id = content_type_match.group(2)
        else:
            # Try to extract just the ID from the URL
            id_match = re.search(r'/(\d{15,})/?', url)
            video_id = id_match.group(1) if id_match else "unknown"
            content_type = "video"

        return username, video_id, content_type

    async def _resolve_url(self, url: str) -> str:
        """Resolve shortened URLs to full URLs."""
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, allow_redirects=True) as response:
                    return str(response.url)
        return url

    async def _convert_photo_to_video_url(self, photo_url: str) -> str:
        """Convert TikTok photo URL to video URL."""
        try:
            # Photo URL: https://www.tiktok.com/@username/photo/1234567890
            # Convert to: https://www.tiktok.com/@username/video/1234567890
            if '/photo/' in photo_url:
                video_url = photo_url.replace('/photo/', '/video/')
                logger.info(f"Converted photo URL to video URL: {video_url}")
                return video_url
            return photo_url
        except Exception as e:
            logger.error(f"Failed to convert photo URL: {e}")
            return photo_url

    async def get_video_info(self, url: str) -> Dict:
        """Get TikTok video/photo info."""
        try:
            url = await self._resolve_url(url)
            username, video_id, content_type = self._extract_video_id(url)

            is_slideshow = content_type == "photo"

            title = f"TikTok {'Photos' if is_slideshow else 'Video'} by @{username}"

            return {
                'title': title[:100],
                'author': username,
                'duration': 'Unknown',
                'video_id': video_id,
                'thumbnail': None,
                'is_slideshow': is_slideshow,
                'num_images': 0,  # Will be determined during download
                'image_urls': [],
                'has_audio': True,
                'content_type': content_type,
                'resolved_url': url,
                'video_url': await self._convert_photo_to_video_url(url) if is_slideshow else url,
            }
        except Exception as e:
            logger.error(f"TikTok info error: {e}")
            raise