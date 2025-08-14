from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from backend.users.models import User
from bot.handlers.menu import show_main_menu
from bot.keyboards.reply_keyboards import request_contact_kb
from bot.utils.db import is_whitelisted, register_user

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, user: User | None = None):
    await state.clear()
    if user:
        welcome_text = "Приветственное сообщение, информация о возможностях бота"
        await show_main_menu(message, welcome_text)
    else:
        await message.answer(
            "Здравствуйте! Для использования бота, пожалуйста, "
            "подтвердите свой номер телефона",
            reply_markup=request_contact_kb,
        )


@router.message(F.contact)
async def contact_handler(
    message: Message, state: FSMContext, user: User | None = None
):
    await state.clear()
    if user:
        await show_main_menu(message, "Вы уже авторизованы.")
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
        menu_text = "Ваш номер подтвержден и есть в списке. Добро пожаловать!"
        await show_main_menu(message, menu_text)
    else:
        await message.answer(
            "К сожалению, вашего номера нет в белом списке. Доступ запрещен."
        )
