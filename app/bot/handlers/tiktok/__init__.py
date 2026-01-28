from aiogram import Router

from app.downloader.tiktok import TikTokDownloader

# Shared downloader instance - must be created before importing sub-modules
tiktok_dl = TikTokDownloader()

from .callbacks import router as callbacks_router  # noqa: E402
from .photo_handler import router as photo_router  # noqa: E402
from .url_handler import router as url_router  # noqa: E402

router = Router()
router.include_router(url_router)
router.include_router(callbacks_router)
router.include_router(photo_router)
