from aiogram import Dispatcher

from .auth import AuthMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.message.outer_middleware(AuthMiddleware())
    dp.callback_query.outer_middleware(AuthMiddleware())
