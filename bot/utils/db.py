from asgiref.sync import sync_to_async
from django.db.models import Exists, OuterRef
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_valid_number

from backend.checker.models import Check
from backend.content.models import FAQ, BotTexts, SiteSettings
from backend.courses.models import (
    Course,
    DifficultyLevel,
    Module,
    Task,
    UserTaskStatus,
)
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


@sync_to_async
def get_user_courses(user_id: int):
    return list(
        Course.objects.filter(user_accesses__user_id=user_id).values_list("id", "title")
    )


@sync_to_async
def get_course_modules(course_id: int, user_id: int):
    return list(
        Module.objects.filter(
            course_id=course_id, course__user_accesses__user_id=user_id
        )
        .order_by("order")
        .values_list("id", "title")
    )


@sync_to_async
def get_module_levels(module_id: int, user_id: int):
    return list(
        DifficultyLevel.objects.filter(
            module_id=module_id, module__course__user_accesses__user_id=user_id
        )
        .order_by("order")
        .values_list("id", "title")
    )


@sync_to_async
def get_level_tasks(level_id: int, user_id: int):
    solved_subquery = UserTaskStatus.objects.filter(
        task=OuterRef("pk"),
        user_id=user_id,
        status=UserTaskStatus.Status.SOLVED,
    )

    tasks = (
        Task.objects.filter(
            level_id=level_id, level__module__course__user_accesses__user_id=user_id
        )
        .annotate(is_solved=Exists(solved_subquery))
        .order_by("number")
        .values("id", "number", "title", "is_solved")
    )
    return list(tasks)


@sync_to_async
def get_task_details(task_id: int, user_id: int):
    try:
        return Task.objects.select_related("level__module__course").get(
            id=task_id, level__module__course__user_accesses__user_id=user_id
        )
    except Task.DoesNotExist:
        return None


@sync_to_async
def get_user_task_status(user_id: int, task_id: int):
    try:
        return UserTaskStatus.objects.get(user_id=user_id, task_id=task_id)
    except UserTaskStatus.DoesNotExist:
        return None


@sync_to_async
def get_check_for_feedback(check_id: int, user_id: int):
    try:
        check = Check.objects.select_related("task__level__module__course").get(
            id=check_id,
            user_id=user_id,
            task__level__module__course__user_accesses__user_id=user_id,
        )
        return check, check.task
    except Check.DoesNotExist:
        return None, None
