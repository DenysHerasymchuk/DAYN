import logging
import time

import aiofiles.os
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from app.bot.utils.logger import user_logger
from app.bot.utils.message_helpers import (
    create_progress_callback,
    safe_delete_message,
    safe_edit_message,
    safe_send_error,
)
from app.bot.utils.metrics import (
    record_download,
    record_error,
    record_processing_time,
    record_request,
)
from app.config.constants import BYTES_PER_MB, CallbackData, Emojis, TelegramLimits, Timeouts
from app.config.settings import settings

from . import tiktok_dl

logger = logging.getLogger(__name__)
router = Router()

HANDLER_NAME = "tiktok_extract_audio_callback"


async def validate_tiktok_session(callback: CallbackQuery, state: FSMContext) -> dict | None:
    """Validate TikTok session and return data if valid."""
    data = await state.get_data()
    url = data.get('url')
    timestamp = data.get('timestamp', 0)
    current_time = time.time()

    if current_time - timestamp > Timeouts.SESSION_EXPIRY_SECONDS:
        await state.clear()
        user_logger.log_user_action(
            HANDLER_NAME,
            callback.from_user.id,
            "Session expired",
            f"Age: {current_time - timestamp:.0f}s"
        )
        await callback.answer(
            f"{Emojis.HOURGLASS} Session expired. Please send the TikTok URL again.",
            show_alert=True
        )
        await safe_edit_message(callback.message, reply_markup=None)
        return None

    if not url:
        user_logger.log_user_error(HANDLER_NAME, callback.from_user.id, "No URL in state")
        await callback.message.reply(
            f"{Emojis.WARNING} Please send the TikTok URL again for audio extraction."
        )
        await safe_edit_message(callback.message, reply_markup=None)
        await state.clear()
        return None

    return data


async def check_tiktok_file_size(file_path: str, user_id: int, status_msg) -> float | None:
    """Check if file size is within limits. Returns file_size_mb if OK, None if too large."""
    file_size = await aiofiles.os.path.getsize(file_path)
    file_size_mb = file_size / BYTES_PER_MB
    max_size_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB

    if file_size > settings.MAX_FILE_SIZE:
        user_logger.log_user_error(
            HANDLER_NAME,
            user_id,
            f"Audio too large: {file_size_mb:.1f}MB (limit: {max_size_mb:.0f}MB)"
        )
        await safe_edit_message(
            status_msg,
            f"{Emojis.CROSS} Audio too large ({file_size_mb:.1f} MB)\n"
            f"{Emojis.SIZE} Limit: {max_size_mb:.0f} MB"
        )
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        return None

    return file_size_mb


async def send_tiktok_audio(
    callback: CallbackQuery,
    file_path: str,
    video_info: dict
) -> None:
    """Send TikTok audio to user."""
    bot_me = await callback.bot.get_me()
    bot_username = f"@{bot_me.username}" if bot_me.username else ""

    username = video_info.get('author', 'Unknown')
    author_link = f'<a href="https://www.tiktok.com/@{username}">@{username}</a>'

    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=FSInputFile(file_path),
        title=video_info.get('title', f'TikTok Audio - @{username}')[:TelegramLimits.MAX_TITLE_LENGTH],
        performer=username[:TelegramLimits.MAX_TITLE_LENGTH],
        caption=(
            f"{Emojis.MUSIC} TikTok Audio\n"
            f"{Emojis.USER} {author_link}\n\n"
            f"Downloaded via:\n{bot_username}"
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data == CallbackData.TIKTOK_EXTRACT_AUDIO)
async def tiktok_extract_audio_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    start_time = time.time()

    data = await validate_tiktok_session(callback, state)
    if not data:
        return

    url = data.get('url')
    video_info = data.get('video_info', {})

    try:
        user_logger.log_user_action(
            HANDLER_NAME,
            user_id,
            "Audio extraction started",
            f"Author: @{video_info.get('author', 'unknown')}"
        )

        status_msg = await callback.message.reply(f"{Emojis.MUSIC} Extracting audio...")
        progress_callback = create_progress_callback(
            status_msg,
            f"{Emojis.MUSIC} Extracting audio..."
        )

        user_logger.log_download_start("tiktok_audio", user_id, url)

        file_path = await tiktok_dl.download_audio(url, progress_callback=progress_callback)

        file_size_mb = await check_tiktok_file_size(file_path, user_id, status_msg)
        if file_size_mb is None:
            return

        file_size = await aiofiles.os.path.getsize(file_path)

        await send_tiktok_audio(callback, file_path, video_info)

        user_logger.log_download_complete("tiktok_audio", user_id, file_size_mb, success=True)
        user_logger.log_user_action(
            HANDLER_NAME,
            user_id,
            "Audio extracted and sent",
            f"Size: {file_size_mb:.1f}MB"
        )

        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)

        await safe_delete_message(status_msg)
        await safe_edit_message(callback.message, reply_markup=None)

        duration = time.time() - start_time
        record_download("tiktok", "audio", True, duration, file_size)
        record_request(HANDLER_NAME, True)
        record_processing_time(HANDLER_NAME, duration)

    except Exception as e:
        user_logger.log_user_error(
            HANDLER_NAME,
            user_id,
            f"TikTok audio extraction error: {str(e)}"
        )

        duration = time.time() - start_time
        record_error("tiktok", type(e).__name__)
        record_request(HANDLER_NAME, False)
        record_processing_time(HANDLER_NAME, duration)

        await safe_send_error(callback, f"{Emojis.CROSS} Audio extraction failed. Please try again.")
        await state.clear()
