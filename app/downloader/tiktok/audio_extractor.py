import asyncio
import logging
import os
from typing import Callable, Optional

import aiofiles.os
import imageio_ffmpeg

from app.config.constants import DownloadSettings, ProgressPercent

from .base_client import TikTokBaseClient
from .ytdlp_client import TikTokVideoDownloader

logger = logging.getLogger(__name__)


class TikTokAudioExtractor:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        self.base_client = TikTokBaseClient(temp_dir)
        self.video_downloader = TikTokVideoDownloader(temp_dir)

    async def download(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        try:
            resolved_url = await self.base_client._resolve_url(url)
            username, video_id, content_type = self.base_client._extract_video_id(resolved_url)

            logger.info(f"TikTok audio download: user=@{username}, id={video_id}, type={content_type}")

            if content_type == "photo":
                video_url = await self.base_client._convert_photo_to_video_url(resolved_url)
                logger.info(f"Converted photo URL to video URL for audio extraction: {video_url}")
                result = await self.video_downloader.download(video_url, video_id, True, progress_callback)
            else:
                result = await self.video_downloader.download(resolved_url, video_id, True, progress_callback)

            if result:
                return result
            else:
                raise Exception("Failed to download audio via yt-dlp")

        except Exception as e:
            logger.error(f"TikTok audio error: {e}")
            logger.info("Trying alternative audio extraction method...")
            return await self._download_audio_alternative(url, progress_callback)

    async def _download_audio_alternative(self, url: str, progress_callback: Optional[Callable] = None) -> str:
        try:
            logger.info("Trying alternative: download video then extract audio...")

            video_path = await self.video_downloader.download(url, "temp_video", False, progress_callback)

            if isinstance(video_path, list):
                raise Exception("Cannot extract audio from photos directly")

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            video_id = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.temp_dir, f"{video_id}_audio.mp3")

            if progress_callback:
                await progress_callback(ProgressPercent.AUDIO_EXTRACTION_START)

            process = await asyncio.create_subprocess_exec(
                ffmpeg_path,
                '-i', video_path,
                '-vn',
                '-acodec', DownloadSettings.AUDIO_CODEC,
                '-ab', DownloadSettings.AUDIO_BITRATE,
                '-y',
                audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg failed with code {process.returncode}: {stderr.decode()}")
                raise Exception(f"FFmpeg extraction failed with code {process.returncode}")

            if await aiofiles.os.path.exists(video_path):
                await aiofiles.os.remove(video_path)

            if progress_callback:
                await progress_callback(ProgressPercent.COMPLETE)

            if await aiofiles.os.path.exists(audio_path):
                logger.info(f"Audio extracted via alternative method: {audio_path}")
                return audio_path
            else:
                raise Exception("Alternative audio extraction failed - file not created")

        except Exception as e:
            logger.error(f"Alternative audio extraction error: {e}")
            raise Exception(f"Audio extraction failed: {str(e)}") from e
