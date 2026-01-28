import asyncio
import logging
import time

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, URLInputFile

from app.bot.keyboards.youtube_kb import get_quality_keyboard_with_sizes
from app.bot.states.download_states import YouTubeState
from app.bot.utils.logger import user_logger
from app.bot.utils.metrics import record_error, record_processing_time, record_request
from app.bot.utils.validators import is_youtube_url
from app.config.settings import settings

from . import youtube_dl

logger = logging.getLogger(__name__)
router = Router()


def youtube_url_filter(message: Message) -> bool:
    """Filter for YouTube URLs only."""
    return bool(message.text and is_youtube_url(message.text.strip()))


async def send_initial_status(message: Message) -> Message:
    """Send initial processing status message."""
    return await message.reply("⏳ Processing YouTube link...")


async def update_status(status_msg: Message, text: str):
    """Update status message with error handling."""
    try:
        await status_msg.edit_text(text)
    except Exception as e:
        logger.debug(f"Failed to update status: {e}")


@router.message(youtube_url_filter)
async def youtube_url_handler(message: Message, state: FSMContext):
    """Handle YouTube URL."""
    user_id = message.from_user.id
    url = message.text.strip()
    start_time = time.time()

    # Log user action
    user_logger.log_user_action(
        "youtube_url_handler",
        user_id,
        "YouTube URL received",
        f"URL: {url[:50]}..."
    )

    # Send initial status message
    status_msg = await send_initial_status(message)

    try:
        # Get video info with timeout
        try:
            user_logger.log_user_action(
                "youtube_url_handler",
                user_id,
                "Fetching YouTube video info"
            )

            video_info = await asyncio.wait_for(
                youtube_dl.get_video_info(url),
                timeout=30  # 30 second timeout
            )
        except asyncio.TimeoutError:
            user_logger.log_user_error(
                "youtube_url_handler",
                user_id,
                "Timeout getting YouTube info"
            )
            await update_status(
                status_msg,
                "❌ Timeout getting video info.\n"
                "YouTube might be slow or the video is too large."
            )
            await state.clear()
            return
        except Exception as e:
            user_logger.log_user_error(
                "youtube_url_handler",
                user_id,
                f"YouTube API error: {str(e)}"
            )
            await update_status(
                status_msg,
                "❌ Error getting video info.\n"
                "Please check the URL and try again."
            )
            await state.clear()
            return

        # Check if anything is available
        qualities_with_size = video_info.get('qualities_with_size', [])
        audio_under_limit = video_info.get('audio_under_limit', False)

        if not qualities_with_size and not audio_under_limit:
            max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)

            user_logger.log_user_action(
                "youtube_url_handler",
                user_id,
                "No suitable formats available",
                f"Title: {video_info.get('title', 'Unknown')[:50]} | Limit: {max_size_mb:.0f}MB"
            )

            await update_status(
                status_msg,
                f"❌ <b>Unable to download</b>\n\n"
                f"📹 {video_info['title']}\n"
                f"⏱ Duration: {video_info['duration']}\n\n"
                f"All formats exceed {max_size_mb:.0f} MB limit."
            )
            await state.clear()
            return

        # Log video info retrieval
        user_logger.log_user_action(
            "youtube_url_handler",
            user_id,
            "YouTube info retrieved",
            f"Title: {video_info.get('title', 'Unknown')[:50]} | "
            f"Author: {video_info.get('author', 'Unknown')[:30]} | "
            f"Qualities: {len(qualities_with_size)} | "
            f"Audio available: {audio_under_limit}"
        )

        # Prepare thumbnail asynchronously
        thumbnail = video_info.get('thumbnail')
        thumbnail_file = None
        if thumbnail:
            try:
                # Use URLInputFile without preloading
                thumbnail_file = URLInputFile(
                    thumbnail,
                    filename="thumbnail.jpg"
                )
            except Exception as e:
                logger.warning(f"Could not load thumbnail: {e}")

        # Create keyboard
        keyboard = get_quality_keyboard_with_sizes(
            qualities_with_size,
            audio_under_limit,
            video_info.get('audio_size_str')
        )

        # Prepare caption
        title = video_info.get('title', 'Unknown Title')
        author = video_info.get('author', 'Unknown Author')
        duration = video_info.get('duration', 'Unknown')

        caption = (
            f"📹 <b>{title[:100]}{'...' if len(title) > 100 else ''}</b>\n"
            f"👤 {author[:50]}\n"
            f"⏱ Duration: {duration}\n\n"
            f"💾 Select quality to download:"
        )

        # Send options and delete status message
        try:
            if thumbnail_file:
                options_msg = await message.reply_photo(
                    photo=thumbnail_file,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                options_msg = await message.reply(
                    caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Failed to send options: {e}")
            # Fallback without thumbnail
            options_msg = await message.reply(
                caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        # Store in state WITH TIMESTAMP
        await state.update_data(
            video_info=video_info,
            url=url,
            platform="youtube",
            timestamp=time.time(),
            options_message_id=options_msg.message_id,
            user_id=user_id  # Store user_id in state too
        )
        await state.set_state(YouTubeState.selecting_quality)

        # Delete status message
        try:
            await status_msg.delete()
        except Exception:
            pass

        logger.info(f"YouTube options sent for: {title[:50]}")

        # Log options sent
        user_logger.log_user_action(
            "youtube_url_handler",
            user_id,
            "YouTube options sent to user",
            f"Message ID: {options_msg.message_id}"
        )

        # Record metrics
        duration = time.time() - start_time
        record_request("youtube_url_handler", True)
        record_processing_time("youtube_url_handler", duration)

    except Exception as e:
        user_logger.log_user_error(
            "youtube_url_handler",
            user_id,
            f"YouTube handler error: {str(e)}"
        )

        # Record error metrics
        duration = time.time() - start_time
        record_error("youtube", type(e).__name__)
        record_request("youtube_url_handler", False)
        record_processing_time("youtube_url_handler", duration)

        try:
            await status_msg.edit_text(
                "❌ Unexpected error. Please try again."
            )
        except Exception:
            await message.reply(
                "❌ Unexpected error. Please try again."
            )
        await state.clear()
