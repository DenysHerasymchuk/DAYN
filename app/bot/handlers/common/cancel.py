from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Handle cancel action."""
    await callback.answer("Cancelled")
    await state.clear()

    try:
        await callback.message.edit_text("❌ Operation cancelled.")
    except Exception:
        await callback.message.answer("❌ Operation cancelled.")
