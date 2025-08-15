from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from backend.users.models import User
from bot.handlers.menu import show_main_menu
from bot.keyboards.reply_keyboards import request_contact_kb
from bot.utils.db import get_bot_texts, is_whitelisted, register_user

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, user: User | None = None):
    await state.clear()
    texts = await get_bot_texts()
    if user:
        await show_main_menu(message, texts.welcome_message)
    else:
        await message.answer(
            texts.request_contact_message,
            reply_markup=request_contact_kb,
        )


@router.message(F.contact)
async def contact_handler(
    message: Message, state: FSMContext, user: User | None = None
):
    await state.clear()
    texts = await get_bot_texts()

    if user:
        await show_main_menu(message, texts.already_authorized_message)
        return

    if message.chat.id != message.contact.user_id:
        return

    user, response_text = await register_user(
        telegram_id=message.contact.user_id,
        username=message.from_user.username,
        phone_number_str="{0:+.0f}".format(int(message.contact.phone_number)),
    )

    await message.answer(response_text, reply_markup=ReplyKeyboardRemove())
    if not user:
        return

    if await is_whitelisted(user.phone_number):
        menu_text = texts.whitelist_success_message
        await show_main_menu(message, menu_text)
    else:
        await message.answer(texts.whitelist_fail_message)
