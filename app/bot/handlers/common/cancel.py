from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.config.constants import Emojis

router = Router()


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer(f"{Emojis.CROSS} Cancelled")
    await state.clear()

    try:
        await callback.message.edit_text(f"{Emojis.CROSS} Operation cancelled.")
    except Exception:
        await callback.message.answer(f"{Emojis.CROSS} Operation cancelled.")
