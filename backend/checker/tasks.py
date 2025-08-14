import logging
import os
import re
import time
from textwrap import dedent

import httpx
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from asgiref.sync import sync_to_async
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils import timezone

from backend.users.models import User
from bot.keyboards.inline_keyboards import get_after_check_kb

from .models import Check, CommonError
from .runner import execute_code

logger = logging.getLogger(__name__)
AI_API_KEY = os.getenv("AI_API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME")


async def get_ai_suggestion(user_code: str, error_traceback: str) -> str:
    system_prompt = "Ты - робот, который исправляет Python код. Ты СТРОГО следуешь формату. Ты НЕ добавляешь лишних слов. Ты отвечаешь ТОЛЬКО на русском."

    part_1 = dedent("""
        ИНСТРУКЦИЯ: Проанализируй КОД и ОШИБКУ после ТВОЯ ЗАДАЧА. Предоставь ТОЛЬКО ТВОЙ ВЫВОД в формате MarkdownV2, точно следуя ШАБЛОНУ ВЫВОДА из ПРИМЕР.
        
        ---
        ПРИМЕР (ШАБЛОН ВЫВОДА ДО ---):
        🧐 **В чем причина ошибки?**
        Ошибка `ZeroDivisionError` происходит, когда программа пытается разделить число на ноль, что является невозможной математической операцией. В вашем коде, в строке `print(a / b)`, переменная `b` равна нулю.

        ✅ **Как это исправить?**
        Перед делением нужно проверить, не равен ли делитель (`b`) нулю.

        Вот исправленный код:
        ```python
        a = 10
        b = 0
        if b != 0:
            print(a / b)
        else:
            print("Ошибка: деление на ноль!")
        ```

        ---
        
        ТВОЯ ЗАДАЧА:

        КОД:
        ```python
    """)

    part_2 = dedent("""
        ```
        
        ОШИБКА:
        ```python
    """)

    part_3 = dedent("""
        ```

        ТВОЙ ВЫВОД (Используй ШАБЛОН ВЫВОДА из ПРИМЕР):
    """)

    user_prompt = f"{part_1}\n{user_code}\n{part_2}\n{error_traceback}\n{part_3}"

    logger.info(f"Запрос к AI с ошибкой: {error_traceback[:100]}...")

    api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    logger.info(f"Запрос к модели {AI_MODEL_NAME}...")
    start_time = time.monotonic()
    ai_response = "Не удалось получить ответ от AI."

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            ai_response = data["choices"][0]["message"]["content"].strip()

    except httpx.RequestError as e:
        logger.error(f"AI request failed: {e}")
        ai_response = "Не удалось связаться с сервисом AI для анализа ошибки."
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse AI response: {e}. Response data: {data}")
        ai_response = "Получен некорректный ответ от сервиса AI."

    end_time = time.monotonic()
    duration_ms = int((end_time - start_time) * 1000)

    if ai_response.startswith("```markdown"):
        ai_response = ai_response[11:]
    if ai_response.startswith("```"):
        ai_response = ai_response[3:]
    if ai_response.endswith("```"):
        ai_response = ai_response[:-3]

    return ai_response.strip(), duration_ms


async def find_common_error(stderr: str) -> CommonError | None:
    common_errors = await sync_to_async(list)(CommonError.objects.all())
    for error in common_errors:
        if re.search(error.error_pattern, stderr, re.DOTALL):
            return error
    return None


@shared_task
def check_code_task(user_id: int, code: str):
    import asyncio

    asyncio.run(check_code_async(user_id, code))


async def check_code_async(user_id: int, code: str, language: str = "python"):
    bot = Bot(token=settings.BOT_TOKEN, default=None)
    check_instance = None
    try:
        user = await User.objects.aget(telegram_id=user_id)
        check_instance = await Check.objects.acreate(
            user=user, code=code, status=Check.Status.RUNNING
        )

        result = await sync_to_async(execute_code)(code, language)

        update_fields = {
            "checks_count": models.F("checks_count") + 1,
            "last_activity_at": timezone.now(),
        }

        if result["exit_code"] == 0 and not result["stderr"]:
            check_instance.status = Check.Status.SUCCESS
            check_instance.stdout = result["stdout"]

            update_fields["successful_checks_count"] = (
                models.F("successful_checks_count") + 1
            )

            response_text = "✅ **Ваш код отработал успешно\\!**"
        else:
            if result["timeout"]:
                check_instance.status = Check.Status.TIMEOUT
            else:
                check_instance.status = Check.Status.ERROR

            check_instance.stderr = result["stderr"]

            update_fields["failed_checks_count"] = models.F("failed_checks_count") + 1

            common_error = await find_common_error(result["stderr"])

            explanation = ""
            ai_time_ms = None
            if common_error:
                explanation = f"🧐 **В чем причина ошибки?**\n{common_error.title}\n\n✅ **Как это исправить?**\n{common_error.description}"
            else:
                explanation, ai_time_ms = await get_ai_suggestion(
                    code[:2000], result["stderr"]
                )
                check_instance.ai_response_ms = ai_time_ms

            check_instance.ai_suggestion = explanation
            sanitized_stderr = result["stderr"][:1000].replace("```", "``\u200b`")
            translation_dict = {
                "[": r"\[",
                "]": r"\]",
                "(": r"\(",
                ")": r"\)",
                "~": r"\~",
                ">": r"\>",
                "#": r"\#",
                "+": r"\+",
                "=": r"\=",
                "-": r"\-",
                "|": r"\|",
                "{": r"\{",
                "}": r"\}",
                ".": r"\.",
                "!": r"\!",
            }

            translation_table = str.maketrans(translation_dict)
            sanitized_explanation = explanation.translate(translation_table)
            if sanitized_explanation.count("```") % 2 != 0:
                sanitized_explanation += "\n```"

            response_text = (
                "❌ **В вашем коде произошла ошибка\\!**\n\n"
                f"**Текст ошибки:**\n```\n{sanitized_stderr}\n```\n\n"
                f"**Анализ и решение:**\n{sanitized_explanation}"
            )

        await sync_to_async(User.objects.filter(telegram_id=user_id).update)(
            **update_fields
        )
        await check_instance.asave()
        try:
            await bot.send_message(
                user_id,
                response_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=get_after_check_kb(),
            )
        except TelegramBadRequest as e:
            logger.warning(
                f"Failed to send formatted message, sending plain text. Error: {e}"
            )
            sanitized_stderr = re.sub(r"[`*_\[\]()~>#\+\-=|{}.!]", "", sanitized_stderr)
            sanitized_explanation = re.sub(
                r"[`*_\[\]()~>#\+\-=|{}.!]", "", sanitized_explanation
            )
            response_text = (
                "❌ **В вашем коде произошла ошибка\\!**\n\n"
                f"**Текст ошибки:**\n```\n{sanitized_stderr}\n```\n\n"
                f"**Анализ и решение:**\n{sanitized_explanation}"
            )
            await bot.send_message(
                user_id,
                response_text,
                reply_markup=get_after_check_kb(),
            )

    except Exception as e:
        logger.exception(f"Critical error in check_code_task for user {user_id}: {e}")
        if check_instance:
            check_instance.status = Check.Status.ERROR
            check_instance.stderr = f"Внутренняя ошибка системы: {e}"
            await check_instance.asave()

        await bot.send_message(
            user_id,
            "Произошла внутренняя ошибка при проверке кода. Мы уже работаем над этим.",
        )

    finally:
        await bot.session.close()
