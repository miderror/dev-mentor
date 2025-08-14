import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import FSInputFile
from asgiref.sync import sync_to_async
from celery import shared_task
from django.conf import settings

from backend.users.models import User, Whitelist

from .models import Broadcast

logger = logging.getLogger(__name__)


async def send_message_to_user(bot: Bot, user: User, broadcast: Broadcast):
    try:
        if broadcast.media_file and broadcast.media_type:
            file = FSInputFile(broadcast.media_file.path)
            media_type = broadcast.media_type

            if media_type == Broadcast.MediaType.PHOTO:
                await bot.send_photo(user.telegram_id, file, caption=broadcast.text)
            elif media_type == Broadcast.MediaType.VIDEO:
                await bot.send_video(user.telegram_id, file, caption=broadcast.text)
            elif media_type == Broadcast.MediaType.DOCUMENT:
                await bot.send_document(user.telegram_id, file, caption=broadcast.text)
            elif media_type == Broadcast.MediaType.AUDIO:
                await bot.send_audio(user.telegram_id, file, caption=broadcast.text)
        else:
            await bot.send_message(user.telegram_id, broadcast.text)

        logger.info(f"Сообщение успешно отправлено пользователю {user.telegram_id}")
        return True
    except TelegramForbiddenError as e:
        logger.warning(
            f"Не удалось отправить сообщение пользователю {user.telegram_id} (т.к. заблочил/удалил бота): {e}"
        )
        return True
    except TelegramAPIError as e:
        logger.error(
            f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}"
        )
        return False


async def run_broadcast(broadcast_id: int):
    try:
        broadcast = await Broadcast.objects.aget(id=broadcast_id)

        whitelisted_phones = Whitelist.objects.values_list("phone_number", flat=True)
        users_to_send = await sync_to_async(list)(
            User.objects.filter(phone_number__in=whitelisted_phones)
        )

        if not users_to_send:
            logger.warning(f"Рассылка {broadcast_id}: нет пользователей для отправки.")
            broadcast.status = Broadcast.Status.ERROR
            await broadcast.asave(update_fields=["status"])
            return

        bot = Bot(token=settings.BOT_TOKEN, default=None)

        tasks = [send_message_to_user(bot, user, broadcast) for user in users_to_send]
        results = await asyncio.gather(*tasks)

        await bot.session.close()

        if all(results):
            broadcast.status = Broadcast.Status.SENT
        else:
            broadcast.status = Broadcast.Status.ERROR

        await broadcast.asave(update_fields=["status"])
        logger.info(
            f"Рассылка {broadcast_id} завершена со статусом {broadcast.status}."
        )

    except Broadcast.DoesNotExist:
        logger.error(f"Рассылка с ID {broadcast_id} не найдена.")
    except Exception as e:
        logger.exception(
            f"Критическая ошибка при выполнении рассылки {broadcast_id}: {e}"
        )
        try:
            broadcast = await Broadcast.objects.aget(id=broadcast_id)
            broadcast.status = Broadcast.Status.ERROR
            await broadcast.asave(update_fields=["status"])
        except Broadcast.DoesNotExist:
            pass


@shared_task
def send_broadcast_task(broadcast_id: int):
    logger.info(f"Запуск задачи рассылки для ID: {broadcast_id}")
    asyncio.run(run_broadcast(broadcast_id))
