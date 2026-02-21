import asyncio
import logging
from typing import Dict

import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeInfoExtractor:
    """Extract video information from YouTube."""

    def __init__(self, max_file_size: int = 50 * 1024 * 1024):
        self.max_file_size = max_file_size

    async def get_video_info(self, url: str) -> Dict:
        """Get YouTube video info using yt-dlp."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # Anti-block options
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                'socket_timeout': 30,
                'nocheckcertificate': True,
            }

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self._extract_info(url, ydl_opts)
            )

            # Extract available formats/qualities with size estimation
            quality_info = {}  # {height: {'video_size': bytes, 'audio_size': bytes}}

            if 'formats' in info:
                # First, find the best audio size
                best_audio_size = 0
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        # This is an audio-only format
                        filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                        if filesize and filesize > best_audio_size:
                            best_audio_size = filesize

                # If no audio size found, estimate it
                if best_audio_size == 0:
                    duration = info.get('duration', 0)
                    minutes = duration / 60 if duration else 5
                    best_audio_size = int(minutes * 3 * 1024 * 1024)  # 3MB per minute

                logger.info(f"Audio stream size: {best_audio_size / (1024 * 1024):.1f}MB")

                # Now get video sizes
                for fmt in info['formats']:
                    height = fmt.get('height')

                    # Only consider video formats (may not have audio)
                    if fmt.get('vcodec') != 'none' and height:
                        # Common qualities
                        if height in [144, 240, 360, 480, 720, 1080, 1440, 2160]:
                            video_size = fmt.get('filesize') or fmt.get('filesize_approx')

                            if height not in quality_info:
                                quality_info[height] = {'video_size': video_size, 'audio_size': best_audio_size}
                            elif video_size is not None:
                                # Keep track of smallest video size for each quality
                                existing = quality_info[height]['video_size']
                                if existing is None or video_size < existing:
                                    quality_info[height] = {'video_size': video_size, 'audio_size': best_audio_size}

            # Get duration for estimation
            duration = info.get('duration', 0)

            # Calculate sizes for all qualities (no size filtering — all shown)
            qualities_with_size = []

            for height, size_info in quality_info.items():
                video_size = size_info['video_size']
                audio_size = size_info['audio_size']

                # Calculate total size (video + audio)
                if video_size is None:
                    estimated_video_size = self._estimate_file_size(height, duration)
                    total_size = estimated_video_size + audio_size
                    size_mb = total_size / (1024 * 1024)
                    exceeds_limit = total_size > self.max_file_size
                    qualities_with_size.append((height, total_size, f"~{size_mb:.1f} MB", True, exceeds_limit))
                else:
                    total_size = video_size + audio_size
                    size_mb = total_size / (1024 * 1024)
                    exceeds_limit = total_size > self.max_file_size
                    qualities_with_size.append((height, total_size, f"{size_mb:.1f} MB", False, exceeds_limit))

            # Sort by quality (high to low)
            qualities_with_size.sort(key=lambda x: x[0], reverse=True)

            # Calculate audio-only size
            audio_only_size = best_audio_size
            audio_only_size_mb = audio_only_size / (1024 * 1024)
            audio_exceeds_limit = audio_only_size > self.max_file_size

            logger.info(f"Found {len(qualities_with_size)} qualities (limit {self.max_file_size / (1024 * 1024):.0f}MB)")

            return {
                'title': info.get('title', 'YouTube Video')[:100],
                'author': info.get('uploader', 'Unknown'),
                'duration': self._format_duration(info.get('duration', 0)),
                'qualities_with_size': qualities_with_size,  # [(height, size_bytes, size_str, estimated, exceeds_limit)]
                'audio_size': audio_only_size,
                'audio_size_str': f"{audio_only_size_mb:.1f} MB",
                'audio_exceeds_limit': audio_exceeds_limit,
                'video_id': info.get('id', 'unknown'),
                'thumbnail': info.get('thumbnail', None)
            }
        except Exception as e:
            logger.error(f"YouTube info error: {e}")
            raise

    def _extract_info(self, url: str, ydl_opts: dict) -> dict:
        """Helper to extract info synchronously."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _format_duration(self, seconds: int) -> str:
        """Format seconds to readable time."""
        if not seconds:
            return 'Unknown'

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _estimate_file_size(self, height: int, duration: int) -> int:
        """Estimate VIDEO ONLY file size based on quality and duration."""
        if duration == 0:
            duration = 300  # Assume 5 minutes if unknown

        minutes = duration / 60

        # Conservative estimates for VIDEO ONLY (audio added separately)
        video_mb_per_minute = {
            144: 1,
            240: 2,
            360: 5,
            480: 8,
            720: 15,
            1080: 25,
            1440: 40,
            2160: 60
        }

        mb_per_min = video_mb_per_minute.get(height, 5)
        estimated_mb = mb_per_min * minutes

        return int(estimated_mb * 1024 * 1024)  # Convert to bytes
