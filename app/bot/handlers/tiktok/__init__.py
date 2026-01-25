from aiogram import Router
from app.downloader.tiktok import TikTokDownloader

# Shared downloader instance
tiktok_dl = TikTokDownloader()

from .url_handler import router as url_router
from .callbacks import router as callbacks_router
from .photo_handler import router as photo_router

router = Router()
router.include_router(url_router)
router.include_router(callbacks_router)
router.include_router(photo_router)