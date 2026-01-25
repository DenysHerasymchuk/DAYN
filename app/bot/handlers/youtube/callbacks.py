import os
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from app.config.settings import settings
from app.bot.utils.progress import create_video_progress_bar
from app.bot.states.download_states import YouTubeState
from app.bot.utils.logger import user_logger
from . import youtube_dl

logger = logging.getLogger(__name__)
router = Router()


# YouTube Callbacks
@router.callback_query(F.data.startswith("quality_"), YouTubeState.selecting_quality)
async def youtube_quality_callback(callback: CallbackQuery, state: FSMContext):
    """Handle YouTube quality selection."""
    await callback.answer()

    user_id = callback.from_user.id

    try:
        # Get data from state
        data = await state.get_data()
        video_info = data.get('video_info')
        url = data.get('url')

        if not video_info or not url:
            user_logger.log_user_error(
                "youtube_quality_callback",
                user_id,
                "Session expired - missing video_info or url"
            )
            await callback.message.edit_text("❌ Session expired. Please send the URL again.")
            await state.clear()
            return

        # Extract quality
        quality = int(callback.data.split('_')[1])

        # Log quality selection
        user_logger.log_user_action(
            "youtube_quality_callback",
            user_id,
            "Quality selected",
            f"Quality: {quality}p | Title: {video_info.get('title', 'Unknown')[:50]}"
        )

        # Update message with progress
        progress_bar = create_video_progress_bar(0)
        try:
            await callback.message.edit_caption(
                caption=f"⬇️ Downloading {quality}p video...\n{progress_bar}",
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                f"⬇️ Downloading {quality}p video...\n{progress_bar}"
            )

        # Progress callback
        async def update_progress(percent):
            try:
                progress_bar = create_video_progress_bar(percent)
                try:
                    await callback.message.edit_caption(
                        caption=f"⬇️ Downloading {quality}p video...\n{progress_bar}",
                        parse_mode="HTML"
                    )
                except:
                    await callback.message.edit_text(
                        f"⬇️ Downloading {quality}p video...\n{progress_bar}"
                    )
            except:
                pass

        # Log download start
        user_logger.log_download_start("youtube", user_id, url, f"{quality}p")

        # Download video
        await state.set_state(YouTubeState.downloading_video)
        file_path = await youtube_dl.download_video(
            url,
            quality=quality,
            progress_callback=update_progress
        )

        # Check file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        if file_size > settings.MAX_FILE_SIZE:
            user_logger.log_user_error(
                "youtube_quality_callback",
                user_id,
                f"File too large: {file_size_mb:.1f}MB (limit: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f}MB)"
            )
            await callback.message.edit_text(
                f"❌ File too large ({file_size_mb:.1f} MB)\n"
                f"Limit: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            await state.clear()
            return

        # Send video
        video_file = FSInputFile(file_path)
        bot_me = await callback.bot.get_me()
        bot_username = f"@{bot_me.username}" if bot_me.username else ""

        await callback.bot.send_video(
            chat_id=callback.message.chat.id,
            video=video_file,
            caption=f"✅ <b>{video_info['title']}</b>\n"
                    f"📺 Quality: {quality}p\n"
                    f"💾 Size: {file_size_mb:.1f} MB\n\n"
                    f"Downloaded via:\n{bot_username}",
            parse_mode="HTML",
            supports_streaming=True
        )

        # Log successful download
        user_logger.log_download_complete("youtube", user_id, file_size_mb, success=True)
        user_logger.log_user_action(
            "youtube_quality_callback",
            user_id,
            "Video sent to user",
            f"Size: {file_size_mb:.1f}MB | Quality: {quality}p"
        )

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete options message
        try:
            await callback.message.delete()
        except:
            pass

        await state.clear()

    except Exception as e:
        user_logger.log_user_error(
            "youtube_quality_callback",
            user_id,
            f"YouTube download error: {str(e)}"
        )
        await callback.message.edit_text("❌ Download failed. Please try again.")
        await state.clear()


@router.callback_query(F.data == "format_audio", YouTubeState.selecting_quality)
async def youtube_audio_callback(callback: CallbackQuery, state: FSMContext):
    """Handle YouTube audio download."""
    await callback.answer()

    user_id = callback.from_user.id

    try:
        # Get data from state
        data = await state.get_data()
        video_info = data.get('video_info')
        url = data.get('url')

        if not video_info or not url:
            user_logger.log_user_error(
                "youtube_audio_callback",
                user_id,
                "Session expired - missing video_info or url"
            )
            await callback.message.edit_text("❌ Session expired. Please send the URL again.")
            await state.clear()
            return

        # Log audio download selection
        user_logger.log_user_action(
            "youtube_audio_callback",
            user_id,
            "Audio download selected",
            f"Title: {video_info.get('title', 'Unknown')[:50]}"
        )

        # Update message with progress
        progress_bar = create_video_progress_bar(0)
        try:
            await callback.message.edit_caption(
                caption=f"🎵 Downloading audio...\n{progress_bar}",
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(f"🎵 Downloading audio...\n{progress_bar}")

        # Progress callback
        async def update_progress(percent):
            try:
                progress_bar = create_video_progress_bar(percent)
                try:
                    await callback.message.edit_caption(
                        caption=f"🎵 Downloading audio...\n{progress_bar}",
                        parse_mode="HTML"
                    )
                except:
                    await callback.message.edit_text(f"🎵 Downloading audio...\n{progress_bar}")
            except:
                pass

        # Log download start
        user_logger.log_download_start("youtube", user_id, url, "audio")

        # Download audio
        await state.set_state(YouTubeState.downloading_audio)
        file_path = await youtube_dl.download_audio(
            url,
            progress_callback=update_progress
        )

        # Check file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        if file_size > settings.MAX_FILE_SIZE:
            user_logger.log_user_error(
                "youtube_audio_callback",
                user_id,
                f"Audio too large: {file_size_mb:.1f}MB (limit: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f}MB)"
            )
            await callback.message.edit_text(
                f"❌ Audio too large ({file_size_mb:.1f} MB)\n"
                f"Limit: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            await state.clear()
            return

        # Send audio
        audio_file = FSInputFile(file_path)
        bot_me = await callback.bot.get_me()
        bot_username = f"@{bot_me.username}" if bot_me.username else ""

        await callback.bot.send_audio(
            chat_id=callback.message.chat.id,
            audio=audio_file,
            title=video_info.get('title', 'Audio')[:64],
            performer=video_info.get('author', 'Unknown')[:64],
            caption=f"{bot_username}"
        )

        # Log successful audio download
        user_logger.log_download_complete("youtube", user_id, file_size_mb, success=True)
        user_logger.log_user_action(
            "youtube_audio_callback",
            user_id,
            "Audio sent to user",
            f"Size: {file_size_mb:.1f}MB"
        )

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete options message
        try:
            await callback.message.delete()
        except:
            pass

        await state.clear()

    except Exception as e:
        user_logger.log_user_error(
            "youtube_audio_callback",
            user_id,
            f"YouTube audio download error: {str(e)}"
        )
        await callback.message.edit_text("❌ Audio download failed. Please try again.")
        await state.clear()