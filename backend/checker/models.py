from django.db import models

from backend.courses.models import Task
from backend.users.models import User


class Check(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "В ожидании"
        RUNNING = "RUNNING", "Выполняется"
        SUCCESS = "SUCCESS", "Успешно"
        ERROR = "ERROR", "Ошибка"
        TIMEOUT = "TIMEOUT", "Тайм-аут"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="checks",
        verbose_name="Пользователь",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checks",
        verbose_name="Задача",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    code = models.TextField(verbose_name="Исходный код")
    stdout = models.TextField(
        blank=True, null=True, verbose_name="Стандартный вывод (stdout)"
    )
    stderr = models.TextField(
        blank=True, null=True, verbose_name="Стандартная ошибка (stderr)"
    )
    ai_suggestion = models.TextField(
        blank=True, null=True, verbose_name="Рекомендация от AI"
    )
    ai_response_ms = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Время ответа AI (мс)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self):
        return f"Проверка #{self.id} от {self.user.username or self.user.telegram_id}"

    class Meta:
        verbose_name = "Проверка кода"
        verbose_name_plural = "Проверки кода"
        ordering = ["-created_at"]


class CommonError(models.Model):
    error_pattern = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Шаблон ошибки (regex)",
        help_text="Регулярное выражение для поиска в stderr.",
    )
    title = models.CharField(max_length=255, verbose_name="Причина ошибки")
    description = models.TextField(verbose_name="Описание и решение")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Типовая ошибка"
        verbose_name_plural = "Реестр типовых ошибок"
