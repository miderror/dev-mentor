from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from ..utils.db import get_user_and_check_whitelist


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user, is_allowed = await get_user_and_check_whitelist(event.from_user.id)
        if not is_allowed and not isinstance(event, Message):
            return

        if not user:
            if event.text and event.text.startswith("/start") or event.contact:
                return await handler(event, data)

            await event.answer(
                "Вы не зарегистрированы. Пожалуйста, отправьте команду /start и поделитесь номером",
            )
            return

        if not is_allowed:
            await event.answer(
                "Отказано в доступе",
            )
            return

        data["user"] = user
        return await handler(event, data)
