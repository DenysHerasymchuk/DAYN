import logging
from typing import Optional

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from .progress import create_video_progress_bar

logger = logging.getLogger(__name__)


async def safe_edit_message(
    message: Message,
    text: Optional[str] = None,
    parse_mode: Optional[str] = "HTML",
    try_caption_first: bool = True,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    # If no text provided, only edit reply_markup (e.g., to clear buttons)
    if text is None:
        try:
            await message.edit_reply_markup(reply_markup=reply_markup)
            return True
        except Exception as e:
            logger.debug(f"edit_reply_markup failed: {e}")
            return False

    if try_caption_first:
        try:
            await message.edit_caption(caption=text, parse_mode=parse_mode, reply_markup=reply_markup)
            return True
        except Exception as e:
            logger.debug(f"edit_caption failed: {e}")

    try:
        await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        return True
    except Exception as e:
        logger.debug(f"edit_text failed: {e}")

    return False


async def safe_send_error(target: CallbackQuery | Message, error_message: str) -> None:
    """Send error message, trying edit first then fallback to reply/answer.

    Args:
        target: Either a CallbackQuery or Message to send error to
        error_message: The error message to display
    """
    if isinstance(target, CallbackQuery):
        message = target.message
    else:
        message = target

    success = await safe_edit_message(
        message,
        error_message,
        parse_mode=None,
        try_caption_first=True
    )

    if not success:
        try:
            await message.answer(error_message)
        except Exception as e:
            logger.warning(f"All message methods failed: {e}")


async def update_download_progress(
    message: Message,
    percent: float,
    status_text: str
) -> None:
    progress_bar = create_video_progress_bar(percent)
    full_text = f"{status_text}\n{progress_bar}"
    await safe_edit_message(message, full_text, parse_mode="HTML")


def create_progress_callback(message: Message, status_text: str):
    async def callback(percent: float) -> None:
        await update_download_progress(message, percent, status_text)
    return callback


async def safe_delete_message(message: Message) -> bool:
    try:
        await message.delete()
        return True
    except Exception as e:
        logger.debug(f"Message delete failed: {e}")
        return False
