from aiogram import Dispatcher

from .checker import router as checker_router
from .courses import router as courses_router
from .faq import router as faq_router
from .menu import router as menu_router
from .start import router as start_router


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_routers(
        start_router,
        menu_router,
        courses_router,
        faq_router,
        checker_router,
    )
