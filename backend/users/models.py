from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(models.Model):
    telegram_id = models.BigIntegerField(
        unique=True, primary_key=True, verbose_name="Телеграм ID"
    )
    username = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Юзернейм"
    )
    phone_number = PhoneNumberField(
        null=True, blank=True, verbose_name="Номер телефона"
    )
    checks_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество проверок кода"
    )
    successful_checks_count = models.PositiveIntegerField(
        default=0, verbose_name="Успешных проверок"
    )
    failed_checks_count = models.PositiveIntegerField(
        default=0, verbose_name="Неуспешных проверок"
    )
    last_activity_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Последняя активность"
    )
    date_joined = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )

    def __str__(self):
        return f"id: {str(self.telegram_id)}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Whitelist(models.Model):
    phone_number = PhoneNumberField(unique=True, verbose_name="Номер телефона")

    def __str__(self):
        return str(self.phone_number)

    class Meta:
        verbose_name = "Белый список"
        verbose_name_plural = "Белый список"
