import io
import logging

import docx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from backend.checker.tasks import check_code_task
from bot.states import CodeCheck

router = Router()

ALLOWED_MIME_TYPES = [
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/x-python",
    "text/x-python-script",
    "application/x-python-code",
    "application/octet-stream",
]
ALLOWED_EXTENSIONS = (".py", ".txt", ".docx")
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024


def decode_file_content(file_bytes: bytes) -> str | None:
    encodings_to_try = ["utf-8", "windows-1251", "cp1251"]
    for encoding in encodings_to_try:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    logging.error(f"Failed to decode file with encodings: {encodings_to_try}")
    return None


@router.callback_query(F.data == "check_code")
async def check_code_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CodeCheck.waiting_for_code)
    await callback.message.edit_text(
        "Отправьте мне свой python-код текстом или файлом (.txt, .py, .docx)."
    )
    await callback.answer()


@router.message(CodeCheck.waiting_for_code, F.text)
async def code_received_text(message: Message, state: FSMContext):
    code = message.text
    await state.clear()
    await message.answer(
        "Код получен и отправлен на проверку. Это может занять несколько минут. Ожидайте..."
    )

    check_code_task.delay(user_id=message.from_user.id, code=code)


@router.message(CodeCheck.waiting_for_code, F.document)
async def code_received_document(message: Message, state: FSMContext):
    if message.document.file_size > MAX_FILE_SIZE_BYTES:
        logging.warning(
            f"User {message.from_user.id} tried to upload a large file: {message.document.file_size} bytes."
        )
        await message.answer(
            f"Файл слишком большой. Максимальный размер файла для проверки кода — {MAX_FILE_SIZE_BYTES // 1024 // 1024} МБ."
        )
        return

    file_name = message.document.file_name.lower()
    is_allowed_extension = file_name.endswith(ALLOWED_EXTENSIONS)
    is_allowed_mime = message.document.mime_type in ALLOWED_MIME_TYPES

    if not (is_allowed_extension or is_allowed_mime):
        await message.answer(
            "Неподдерживаемый тип файла. Пожалуйста, отправьте код в файле с расширением .py, .txt или .docx."
        )
        return

    try:
        file_info = await message.bot.get_file(message.document.file_id)
        file_in_memory = await message.bot.download_file(file_info.file_path)

        file_bytes = file_in_memory.read()

    except Exception as e:
        logging.error(
            f"Failed to download/read file from user {message.from_user.id}: {e}"
        )
        await message.answer("Не удалось загрузить файл. Попробуйте еще раз.")
        return

    code = None
    if file_name.lower().endswith(".docx"):
        try:
            doc_stream = io.BytesIO(file_bytes)
            doc = docx.Document(doc_stream)
            code = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logging.error(
                f"Failed to read .docx file from user {message.from_user.id}: {e}"
            )
            await message.answer(
                "Не удалось прочитать .docx файл. Возможно, он поврежден или имеет нестандартный формат."
            )
            return
    else:
        code = decode_file_content(file_bytes)
        if code is None:
            await message.answer(
                "Не удалось определить кодировку файла. Пожалуйста, сохраните его в UTF-8 и попробуйте снова."
            )
            return

    if not code.strip():
        await message.answer("Файл пустой. Пожалуйста, отправьте файл с кодом.")
        return

    await state.clear()
    await message.answer(
        "Код получен и отправлен на проверку. Это может занять несколько минут. Ожидайте..."
    )

    check_code_task.delay(user_id=message.from_user.id, code=code)


@router.message(CodeCheck.waiting_for_code)
async def wrong_input_in_code_check(message: Message):
    await message.answer("Пожалуйста, отправьте код текстом или файлом.")
