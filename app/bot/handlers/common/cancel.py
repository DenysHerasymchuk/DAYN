from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Handle cancel action."""
    await callback.answer("Cancelled")
    await state.clear()

    try:
        await callback.message.edit_text("❌ Operation cancelled.")
    except:
        await callback.message.answer("❌ Operation cancelled.")