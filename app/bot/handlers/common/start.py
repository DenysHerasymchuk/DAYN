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

    await message.answer(
        Messages.START.format(
            video=Emojis.VIDEO,
            light=Emojis.LIGHT,
            gear=Emojis.GEAR,
            status=f"📦 Max file size: {max_size_mb:.0f}MB"
        ),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command."""
    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)

    await message.answer(
        Messages.HELP.format(
            help=Emojis.HELP,
            light=Emojis.LIGHT,
            limit_text=f"Only qualities under {max_size_mb:.0f}MB are shown"
        ),
        parse_mode="HTML"
    )