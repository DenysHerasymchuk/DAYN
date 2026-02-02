import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.states.download_states import TikTokState, YouTubeState
from app.bot.utils.message_helpers import safe_edit_message, safe_send_error
from app.config.constants import CallbackData, Emojis

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == CallbackData.CANCEL)
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Handle cancel button click.

    During download: Sets cancelled flag so download handler can abort.
    During selection: Clears state and shows cancelled message.
    """
    current_state = await state.get_state()

    # Check if we're in a downloading state
    downloading_states = [
        YouTubeState.downloading_video,
        YouTubeState.downloading_audio,
        TikTokState.selecting_format,  # TikTok downloads immediately in this state
    ]

    if current_state in [s.state for s in downloading_states]:
        # Set cancelled flag - download handler will check this
        await state.update_data(cancelled=True)
        await callback.answer(f"{Emojis.CROSS} Cancelling download...")
        await safe_edit_message(
            callback.message,
            f"{Emojis.HOURGLASS} Cancelling download...",
            reply_markup=None
        )
        logger.info(f"Download cancelled by user {callback.from_user.id}")
    else:
        # Not downloading - just clear state
        await callback.answer(f"{Emojis.CROSS} Cancelled")
        await state.clear()
        success = await safe_edit_message(
            callback.message,
            f"{Emojis.CROSS} Operation cancelled."
        )
        if not success:
            await safe_send_error(callback, f"{Emojis.CROSS} Operation cancelled.")


async def is_cancelled(state: FSMContext) -> bool:
    """Check if download was cancelled by user."""
    data = await state.get_data()
    return data.get('cancelled', False)
