import asyncio
import logging
import os
import time

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from app.bot.keyboards.tiktok_kb import get_audio_button
from app.bot.states.download_states import TikTokState
from app.bot.utils.logger import user_logger
from app.bot.utils.metrics import (
    record_download,
    record_error,
    record_processing_time,
    record_request,
)
from app.bot.utils.progress import create_video_progress_bar
from app.bot.utils.validators import is_tiktok_url
from app.config.constants import BYTES_PER_MB, Emojis
from app.config.settings import settings
from app.core.file_manager import file_manager

from . import tiktok_dl
from .photo_handler import handle_single_photo, send_tiktok_photos

logger = logging.getLogger(__name__)
router = Router()


def tiktok_url_filter(message: Message) -> bool:
    """Filter for TikTok URLs only."""
    return bool(message.text and is_tiktok_url(message.text.strip()))

async def cleanup_files(file_paths, user_id: int = None):
    """Clean up files using file manager with user logging."""
    if not file_paths:
        return

    # Log cleanup if user_id provided
    if user_id:
        user_logger.log_user_action(
            "url_handler.cleanup_files",
            user_id,
            "Cleaning up temporary files",
            f"Files: {len(file_paths)}"
        )

    # Clean up files using file manager
    deleted_count = await file_manager.cleanup_files(file_paths)

    # Log result if user_id provided
    if user_id and deleted_count > 0:
        user_logger.log_user_action(
            "url_handler.cleanup_files",
            user_id,
            "Files cleaned up",
            f"Deleted: {deleted_count}/{len(file_paths)} files"
        )


@router.message(tiktok_url_filter)
async def tiktok_url_handler(message: Message, state: FSMContext):
    """Handle TikTok URL - instantly download and send."""
    user_id = message.from_user.id
    url = message.text.strip()
    start_time = time.time()

    # Log user action
    user_logger.log_user_action(
        "tiktok_url_handler",
        user_id,
        "TikTok URL received",
        f"URL: {url[:50]}..."
    )

    try:
        # Store URL in state immediately for potential audio extraction
        await state.update_data(
            url=url,
            timestamp=time.time(),  # Store creation time
            platform="tiktok"
        )

        status_msg = await message.reply(f"{Emojis.HOURGLASS} Processing TikTok link...")

        # Get video info
        video_info = await tiktok_dl.get_video_info(url)
        username = video_info.get('author', 'unknown')
        content_type = video_info.get('content_type', 'video')

        # Log video info
        user_logger.log_user_action(
            "tiktok_url_handler",
            user_id,
            "TikTok info retrieved",
            f"User: @{username} | Type: {content_type}"
        )

        # Store video info in state
        await state.update_data(video_info=video_info)
        await state.set_state(TikTokState.selecting_format)

        await status_msg.edit_text(f"{Emojis.DOWNLOAD} Downloading {'photos' if content_type == 'photo' else 'video'}...")

        # Log download start
        user_logger.log_download_start("tiktok", user_id, url)

        # Progress callback
        async def update_progress(percent):
            try:
                progress_bar = create_video_progress_bar(percent)
                await status_msg.edit_text(
                    f"{Emojis.DOWNLOAD} Downloading... {int(percent)}%\n{progress_bar}"
                )
            except Exception:
                pass

        # Download content
        content = await tiktok_dl.download_video(url, progress_callback=update_progress)

        # Calculate file size for logging
        if isinstance(content, list):
            # Photos
            total_size = sum(os.path.getsize(f) for f in content if os.path.exists(f))
        else:
            # Video
            total_size = os.path.getsize(content) if os.path.exists(content) else 0

        file_size_mb = total_size / (1024 * 1024)

        # Log download completion
        user_logger.log_download_complete("tiktok", user_id, file_size_mb)

        # Get bot username for caption
        bot_me = await message.bot.get_me()
        bot_username = f"@{bot_me.username}" if bot_me.username else ""

        # Create author link
        author_link = f'<a href="https://www.tiktok.com/@{username}">@{username}</a>'

        if isinstance(content, list):
            # It's photos
            images = content
            total_downloaded = len(images)

            if total_downloaded == 1:
                await status_msg.edit_text(f"{Emojis.UPLOAD} Sending photo...")

                # Use photo handler
                await handle_single_photo(
                    message=message,
                    image_path=images[0],
                    author_link=author_link,
                    bot_username=bot_username,
                    state=state,
                    user_id=user_id
                )

                # Cleanup in background
                asyncio.create_task(cleanup_files([images[0]], user_id))

            else:
                await status_msg.edit_text(f"{Emojis.UPLOAD} Sending {total_downloaded} photos...")

                # Use photo handler
                await send_tiktok_photos(
                    message=message,
                    images=images,
                    author_link=author_link,
                    bot_username=bot_username,
                    state=state,
                    user_id=user_id
                )

                # Cleanup in background AFTER sending
                asyncio.create_task(cleanup_files(images, user_id))

        else:
            await status_msg.edit_text(f"{Emojis.UPLOAD} Sending video...")

            file_path = content
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            if file_size > settings.MAX_FILE_SIZE:
                user_logger.log_user_error(
                    "tiktok_url_handler",
                    user_id,
                    f"File too large: {file_size_mb:.1f}MB"
                )
                await status_msg.edit_text(
                    f"{Emojis.CROSS} Video too large ({file_size_mb:.1f} MB)\n"
                    f"{Emojis.SIZE} Limit: {settings.MAX_FILE_SIZE / BYTES_PER_MB:.0f} MB"
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
                return

            video_msg = await message.reply_video(
                video=FSInputFile(file_path),
                caption=f"{Emojis.VIDEO} TikTok Video\n{Emojis.USER} {author_link}\n{Emojis.SIZE} {file_size_mb:.1f} MB\n\nDownloaded via:\n{bot_username}",
                parse_mode="HTML",
                supports_streaming=True,
                reply_markup=get_audio_button()
            )

            # Store the message ID for potential audio extraction
            await state.update_data(video_message_id=video_msg.message_id)

            # Cleanup video file in background
            asyncio.create_task(cleanup_files([file_path], user_id))

        # Delete status message
        try:
            await status_msg.delete()
        except Exception:
            pass

        # Record metrics
        duration = time.time() - start_time
        record_download("tiktok", content_type, True, duration, total_size)
        record_request("tiktok_url_handler", True)
        record_processing_time("tiktok_url_handler", duration)

    except Exception as e:
        # Log error
        user_logger.log_user_error(
            "tiktok_url_handler",
            user_id,
            f"TikTok download error: {str(e)}"
        )

        # Record error metrics
        duration = time.time() - start_time
        record_error("tiktok", type(e).__name__)
        record_request("tiktok_url_handler", False)
        record_processing_time("tiktok_url_handler", duration)

        try:
            await status_msg.edit_text(
                f"{Emojis.CROSS} Error downloading TikTok content.\n"
                "Please check the URL and try again."
            )
        except Exception:
            await message.reply(
                f"{Emojis.CROSS} Error downloading TikTok content.\n"
                "Please check the URL and try again."
            )
        await state.clear()
