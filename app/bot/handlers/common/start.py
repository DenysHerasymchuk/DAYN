from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config.constants import BYTES_PER_MB, Emojis, Messages
from app.config.settings import settings

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    max_size_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB

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
    max_size_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB

    await message.answer(
        Messages.HELP.format(
            help=Emojis.HELP,
            light=Emojis.LIGHT,
            limit_text=f"Only qualities under {max_size_mb:.0f}MB are shown"
        ),
        parse_mode="HTML"
    )
