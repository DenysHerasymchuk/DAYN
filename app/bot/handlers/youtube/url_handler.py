import asyncio
import logging
import time

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, URLInputFile

from app.bot.keyboards.youtube_kb import get_quality_keyboard_with_sizes
from app.bot.states.download_states import YouTubeState
from app.bot.utils.logger import user_logger
from app.bot.utils.message_helpers import (
    safe_delete_message,
    safe_edit_message,
    safe_send_error,
)
from app.bot.utils.metrics import record_error, record_processing_time, record_request
from app.bot.utils.validators import is_youtube_url
from app.config.constants import BYTES_PER_MB, Emojis
from app.config.settings import settings

from . import youtube_dl

logger = logging.getLogger(__name__)
router = Router()

HANDLER_NAME = "youtube_url_handler"


def youtube_url_filter(message: Message) -> bool:
    """Filter for YouTube URLs only."""
    return bool(message.text and is_youtube_url(message.text.strip()))


async def load_thumbnail(url: str) -> URLInputFile | None:
    """Attempt to load thumbnail, returns None on failure."""
    try:
        return URLInputFile(url, filename="thumbnail.jpg")
    except Exception as e:
        logger.warning(f"Could not load thumbnail: {e}")
        return None


async def send_quality_options(
    message: Message,
    caption: str,
    keyboard,
    thumbnail_file: URLInputFile | None
) -> Message:
    """Send quality selection options with optional thumbnail."""
    try:
        if thumbnail_file:
            return await message.reply_photo(
                photo=thumbnail_file,
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            return await message.reply(
                caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Failed to send options with thumbnail: {e}")
        return await message.reply(
            caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(youtube_url_filter)
async def youtube_url_handler(message: Message, state: FSMContext):
    """Handle YouTube URL."""
    user_id = message.from_user.id
    url = message.text.strip()
    start_time = time.time()

    user_logger.log_user_action(
        HANDLER_NAME,
        user_id,
        "YouTube URL received",
        f"URL: {url[:50]}..."
    )

    status_msg = await message.reply(f"{Emojis.HOURGLASS} Processing YouTube link...")

    try:
        user_logger.log_user_action(HANDLER_NAME, user_id, "Fetching YouTube video info")

        try:
            video_info = await asyncio.wait_for(
                youtube_dl.get_video_info(url),
                timeout=30
            )
        except asyncio.TimeoutError:
            user_logger.log_user_error(HANDLER_NAME, user_id, "Timeout getting YouTube info")
            await safe_edit_message(
                status_msg,
                f"{Emojis.CROSS} Timeout getting video info.\n"
                "YouTube might be slow or the video is too large."
            )
            await state.clear()
            return
        except Exception as e:
            user_logger.log_user_error(HANDLER_NAME, user_id, f"YouTube API error: {str(e)}")
            await safe_edit_message(
                status_msg,
                f"{Emojis.CROSS} Error getting video info.\n"
                "Please check the URL and try again."
            )
            await state.clear()
            return

        qualities_with_size = video_info.get('qualities_with_size', [])
        audio_under_limit = video_info.get('audio_under_limit', False)

        if not qualities_with_size and not audio_under_limit:
            max_size_mb = settings.MAX_FILE_SIZE / BYTES_PER_MB

            user_logger.log_user_action(
                HANDLER_NAME,
                user_id,
                "No suitable formats available",
                f"Title: {video_info.get('title', 'Unknown')[:50]} | Limit: {max_size_mb:.0f}MB"
            )

            await safe_edit_message(
                status_msg,
                f"{Emojis.CROSS} <b>Unable to download</b>\n\n"
                f"{Emojis.VIDEO} {video_info['title']}\n"
                f"{Emojis.CLOCK} Duration: {video_info['duration']}\n\n"
                f"All formats exceed {max_size_mb:.0f} MB limit."
            )
            await state.clear()
            return

        user_logger.log_user_action(
            HANDLER_NAME,
            user_id,
            "YouTube info retrieved",
            f"Title: {video_info.get('title', 'Unknown')[:50]} | "
            f"Author: {video_info.get('author', 'Unknown')[:30]} | "
            f"Qualities: {len(qualities_with_size)} | "
            f"Audio available: {audio_under_limit}"
        )

        thumbnail = video_info.get('thumbnail')
        thumbnail_file = await load_thumbnail(thumbnail) if thumbnail else None

        keyboard = get_quality_keyboard_with_sizes(
            qualities_with_size,
            audio_under_limit,
            video_info.get('audio_size_str')
        )

        title = video_info.get('title', 'Unknown Title')
        author = video_info.get('author', 'Unknown Author')
        video_duration = video_info.get('duration', 'Unknown')

        caption = (
            f"{Emojis.VIDEO} <b>{title[:100]}{'...' if len(title) > 100 else ''}</b>\n"
            f"{Emojis.USER} {author[:50]}\n"
            f"{Emojis.CLOCK} Duration: {video_duration}\n\n"
            f"{Emojis.SIZE} Select quality to download:"
        )

        options_msg = await send_quality_options(message, caption, keyboard, thumbnail_file)

        await state.update_data(
            video_info=video_info,
            url=url,
            platform="youtube",
            timestamp=time.time(),
            options_message_id=options_msg.message_id,
            user_id=user_id
        )
        await state.set_state(YouTubeState.selecting_quality)

        await safe_delete_message(status_msg)

        logger.info(f"YouTube options sent for: {title[:50]}")

        user_logger.log_user_action(
            HANDLER_NAME,
            user_id,
            "YouTube options sent to user",
            f"Message ID: {options_msg.message_id}"
        )

        duration = time.time() - start_time
        record_request(HANDLER_NAME, True)
        record_processing_time(HANDLER_NAME, duration)

    except Exception as e:
        user_logger.log_user_error(
            HANDLER_NAME,
            user_id,
            f"YouTube handler error: {str(e)}"
        )

        duration = time.time() - start_time
        record_error("youtube", type(e).__name__)
        record_request(HANDLER_NAME, False)
        record_processing_time(HANDLER_NAME, duration)

        await safe_send_error(
            status_msg,
            f"{Emojis.CROSS} Unexpected error. Please try again."
        )
        await state.clear()
