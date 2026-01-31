import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from app.bot.states.download_states import YouTubeState
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
from app.config.settings import settings

from . import youtube_dl

logger = logging.getLogger(__name__)
router = Router()


class DownloadType(Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class DownloadContext:
    callback: CallbackQuery
    state: FSMContext
    user_id: int
    url: str
    video_info: dict
    download_type: DownloadType
    quality: Optional[int] = None

    @property
    def handler_name(self) -> str:
        return f"youtube_{self.download_type.value}_callback"

    @property
    def status_text(self) -> str:
        if self.download_type == DownloadType.VIDEO:
            return f"Downloading {self.quality}p video..."
        return "Downloading audio..."

    @property
    def download_state(self):
        if self.download_type == DownloadType.VIDEO:
            return YouTubeState.downloading_video
        return YouTubeState.downloading_audio


async def validate_session(callback: CallbackQuery, state: FSMContext) -> Optional[tuple]:
    data = await state.get_data()
    video_info = data.get('video_info')
    url = data.get('url')

    if not video_info or not url:
        user_logger.log_user_error(
            "youtube_callback",
            callback.from_user.id,
            "Session expired - missing video_info or url"
        )
        await callback.message.edit_text("Session expired. Please send the URL again.")
        await state.clear()
        return None

    return url, video_info


async def check_file_size(file_path: str, ctx: DownloadContext) -> Optional[float]:
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)

    if file_size > settings.MAX_FILE_SIZE:
        user_logger.log_user_error(
            ctx.handler_name,
            ctx.user_id,
            f"File too large: {file_size_mb:.1f}MB (limit: {max_size_mb:.0f}MB)"
        )
        await ctx.callback.message.edit_text(
            f"File too large ({file_size_mb:.1f} MB)\nLimit: {max_size_mb:.0f} MB"
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        await ctx.state.clear()
        return None

    return file_size_mb


async def send_video(ctx: DownloadContext, file_path: str, file_size_mb: float) -> None:
    bot_me = await ctx.callback.bot.get_me()
    bot_username = f"@{bot_me.username}" if bot_me.username else ""

    await ctx.callback.bot.send_video(
        chat_id=ctx.callback.message.chat.id,
        video=FSInputFile(file_path),
        caption=f"<b>{ctx.video_info['title']}</b>\n"
                f"Quality: {ctx.quality}p\n"
                f"Size: {file_size_mb:.1f} MB\n\n"
                f"Downloaded via:\n{bot_username}",
        parse_mode="HTML",
        supports_streaming=True
    )


async def send_audio(ctx: DownloadContext, file_path: str) -> None:
    bot_me = await ctx.callback.bot.get_me()
    bot_username = f"@{bot_me.username}" if bot_me.username else ""

    await ctx.callback.bot.send_audio(
        chat_id=ctx.callback.message.chat.id,
        audio=FSInputFile(file_path),
        title=ctx.video_info.get('title', 'Audio')[:64],
        performer=ctx.video_info.get('author', 'Unknown')[:64],
        caption=f"{bot_username}"
    )


async def process_download(ctx: DownloadContext) -> None:
    start_time = time.time()

    try:
        user_logger.log_user_action(
            ctx.handler_name,
            ctx.user_id,
            f"{ctx.download_type.value.title()} download started",
            f"Title: {ctx.video_info.get('title', 'Unknown')[:50]}"
        )

        progress_callback = create_progress_callback(ctx.callback.message, ctx.status_text)
        await safe_edit_message(ctx.callback.message, ctx.status_text)

        quality_str = f"{ctx.quality}p" if ctx.quality else "audio"
        user_logger.log_download_start("youtube", ctx.user_id, ctx.url, quality_str)

        await ctx.state.set_state(ctx.download_state)

        if ctx.download_type == DownloadType.VIDEO:
            file_path = await youtube_dl.download_video(
                ctx.url, quality=ctx.quality, progress_callback=progress_callback
            )
        else:
            file_path = await youtube_dl.download_audio(
                ctx.url, progress_callback=progress_callback
            )

        file_size_mb = await check_file_size(file_path, ctx)
        if file_size_mb is None:
            return

        file_size = os.path.getsize(file_path)

        if ctx.download_type == DownloadType.VIDEO:
            await send_video(ctx, file_path, file_size_mb)
        else:
            await send_audio(ctx, file_path)

        user_logger.log_download_complete("youtube", ctx.user_id, file_size_mb, success=True)
        user_logger.log_user_action(
            ctx.handler_name,
            ctx.user_id,
            f"{ctx.download_type.value.title()} sent to user",
            f"Size: {file_size_mb:.1f}MB"
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        await safe_delete_message(ctx.callback.message)

        duration = time.time() - start_time
        record_download("youtube", ctx.download_type.value, True, duration, file_size)
        record_request(ctx.handler_name, True)
        record_processing_time(ctx.handler_name, duration)

        await ctx.state.clear()

    except Exception as e:
        user_logger.log_user_error(
            ctx.handler_name,
            ctx.user_id,
            f"YouTube {ctx.download_type.value} error: {str(e)}"
        )

        duration = time.time() - start_time
        record_error("youtube", type(e).__name__)
        record_request(ctx.handler_name, False)
        record_processing_time(ctx.handler_name, duration)

        await safe_send_error(ctx.callback, "Download failed. Please try again.")
        await ctx.state.clear()


@router.callback_query(F.data.startswith("quality_"), YouTubeState.selecting_quality)
async def youtube_quality_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    session = await validate_session(callback, state)
    if not session:
        return

    url, video_info = session
    quality = int(callback.data.split('_')[1])

    ctx = DownloadContext(
        callback=callback,
        state=state,
        user_id=callback.from_user.id,
        url=url,
        video_info=video_info,
        download_type=DownloadType.VIDEO,
        quality=quality
    )

    await process_download(ctx)


@router.callback_query(F.data == "format_audio", YouTubeState.selecting_quality)
async def youtube_audio_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    session = await validate_session(callback, state)
    if not session:
        return

    url, video_info = session

    ctx = DownloadContext(
        callback=callback,
        state=state,
        user_id=callback.from_user.id,
        url=url,
        video_info=video_info,
        download_type=DownloadType.AUDIO
    )

    await process_download(ctx)
