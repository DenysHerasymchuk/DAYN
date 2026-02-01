import logging
import os
import re
from typing import Callable, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


class TikTokPhotoDownloader:
    """Download TikTok photos using musicaldown.com API."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def download(
        self,
        url: str,
        video_id: str,
        progress_callback: Optional[Callable] = None,
        photo_progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Download PHOTOS using musicaldown.com API.

        Args:
            url: TikTok URL
            video_id: Video ID for filename
            progress_callback: Optional callback(percent: float) for percentage progress
            photo_progress_callback: Optional callback(current: int, total: int) for photo count progress
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://musicaldown.com',
            'Referer': 'https://musicaldown.com/en?ref=more',
        }

        async with aiohttp.ClientSession() as session:
            # Get the page to extract tokens
            async with session.get("https://musicaldown.com/en", headers=headers) as response:
                html = await response.text()

            # Extract tokens using regex
            token_a_match = re.search(r'<input\s+name="([^"]+)"[^>]*id="link_url"', html)
            if not token_a_match:
                token_a_match = re.search(r'name="([^"]+)"[^>]*id="link_url"', html)

            token_b_match = re.search(r'<input\s+name="([^"]+)"\s+type="hidden"\s+value="([^"]*)"', html)

            if not token_a_match:
                raise Exception("Could not find token_a")

            token_a = token_a_match.group(1)
            token_b = token_b_match.group(1) if token_b_match else None
            token_b_value = token_b_match.group(2) if token_b_match else None

            data = {token_a: url, 'verify': '1'}
            if token_b and token_b_value:
                data[token_b] = token_b_value

            # Submit the form
            async with session.post(
                    'https://musicaldown.com/download',
                    headers=headers,
                    data=data
            ) as response:
                result_html = await response.text()

            # Extract photo URLs
            photo_urls = re.findall(r'<div class="card-image">\s*<img[^>]+src="([^"]+)"', result_html)

            if not photo_urls:
                # Try alternative pattern
                photo_urls = re.findall(r'class="card-image"[^>]*>.*?<img[^>]+src="([^"]+)"', result_html, re.DOTALL)

            if not photo_urls:
                raise Exception("No photo URLs found")

            logger.info(f"Found {len(photo_urls)} photos")

            # Download all photos
            downloaded_files = []
            total = len(photo_urls)

            for i, photo_url in enumerate(photo_urls):
                current = i + 1

                # Use photo count callback if provided, otherwise use percent callback
                if photo_progress_callback:
                    await photo_progress_callback(current, total)
                elif progress_callback:
                    percent = (current / total) * 100
                    await progress_callback(percent)

                file_path = os.path.join(self.temp_dir, f"{video_id}_photo_{current}.jpeg")

                async with session.get(photo_url, headers=HEADERS) as img_response:
                    if img_response.status == 200:
                        content = await img_response.read()
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        downloaded_files.append(file_path)
                        logger.debug(f"Downloaded photo {current}/{total}")

            return downloaded_files
