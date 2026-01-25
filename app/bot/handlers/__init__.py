from aiogram import Router
from .common import router as common_router
from .youtube import router as youtube_router
from .tiktok import router as tiktok_router

# Create main router and include all sub-routers
router = Router()
router.include_router(common_router)
router.include_router(youtube_router)
router.include_router(tiktok_router)

__all__ = ['router']