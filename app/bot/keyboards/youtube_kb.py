from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.constants import CallbackData, Emojis


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown during download - cancel option."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{Emojis.CROSS} Cancel", callback_data=CallbackData.CANCEL)
    builder.adjust(1)
    return builder.as_markup()


def get_quality_keyboard_with_sizes(
        qualities_with_size: list,
        audio_exceeds_limit: bool = False,
        audio_size_str: str = ""
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    reversed_qualities = list(reversed(qualities_with_size))

    for height, _size_bytes, size_str, _estimated, exceeds_limit in reversed_qualities:
        link_indicator = f" {Emojis.LINK}" if exceeds_limit else ""
        display_text = f"{height}p - {size_str}{link_indicator}"
        builder.button(
            text=display_text,
            callback_data=CallbackData.quality(height)
        )

    num_qualities = len(reversed_qualities)

    audio_link_indicator = f" {Emojis.LINK}" if audio_exceeds_limit else ""
    builder.button(
        text=f"{Emojis.MUSIC} MP3 - {audio_size_str}{audio_link_indicator}",
        callback_data=CallbackData.FORMAT_AUDIO
    )

    # Adjust layout: qualities in pairs, audio alone on its own row
    row_pattern = [2] * (num_qualities // 2)
    if num_qualities % 2 == 1:
        row_pattern.append(1)
    row_pattern.append(1)

    builder.adjust(*row_pattern)
    return builder.as_markup()
