from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.constants import Emojis


def get_quality_keyboard_with_sizes(
        qualities_with_size: list,
        audio_under_limit: bool = True,
        audio_size_str: str = ""
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    reversed_qualities = list(reversed(qualities_with_size))

    for height, _size_bytes, size_str, _estimated in reversed_qualities:
        display_text = f"{height}p - {size_str}"
        builder.button(
            text=display_text,
            callback_data=f"quality_{height}"
        )

    num_qualities = len(reversed_qualities)

    if audio_under_limit:
        builder.button(text=f"{Emojis.MUSIC} MP3 - {audio_size_str}", callback_data="format_audio")

    # Adjust layout
    row_pattern = [2] * (num_qualities // 2)
    if num_qualities % 2 == 1:
        row_pattern.append(1)
    if audio_under_limit:
        row_pattern.append(1)

    builder.adjust(*row_pattern)
    return builder.as_markup()
