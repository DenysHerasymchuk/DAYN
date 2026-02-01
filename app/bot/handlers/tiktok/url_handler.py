import asyncio
import logging
import time

import aiofiles.os
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from app.bot.keyboards.tiktok_kb import get_audio_button, get_cancel_keyboard
from app.bot.states.download_states import TikTokState
from app.bot.utils.logger import user_logger
from app.bot.utils.message_helpers import (
    create_photo_progress_callback,
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
from app.bot.utils.validators import is_tiktok_url
from app.config.constants import BYTES_PER_MB, Emojis
from app.config.settings import settings
from app.core.file_manager import file_manager

from . import tiktok_dl
from ..common.cancel import is_cancelled
from .photo_handler import handle_single_photo, send_tiktok_photos

logger = logging.getLogger(__name__)
router = Router()

HANDLER_NAME = "tiktok_url_handler"


def tiktok_url_filter(message: Message) -> bool:
    """Filter for TikTok URLs only."""
    return bool(message.text and is_tiktok_url(message.text.strip()))


async def cleanup_files(file_paths: list, user_id: int | None = None) -> None:
    """Clean up files using file manager with user logging."""
    if not file_paths:
        return

    if user_id:
        user_logger.log_user_action(
            f"{HANDLER_NAME}.cleanup_files",
            user_id,
            "Cleaning up temporary files",
            f"Files: {len(file_paths)}"
        )

    deleted_count = await file_manager.cleanup_files(file_paths)

    if user_id and deleted_count > 0:
        user_logger.log_user_action(
            f"{HANDLER_NAME}.cleanup_files",
            user_id,
            "Files cleaned up",
            f"Deleted: {deleted_count}/{len(file_paths)} files"
        )


async def calculate_content_size(content) -> int:
    """Calculate total size of downloaded content."""
    if isinstance(content, list):
        total = 0
        for f in content:
            if await aiofiles.os.path.exists(f):
                total += await aiofiles.os.path.getsize(f)
        return total
    else:
        if await aiofiles.os.path.exists(content):
            return await aiofiles.os.path.getsize(content)
        return 0


async def check_video_size(file_path: str, user_id: int, status_msg: Message) -> float | None:
    """Check if video file size is within limits. Returns size_mb if OK, None if too large."""
    file_size = await aiofiles.os.path.getsize(file_path)
    file_size_mb = file_size / BYTES_PER_MB
    max_size_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB

    if file_size > settings.MAX_FILE_SIZE:
        user_logger.log_user_error(
            HANDLER_NAME,
            user_id,
            f"File too large: {file_size_mb:.1f}MB (limit: {max_size_mb:.0f}MB)"
        )
        await safe_edit_message(
            status_msg,
            f"{Emojis.CROSS} Video too large ({file_size_mb:.1f} MB)\n"
            f"{Emojis.SIZE} Limit: {max_size_mb:.0f} MB"
        )
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        return None

    return file_size_mb


async def send_tiktok_video(
    message: Message,
    file_path: str,
    file_size_mb: float,
    author_link: str,
    bot_username: str,
    state: FSMContext
) -> None:
    """Send TikTok video to user."""
    video_msg = await message.reply_video(
        video=FSInputFile(file_path),
        caption=(
            f"{Emojis.VIDEO} TikTok Video\n"
            f"{Emojis.USER} {author_link}\n"
            f"{Emojis.SIZE} {file_size_mb:.1f} MB\n\n"
            f"Downloaded via:\n{bot_username}"
        ),
        parse_mode="HTML",
        supports_streaming=True,
        reply_markup=get_audio_button()
    )
    await state.update_data(video_message_id=video_msg.message_id)


async def handle_photo_content(
    message: Message,
    images: list,
    author_link: str,
    bot_username: str,
    state: FSMContext,
    user_id: int,
    status_msg: Message
) -> None:
    """Handle TikTok photo content (single or multiple)."""
    total_downloaded = len(images)

    if total_downloaded == 1:
        await safe_edit_message(status_msg, f"{Emojis.UPLOAD} Sending photo...")
        await handle_single_photo(
            message=message,
            image_path=images[0],
            author_link=author_link,
            bot_username=bot_username,
            state=state,
            user_id=user_id
        )
        asyncio.create_task(cleanup_files([images[0]], user_id))
    else:
        await safe_edit_message(status_msg, f"{Emojis.UPLOAD} Sending {total_downloaded} photos...")
        await send_tiktok_photos(
            message=message,
            images=images,
            author_link=author_link,
            bot_username=bot_username,
            state=state,
            user_id=user_id
        )
        asyncio.create_task(cleanup_files(images, user_id))


async def handle_video_content(
    message: Message,
    file_path: str,
    author_link: str,
    bot_username: str,
    state: FSMContext,
    user_id: int,
    status_msg: Message
) -> bool:
    """Handle TikTok video content. Returns True if successful."""
    file_size_mb = await check_video_size(file_path, user_id, status_msg)
    if file_size_mb is None:
        return False

    await safe_edit_message(status_msg, f"{Emojis.UPLOAD} Sending video...")
    await send_tiktok_video(
        message=message,
        file_path=file_path,
        file_size_mb=file_size_mb,
        author_link=author_link,
        bot_username=bot_username,
        state=state
    )
    asyncio.create_task(cleanup_files([file_path], user_id))
    return True


@router.message(tiktok_url_filter)
async def tiktok_url_handler(message: Message, state: FSMContext):
    """Handle TikTok URL - instantly download and send."""
    user_id = message.from_user.id
    url = message.text.strip()
    start_time = time.time()

    user_logger.log_user_action(
        HANDLER_NAME,
        user_id,
        "TikTok URL received",
        f"URL: {url[:50]}..."
    )

    status_msg = await message.reply(f"{Emojis.HOURGLASS} Processing TikTok link...")

    try:
        await state.update_data(
            url=url,
            timestamp=time.time(),
            platform="tiktok"
        )

        video_info = await tiktok_dl.get_video_info(url)
        username = video_info.get('author', 'unknown')
        content_type = video_info.get('content_type', 'video')

        user_logger.log_user_action(
            HANDLER_NAME,
            user_id,
            "TikTok info retrieved",
            f"User: @{username} | Type: {content_type}"
        )

        # Pre-check estimated size for videos (not photos)
        if content_type != 'photo':
            estimated_size = video_info.get('estimated_size', 0)
            if estimated_size > settings.MAX_FILE_SIZE:
                estimated_mb = estimated_size / BYTES_PER_MB
                max_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB
                is_estimated = video_info.get('size_is_estimated', True)

                user_logger.log_user_error(
                    HANDLER_NAME,
                    user_id,
                    f"Video too large (pre-check): ~{estimated_mb:.1f}MB"
                )

                estimate_note = " (estimated)" if is_estimated else ""
                await safe_edit_message(
                    status_msg,
                    f"{Emojis.CROSS} Video too large{estimate_note}: ~{estimated_mb:.1f} MB\n"
                    f"{Emojis.SIZE} Limit: {max_mb:.0f} MB"
                )
                await state.clear()
                return

        await state.update_data(video_info=video_info)
        await state.set_state(TikTokState.selecting_format)

        cancel_kb = get_cancel_keyboard()

        if content_type == 'photo':
            download_text = f"{Emojis.DOWNLOAD} Downloading photos..."
            await safe_edit_message(status_msg, download_text, reply_markup=cancel_kb)
            user_logger.log_download_start("tiktok", user_id, url)

            photo_progress = create_photo_progress_callback(
                status_msg,
                f"{Emojis.PHOTO} Downloading photos",
                cancel_kb,
                state
            )
            content = await tiktok_dl.download_video(url, photo_progress_callback=photo_progress)
        else:
            download_text = f"{Emojis.DOWNLOAD} Downloading video..."
            await safe_edit_message(status_msg, download_text, reply_markup=cancel_kb)
            user_logger.log_download_start("tiktok", user_id, url)

            video_progress = create_progress_callback(
                status_msg,
                f"{Emojis.DOWNLOAD} Downloading video",
                cancel_kb,
                state
            )
            content = await tiktok_dl.download_video(url, progress_callback=video_progress)

        # Check if user cancelled during download
        if await is_cancelled(state):
            user_logger.log_user_action(HANDLER_NAME, user_id, "Download cancelled by user")
            # Clean up downloaded files
            if isinstance(content, list):
                await cleanup_files(content, user_id)
            elif content and await aiofiles.os.path.exists(content):
                await aiofiles.os.remove(content)
            await safe_edit_message(status_msg, f"{Emojis.CROSS} Download cancelled.")
            await state.clear()
            return

        total_size = await calculate_content_size(content)
        file_size_mb = total_size / BYTES_PER_MB

        user_logger.log_download_complete("tiktok", user_id, file_size_mb)

        bot_me = await message.bot.get_me()
        bot_username = f"@{bot_me.username}" if bot_me.username else ""
        author_link = f'<a href="https://www.tiktok.com/@{username}">@{username}</a>'

        if isinstance(content, list):
            await handle_photo_content(
                message, content, author_link, bot_username, state, user_id, status_msg
            )
        else:
            success = await handle_video_content(
                message, content, author_link, bot_username, state, user_id, status_msg
            )
            if not success:
                return

        await safe_delete_message(status_msg)

        duration = time.time() - start_time
        record_download("tiktok", content_type, True, duration, total_size)
        record_request(HANDLER_NAME, True)
        record_processing_time(HANDLER_NAME, duration)

    except Exception as e:
        user_logger.log_user_error(
            HANDLER_NAME,
            user_id,
            f"TikTok download error: {str(e)}"
        )

        duration = time.time() - start_time
        record_error("tiktok", type(e).__name__)
        record_request(HANDLER_NAME, False)
        record_processing_time(HANDLER_NAME, duration)

        await safe_send_error(
            status_msg,
            f"{Emojis.CROSS} Error downloading TikTok content.\n"
            "Please check the URL and try again."
        )
        await state.clear()
