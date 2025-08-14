from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline_keyboards import get_main_menu_kb

router = Router()


async def show_main_menu(message: Message, text: str):
    await message.answer(text, reply_markup=await get_main_menu_kb())


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await show_main_menu(callback.message, "Вы вернулись в главное меню.")
