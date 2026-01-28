from aiogram import Router

from .cancel import router as cancel_router
from .start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(cancel_router)
