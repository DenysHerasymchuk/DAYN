import logging
from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from .progress import create_video_progress_bar

logger = logging.getLogger(__name__)


async def _is_cancelled(state: Optional[FSMContext]) -> bool:
    """Check if download was cancelled. Returns False if no state provided."""
    if state is None:
        return False
    data = await state.get_data()
    return data.get('cancelled', False)


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
    status_text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    progress_bar = create_video_progress_bar(percent)
    full_text = f"{status_text} {int(percent)}%\n{progress_bar}"
    await safe_edit_message(message, full_text, parse_mode="HTML", reply_markup=reply_markup)


def create_progress_callback(
    message: Message,
    status_text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    state: Optional[FSMContext] = None
):
    """Create a progress callback for percentage-based progress.

    Args:
        message: Message to update with progress
        status_text: Text to show before progress bar
        reply_markup: Optional keyboard to show
        state: Optional FSMContext to check for cancellation
    """
    last_percent = [-1]  # Mutable to track last update
    stopped = [False]  # Flag to stop updates after cancellation

    async def callback(percent: float) -> None:
        if stopped[0]:
            return

        # Check if cancelled
        if await _is_cancelled(state):
            stopped[0] = True
            return

        # Update every 5% to reduce API calls but still be responsive
        if abs(percent - last_percent[0]) >= 5 or percent >= 100:
            await update_download_progress(message, percent, status_text, reply_markup)
            last_percent[0] = percent

    return callback


async def update_photo_progress(
    message: Message,
    current: int,
    total: int,
    status_text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    """Update progress for photo downloads showing count."""
    percent = (current / total) * 100 if total > 0 else 0
    progress_bar = create_video_progress_bar(percent)
    full_text = f"{status_text} ({current}/{total})\n{progress_bar}"
    await safe_edit_message(message, full_text, parse_mode="HTML", reply_markup=reply_markup)


def create_photo_progress_callback(
    message: Message,
    status_text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    state: Optional[FSMContext] = None
):
    """Create a progress callback for photo count progress.

    Args:
        message: Message to update with progress
        status_text: Text to show before progress bar
        reply_markup: Optional keyboard to show
        state: Optional FSMContext to check for cancellation
    """
    stopped = [False]  # Flag to stop updates after cancellation

    async def callback(current: int, total: int) -> None:
        if stopped[0]:
            return

        # Check if cancelled
        if await _is_cancelled(state):
            stopped[0] = True
            return

        await update_photo_progress(message, current, total, status_text, reply_markup)

    return callback


async def safe_delete_message(message: Message) -> bool:
    try:
        await message.delete()
        return True
    except Exception as e:
        logger.debug(f"Message delete failed: {e}")
        return False
