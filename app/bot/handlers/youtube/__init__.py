from aiogram import Router

from app.config.settings import settings
from app.downloader.youtube import YouTubeDownloader

# Shared downloader instance - must be created before importing sub-modules
youtube_dl = YouTubeDownloader(
    max_file_size=settings.MAX_FILE_SIZE
)

from .callbacks import router as callbacks_router  # noqa: E402
from .url_handler import router as url_router  # noqa: E402

router = Router()
router.include_router(url_router)
router.include_router(callbacks_router)
