from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.constants import CallbackData, Emojis


def get_audio_button() -> InlineKeyboardMarkup:
    """Keyboard shown after video/photo is sent - extract audio option."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{Emojis.MUSIC} Extract Audio", callback_data=CallbackData.TIKTOK_EXTRACT_AUDIO)
    builder.adjust(1)
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown during download - cancel option."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{Emojis.CROSS} Cancel", callback_data=CallbackData.CANCEL)
    builder.adjust(1)
    return builder.as_markup()
