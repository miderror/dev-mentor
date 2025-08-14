import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.core.settings")
import django

django.setup()

from django.conf import settings

from bot.handlers import setup_handlers
from bot.middlewares import setup_middlewares


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = RedisStorage.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_CELERY}"
    )
    dp = Dispatcher(storage=storage)

    setup_middlewares(dp)
    setup_handlers(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
