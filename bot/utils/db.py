from asgiref.sync import sync_to_async
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_valid_number

from backend.content.models import FAQ, BotTexts, SiteSettings
from backend.users.models import User, Whitelist


@sync_to_async
def register_user(telegram_id: int, username: str | None, phone_number_str: str):
    phone_number = to_python(phone_number_str)
    if not is_valid_number(phone_number):
        return None, "Некорректный формат номера телефона."

    user, created = User.objects.update_or_create(
        telegram_id=telegram_id,
        defaults={"username": username, "phone_number": phone_number},
    )
    status = (
        "Вы успешно зарегистрированы!" if created else "Ваш номер телефона обновлен."
    )
    return user, status


@sync_to_async
def is_whitelisted(phone_number):
    if not phone_number:
        return False
    return Whitelist.objects.filter(phone_number=phone_number).exists()


@sync_to_async
def get_user_and_check_whitelist(telegram_id: int):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        if not user.phone_number:
            return user, False

        allowed = Whitelist.objects.filter(phone_number=user.phone_number).exists()
        return user, allowed
    except User.DoesNotExist:
        return None, False


@sync_to_async
def get_support_link():
    settings, _ = SiteSettings.objects.get_or_create(pk=1)
    return settings.support_link


@sync_to_async
def get_faq_list():
    return list(FAQ.objects.values_list("id", "question"))


@sync_to_async
def get_faq_item(faq_id: int):
    try:
        return FAQ.objects.get(id=faq_id)
    except FAQ.DoesNotExist:
        return None


@sync_to_async
def get_bot_texts():
    texts, _ = BotTexts.objects.get_or_create(pk=1)
    return texts
