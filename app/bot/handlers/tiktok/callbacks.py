import os
import logging
import time
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from app.config.settings import settings
from app.bot.keyboards.tiktok_kb import get_audio_button
from app.bot.utils.progress import create_video_progress_bar
from app.bot.utils.logger import user_logger
from . import tiktok_dl

logger = logging.getLogger(__name__)
router = Router()


# TikTok Callbacks
@router.callback_query(F.data == "tiktok_extract_audio")
async def tiktok_extract_audio_callback(callback: CallbackQuery, state: FSMContext):
    """Handle TikTok audio extraction from video."""

    user_id = callback.from_user.id

    try:
        # Get data from state
        data = await state.get_data()
        url = data.get('url')
        video_info = data.get('video_info', {})

        # CHECK TIMESTAMP
        timestamp = data.get('timestamp', 0)
        current_time = time.time()

        # Clear state if older than 24 hours (86400 seconds)
        if current_time - timestamp > 86400:
            await state.clear()
            user_logger.log_user_action(
                "tiktok_extract_audio_callback",
                user_id,
                "Session expired",
                f"Age: {current_time - timestamp:.0f}s"
            )
            await callback.answer("⏳ Session expired. Please send the TikTok URL again.", show_alert=True)

            # Remove the audio button
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except:
                pass
            return

        if not url:
            user_logger.log_user_error(
                "tiktok_extract_audio_callback",
                user_id,
                "No URL in state"
            )
            # Try to get URL from the original message text
            try:
                video_message_id = data.get('video_message_id')
                if video_message_id:
                    await callback.message.reply(
                        "⚠️ Session expired. Please send the TikTok URL again for audio extraction."
                    )
                    await state.clear()
                    return
            except:
                pass

            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.reply("❌ Please send the TikTok URL again for audio extraction.")
            await state.clear()
            return

        # Log audio extraction start
        user_logger.log_user_action(
            "tiktok_extract_audio_callback",
            user_id,
            "Audio extraction started",
            f"User: @{video_info.get('author', 'unknown')}"
        )

        # Send status message
        status_msg = await callback.message.reply("🎵 Extracting audio...")

        # Progress callback
        async def update_progress(percent):
            try:
                progress_bar = create_video_progress_bar(percent)
                await status_msg.edit_text(f"🎵 Extracting audio... {int(percent)}%\n{progress_bar}")
            except:
                pass

        # Log download start
        user_logger.log_download_start("tiktok_audio", user_id, url)

        # Download audio directly from the URL
        file_path = await tiktok_dl.download_audio(url, progress_callback=update_progress)

        # Check file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        if file_size > settings.MAX_FILE_SIZE:
            user_logger.log_user_error(
                "tiktok_extract_audio_callback",
                user_id,
                f"Audio too large: {file_size_mb:.1f}MB"
            )
            await status_msg.edit_text(
                f"❌ Audio too large ({file_size_mb:.1f} MB)\n"
                f"Limit: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        # Get bot username
        bot_me = await callback.bot.get_me()
        bot_username = f"@{bot_me.username}" if bot_me.username else ""

        # Create author link
        username = video_info.get('author', 'unknown')
        author_link = f'<a href="https://www.tiktok.com/@{username}">@{username}</a>'

        # Send audio
        await callback.bot.send_audio(
            chat_id=callback.message.chat.id,
            audio=FSInputFile(file_path),
            title=f"TikTok Audio - @{username}"[:64],
            performer=username[:64],
            caption=f"🎵 TikTok Audio\n👤 {author_link}\n\nDownloaded via:\n{bot_username}",
            parse_mode="HTML"
        )

        # Log successful extraction
        user_logger.log_download_complete("tiktok_audio", user_id, file_size_mb, success=True)
        user_logger.log_user_action(
            "tiktok_extract_audio_callback",
            user_id,
            "Audio extracted and sent",
            f"Size: {file_size_mb:.1f}MB"
        )

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete status message
        await status_msg.delete()

        # Remove the audio button from original message
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass

    except Exception as e:
        user_logger.log_user_error(
            "tiktok_extract_audio_callback",
            user_id,
            f"TikTok audio extraction error: {str(e)}"
        )
        try:
            await callback.message.reply("❌ Audio extraction failed. Please try again.")
        except:
            pass