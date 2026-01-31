from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.constants import CallbackData, Emojis


def get_audio_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{Emojis.MUSIC} Extract Audio", callback_data=CallbackData.TIKTOK_EXTRACT_AUDIO)
    return builder.as_markup()
