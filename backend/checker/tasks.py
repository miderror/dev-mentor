import logging
import os
import re
import time
from textwrap import dedent

import httpx
from aiogram import Bot
from aiogram.enums import ParseMode
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
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")


async def get_ai_suggestion(error_traceback: str) -> str:
    system_prompt = (
        "Ты — полезный ассистент-наставник для начинающих Python-программистов. "
        "Твоя задача — анализировать ошибки и давать объяснения на русском языке строго в заданном формате и шаблоне. "
        "Не добавляй никаких вступлений, заключений или лишних фраз. "
        "Ответ должен содержать только два блока, разделенные пустой строкой (шаблон)."
    )

    header = dedent("""
        Проанализируй следующую ошибку в Python коде. Дай ответ строго в формате MarkdownV2, не используя заголовки (#).

        Вот текст ошибки для анализа:
        ```python
    """)

    footer = dedent("""
        ```

        Вот шаблон, в котором строго нужно вернуть ответ (шаблон находится только внутри блока ```, где вместо всех [] подставь нужный ответ):
        ```
        🧐 **В чем причина ошибки?**
        [Здесь кратко и понятно для новичка объясни, что пошло не так в коде]

        ✅ **Как это исправить?**
        [Здесь предложи конкретный код или шаги для исправления]
        ```
    """)

    user_prompt = f"{header}\n{error_traceback}\n{footer}"
    
    logger.info(f"Запрос к AI с ошибкой: {error_traceback[:100]}...")
    start_time = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "codellama:7b-instruct",
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            ai_response = data.get(
                "response", "Не удалось получить ответ от AI."
            ).strip()
    except httpx.RequestError as e:
        logger.error(f"AI request failed: {e}")
        ai_response = "Не удалось связаться с сервисом AI для анализа ошибки."

    end_time = time.monotonic()
    duration_ms = int((end_time - start_time) * 1000)

    return ai_response, duration_ms


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
                explanation, ai_time_ms = await get_ai_suggestion(result["stderr"])
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

            response_text = (
                "❌ **В вашем коде произошла ошибка\\!**\n\n"
                f"**Текст ошибки:**\n```\n{sanitized_stderr}\n```\n\n"
                f"**Анализ и решение:**\n{sanitized_explanation}"
            )

        await sync_to_async(User.objects.filter(telegram_id=user_id).update)(
            **update_fields
        )
        await check_instance.asave()
        await bot.send_message(
            user_id,
            response_text,
            parse_mode=ParseMode.MARKDOWN_V2,
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
