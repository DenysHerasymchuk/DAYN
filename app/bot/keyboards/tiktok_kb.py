from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_audio_button() -> InlineKeyboardMarkup:
    """Create audio extraction button for TikTok videos."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎵 Extract Audio", callback_data="tiktok_extract_audio")
    return builder.as_markup()
