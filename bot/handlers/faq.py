import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, FSInputFile

from bot.keyboards.inline_keyboards import FaqCallback, get_faq_list_kb
from bot.utils.db import get_faq_item, get_faq_list

router = Router()


@router.callback_query(F.data == "show_faq_list")
async def show_faq_list_handler(callback: CallbackQuery):
    faq_list = await get_faq_list()
    if not faq_list:
        await callback.answer("Раздел FAQ пока пуст.", show_alert=True)
        return

    await callback.message.edit_text(
        "Часто задаваемые вопросы:", reply_markup=get_faq_list_kb(faq_list)
    )
    await callback.answer()


@router.callback_query(FaqCallback.filter())
async def show_faq_answer_handler(callback: CallbackQuery, callback_data: FaqCallback):
    faq_item = await get_faq_item(callback_data.id)
    if not faq_item:
        await callback.answer(
            "Извините, этот вопрос больше не актуален.", show_alert=True
        )
        return

    question_text = html.escape(faq_item.question)
    answer_text = html.escape(faq_item.answer)
    full_text = f"<b>{question_text}</b>\n\n{answer_text}"

    try:
        if faq_item.media_file and faq_item.media_type:
            file = FSInputFile(faq_item.media_file.path)
            media_type = faq_item.media_type

            if media_type == faq_item.MediaType.PHOTO:
                await callback.message.answer_photo(file, caption=full_text)
            elif media_type == faq_item.MediaType.VIDEO:
                await callback.message.answer_video(file, caption=full_text)
            elif media_type == faq_item.MediaType.DOCUMENT:
                await callback.message.answer_document(file, caption=full_text)
            elif media_type == faq_item.MediaType.AUDIO:
                await callback.message.answer_audio(file, caption=full_text)
        else:
            await callback.message.answer(full_text)
    except TelegramForbiddenError as e:
        logging.warning(
            f"Не удалось отправить сообщение пользователю {callback.message.chat.id} (т.к. заблочил/удалил бота): {e}"
        )
    except (TelegramBadRequest, FileNotFoundError) as e:
        logging.error(f"Failed to send FAQ media for item {faq_item.id}: {e}")
        await callback.message.answer(
            f"{full_text}\n\n<i>(Не удалось загрузить прикрепленный файл)</i>"
        )

    await callback.answer()
