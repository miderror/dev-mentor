import asyncio
import logging
import re

from aiogram import Bot
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils import timezone

from backend.core.markdown import convert_md_to_html_for_telegram
from backend.courses.models import Task, UserTaskStatus
from backend.users.models import User
from bot.keyboards.inline_keyboards import get_after_check_kb, get_feedback_kb
from bot.utils.db import get_check_for_feedback

from . import ai_service
from .models import Check, CommonError
from .runner import execute_code

logger = logging.getLogger(__name__)

MAX_OUTPUT_LENGTH = 1000


async def find_common_error(stderr: str) -> CommonError | None:
    common_errors = await sync_to_async(list)(CommonError.objects.all())
    for error in common_errors:
        if re.search(error.error_pattern, stderr, re.DOTALL):
            return error
    return None


@shared_task
def check_solution_task(user_id: int, code: str, task_id: int):
    asyncio.run(check_solution_async(user_id, code, task_id))


async def check_solution_async(user_id: int, code: str, task_id: int):
    bot = Bot(token=settings.BOT_TOKEN, default=None)
    check_instance = None
    try:
        user = await User.objects.aget(telegram_id=user_id)
        task = await Task.objects.aget(id=task_id)

        check_instance = await Check.objects.acreate(
            user=user, code=code, task=task, status=Check.Status.RUNNING
        )

        tests = task.tests.get("tests", [])
        failed_test_info = None

        for i, test in enumerate(tests):
            input_data = "\n".join(map(str, test.get("input", [])))

            result = await sync_to_async(execute_code)(code, input_data=input_data)

            if result["exit_code"] != 0 or result["stderr"]:
                failed_test_info = {
                    "type": "runtime_error",
                    "test_num": i + 1,
                    "stderr": result["stderr"],
                    "timeout": result["timeout"],
                }
                break

            actual_output = result["stdout"].strip()
            expected_output = str(test["expected"]).strip()

            if isinstance(test["expected"], bool):
                expected_output = str(test["expected"])

            if actual_output != expected_output:
                failed_test_info = {
                    "type": "wrong_answer",
                    "test_num": i + 1,
                    "input": input_data,
                    "expected": expected_output,
                    "actual": actual_output,
                }
                check_instance.stdout = actual_output
                check_instance.error_context = {
                    "input": input_data,
                    "expected": expected_output,
                }
                break

        update_fields = {
            "checks_count": models.F("checks_count") + 1,
            "last_activity_at": timezone.now(),
        }

        if failed_test_info:
            check_instance.status = Check.Status.ERROR

            if failed_test_info["type"] == "runtime_error":
                check_instance.stderr = failed_test_info["stderr"][:MAX_OUTPUT_LENGTH]
                response_text = f"❌ *Ошибка выполнения на тесте #{failed_test_info['test_num']}*\n\nВаш код завершился с ошибкой:\n```\n{check_instance.stderr}\n```"
            else:
                check_instance.stdout = failed_test_info["actual"][:MAX_OUTPUT_LENGTH]
                response_text = (
                    f"❌ *Неверный ответ на тесте #{failed_test_info['test_num']}*\n\n"
                    f"*Входные данные:*\n`{failed_test_info['input']}`\n\n"
                    f"*Ожидаемый результат:*\n`{failed_test_info['expected']}`\n\n"
                    f"*Ваш результат:*\n`{check_instance.stdout}`"
                )

            update_fields["failed_checks_count"] = models.F("failed_checks_count") + 1

        else:
            check_instance.status = Check.Status.SUCCESS
            response_text = "✅ *Решение принято!*\n\nВсе тесты пройдены успешно."
            update_fields["successful_checks_count"] = (
                models.F("successful_checks_count") + 1
            )
            await UserTaskStatus.objects.aupdate_or_create(
                user=user,
                task=task,
                defaults={
                    "status": UserTaskStatus.Status.SOLVED,
                    "solved_at": timezone.now(),
                },
            )

        await sync_to_async(User.objects.filter(telegram_id=user_id).update)(
            **update_fields
        )
        await check_instance.asave()

        keyboard = get_feedback_kb(check_id=check_instance.id)
        await bot.send_message(
            user_id, response_text, reply_markup=keyboard, parse_mode="Markdown"
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


@shared_task
def get_ai_feedback_task(user_id: int, check_id: int):
    asyncio.run(get_ai_feedback_async(user_id, check_id))


async def get_ai_feedback_async(user_id: int, check_id: int):
    bot = Bot(token=settings.BOT_TOKEN, default=None)

    check, task = await get_check_for_feedback(check_id, user_id)
    if not check or not task:
        logger.warning(
            f"AI feedback requested for invalid check_id {check_id} or no access for user {user_id}"
        )
        await bot.send_message(user_id, "Не удалось найти вашу проверку.")
        await bot.session.close()
        return

    ai_suggestion, duration_ms = await ai_service.get_ai_suggestion(check, task)

    check.ai_suggestion = ai_suggestion
    check.ai_response_ms = duration_ms
    await check.asave(update_fields=["ai_suggestion", "ai_response_ms"])

    header = "<b>🤖 Обратная связь от AI:</b>"
    html_suggestion = convert_md_to_html_for_telegram(ai_suggestion)
    final_text = f"{header}\n\n{html_suggestion}"

    try:
        await bot.send_message(
            user_id,
            final_text,
            reply_markup=get_after_check_kb(),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Failed to send AI feedback as HTML, falling back to plain text. Error: {e}")
        await bot.send_message(
            user_id,
            f"🤖 Обратная связь от AI:\n\n{ai_suggestion}",
            reply_markup=get_after_check_kb(),
        )
    finally:
        await bot.session.close()
