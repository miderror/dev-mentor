from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.db import get_support_link


class FaqCallback(CallbackData, prefix="faq"):
    id: int


async def get_main_menu_kb() -> InlineKeyboardMarkup:
    support_link = await get_support_link()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Проверить код", callback_data="check_code")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="show_faq_list")],
            [InlineKeyboardButton(text="👨‍💻 Тех. поддержка", url=support_link)],
        ]
    )


def get_faq_list_kb(faq_list: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=question, callback_data=FaqCallback(id=faq_id).pack()
            )
        ]
        for faq_id, question in faq_list
    ]
    buttons.append(
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="back_to_main_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Загрузить код снова", callback_data="check_code"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Вернуться в меню", callback_data="back_to_main_menu"
                )
            ],
        ]
    )
