from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

request_contact_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Нажмите кнопку, чтобы поделиться номером",
)

