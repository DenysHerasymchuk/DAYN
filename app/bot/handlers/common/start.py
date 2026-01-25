from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from app.config.settings import settings
from app.config.constants import Emojis, Messages

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    """Handle /start command."""
    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
    premium_status = "✅ Premium (2GB limit)" if settings.PREMIUM else "📦 Regular (50MB limit)"

    await message.answer(
        Messages.START.format(
            video=Emojis.VIDEO,
            light=Emojis.LIGHT,
            gear=Emojis.GEAR,
            status=premium_status
        ),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command."""
    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
    limit_text = f"Only qualities under {max_size_mb:.0f}MB are shown" if not settings.PREMIUM else f"Can download files up to {max_size_mb:.0f}MB"

    await message.answer(
        Messages.HELP.format(
            help=Emojis.HELP,
            light=Emojis.LIGHT,
            limit_text=limit_text
        ),
        parse_mode="HTML"
    )