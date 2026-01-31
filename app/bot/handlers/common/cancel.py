import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.utils.message_helpers import safe_edit_message, safe_send_error
from app.config.constants import CallbackData, Emojis

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == CallbackData.CANCEL)
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer(f"{Emojis.CROSS} Cancelled")
    await state.clear()

    success = await safe_edit_message(callback.message, f"{Emojis.CROSS} Operation cancelled.")
    if not success:
        await safe_send_error(callback, f"{Emojis.CROSS} Operation cancelled.")
