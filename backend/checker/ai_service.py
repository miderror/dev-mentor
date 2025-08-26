import logging
import os
import time
from textwrap import dedent

import httpx

from backend.courses.models import Task

from .models import Check

logger = logging.getLogger(__name__)
AI_API_KEY = os.getenv("AI_API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME")


def _get_prompt_for_success(task_description: str, user_code: str) -> tuple[str, str]:
    system_prompt = "Ты - робот, проводящий код-ревью Python кода. Ты СТРОГО следуешь формату. Ты НЕ ДОБАВЛЯЕШЬ лишних слов. Ты отвечаешь ТОЛЬКО на русском."

    part_1 = dedent("""
        ИНСТРУКЦИЯ: Проанализируй КОД и ОПИСАНИЕ ЗАДАЧИ КОТОРУЮ РЕШАЕТ КОД после ТВОЯ ЗАДАЧА. Предоставь ТОЛЬКО ТВОЙ ВЫВОД в формате MarkdownV2, точно следуя ШАБЛОНУ ВЫВОДА из ПРИМЕР.
        ВСЕ ОСТАЛЬНЫЕ спецсимволы (например, `.`, `!`, `-`, `(`, `)`) ты ОБЯЗАН экранировать обратным слэшем `\` ЕСЛИ ОНИ НЕ В БЛОКЕ КОДА.
        
        ---
        ПРИМЕР (ШАБЛОН ВЫВОДА ДО --- НЕВКЛЮЧИТЕЛЬНО):
        👍 **Отличное решение!**
        Все тесты пройдены, и задача решена корректно. Поздравляю!

        💡 **Что можно улучшить?**
        Твой код использует два вложенных цикла для поиска дубликатов. Это рабочий подход, но представь, что в списке будет миллион элементов! Программа будет делать огромное количество лишних сравнений, и ее выполнение займет очень много времени.

        Более быстрый способ — использовать структуру данных `set` (множество), которая хранит только уникальные элементы.

        Вот оптимизированный вариант:
        ```python
        def has_duplicates_optimized(nums):
            seen = set()
            for num in nums:
                if num in seen:
                    return True
                seen.add(num)
            return False
        ```

        ---
        
        ТВОЯ ЗАДАЧА:

        КОД:
        ```python
    """)

    part_2 = dedent("""
        ```
        
        ОПИСАНИЕ ЗАДАЧИ КОТОРУЮ РЕШАЕТ КОД:
        ```python
    """)

    part_3 = dedent("""
        ```

        ТВОЙ ВЫВОД (Используй ШАБЛОН ВЫВОДА из ПРИМЕР):
    """)

    user_prompt = f"{part_1}\n{user_code}\n{part_2}\n{task_description}\n{part_3}"
    return system_prompt, user_prompt


def _get_prompt_for_runtime_error(
    user_code: str, error_traceback: str
) -> tuple[str, str]:
    system_prompt = "Ты - робот, который исправляет Python код. Ты СТРОГО следуешь формату. Ты НЕ ДОБАВЛЯЕШЬ лишних слов. Ты отвечаешь ТОЛЬКО на русском."

    part_1 = dedent("""
        ИНСТРУКЦИЯ: Проанализируй КОД и ОШИБКУ после ТВОЯ ЗАДАЧА. Предоставь ТОЛЬКО ТВОЙ ВЫВОД в формате MarkdownV2, точно следуя ШАБЛОНУ ВЫВОДА из ПРИМЕР.
            ВСЕ ОСТАЛЬНЫЕ спецсимволы (например, `.`, `!`, `-`, `(`, `)`) ты ОБЯЗАН экранировать обратным слэшем `\` ЕСЛИ ОНИ НЕ В БЛОКЕ КОДА.
        
        ---
        ПРИМЕР (ШАБЛОН ВЫВОДА ДО --- НЕВКЛЮЧИТЕЛЬНО):
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
    return system_prompt, user_prompt


def _get_prompt_for_wrong_answer(
    task_description: str, user_code: str, test_input: str, expected: str, actual: str
) -> str:
    system_prompt = "Ты - умный отладчик кода на Python. Ты СТРОГО следуешь формату. Ты НЕ ДОБАВЯЕШЬ лишних слов. Ты отвечаешь ТОЛЬКО на русском."

    part_1 = dedent("""
        ИНСТРУКЦИЯ: Проанализируй КОД и ОПИСАНИЕ ЗАДАЧИ КОТОРУЮ ДОЛЖЕН РЕШАТЬ КОД и ДЕТАЛИ ПРОВАЛЕННОГО ТЕСТА после ТВОЯ ЗАДАЧА. Предоставь ТОЛЬКО ТВОЙ ВЫВОД в формате MarkdownV2, точно следуя ШАБЛОНУ ВЫВОДА из ПРИМЕР.
        ВСЕ ОСТАЛЬНЫЕ спецсимволы (например, `.`, `!`, `-`, `(`, `)`) ты ОБЯЗАН экранировать обратным слэшем `\` ЕСЛИ ОНИ НЕ В БЛОКЕ КОДА.
        
        ---
        ПРИМЕР (ШАБЛОН ВЫВОДА ДО --- НЕВКЛЮЧИТЕЛЬН):
        🤔 **В чем может быть ошибка?**
        Твой алгоритм `s == s[::-1]` напрямую сравнивает строку `А роза упала на лапу Азора` с её перевернутой версией, которая выглядит как `азорА упал ан алапу азор А`. Из-за разницы в регистре (`А` vs `а`) и пробелов, они не равны, и код возвращает `False`.
        
        🎯 **Подсказка для исправления**
        Перед тем, как сравнивать строку с её перевернутой копией, её нужно "нормализовать".

        Подумай, какие два метода для строк в Python помогут тебе:
        1.  Превратить все буквы в строчные?
        2.  Удалить все пробелы из строки?

        Примени их к строке `s` **перед** сравнением, и всё получится!

        ---
        
        ТВОЯ ЗАДАЧА:

        КОД:
        ```python
    """)

    part_2 = dedent("""
        ```
        
        ОПИСАНИЕ ЗАДАЧИ КОТОРУЮ ДОЛЖЕН РЕШАТЬ КОД:
        ```python
    """)

    part_3 = dedent(f"""
        ```
        ДЕТАЛИ ПРОВАЛЕННОГО ТЕСТА:
        - Входные данные (`input`): `{test_input}`
        - Ожидаемый результат (`expected`): `{expected}`
        - Фактический результат, который выдал код (`actual`):
        ```
    """)

    part_4 = dedent("""
        ```

        ТВОЙ ВЫВОД (Используй ШАБЛОН ВЫВОДА из ПРИМЕР):
    """)

    user_prompt = f"{part_1}\n{user_code}\n{part_2}\n{task_description}\n{part_3}\n{actual}\n{part_4}"

    return system_prompt, user_prompt


async def _call_ai_api(
    user_prompt: str, system_prompt: str = "Ты — полезный ассистент на русском по коду."
) -> tuple[str, int]:
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
        "temperature": 0.2,
        "max_tokens": 1500,
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
        ai_response = "Не удалось связаться с сервисом AI."
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse AI response: {e}. Response data: {data}")
        ai_response = "Получен некорректный ответ от сервиса AI."
    end_time = time.monotonic()
    duration_ms = int((end_time - start_time) * 1000)
    return ai_response, duration_ms


async def get_ai_suggestion(check: Check, task: Task) -> tuple[str, int]:
    system_prompt, user_prompt = "", ""
    if check.status == Check.Status.SUCCESS:
        system_prompt, user_prompt = _get_prompt_for_success(
            task.description, check.code
        )

    elif check.status == Check.Status.ERROR:
        if check.stderr:
            system_prompt, user_prompt = _get_prompt_for_runtime_error(
                check.code, check.stderr
            )
        elif check.error_context:
            context = check.error_context
            system_prompt, user_prompt = _get_prompt_for_wrong_answer(
                task.description,
                check.code,
                context.get("input", "неизвестно"),
                context.get("expected", "неизвестно"),
                check.stdout,
            )

    if not user_prompt:
        return "Не удалось определить сценарий для анализа. Обратитесь в поддержку.", 0

    return await _call_ai_api(user_prompt=user_prompt, system_prompt=system_prompt)
