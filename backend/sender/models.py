from django.db import models
from django.utils import timezone


class Broadcast(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Запланировано"
        SENT = "SENT", "Отправлено"
        ERROR = "ERROR", "Ошибка"
        CANCELED = "CANCELED", "Отменена"

    class MediaType(models.TextChoices):
        PHOTO = "PHOTO", "Фото"
        VIDEO = "VIDEO", "Видео"
        DOCUMENT = "DOCUMENT", "Документ"
        AUDIO = "AUDIO", "Аудио"

    text = models.TextField(
        verbose_name="Текст сообщения",
        help_text="Основной текст рассылки. Будет отправлен как есть или как подпись к медиафайлу.",
    )
    media_file = models.FileField(
        upload_to="broadcasts/",
        blank=True,
        null=True,
        verbose_name="Медиафайл",
        help_text="Опциональный файл для отправки (фото, видео, документ, аудио).",
    )
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        blank=True,
        null=True,
        verbose_name="Тип медиафайла",
        help_text="Необходимо указать тип, если вы прикрепили медиафайл.",
    )
    scheduled_at = models.DateTimeField(
        verbose_name="Запланированное время отправки",
        help_text="Укажите дату и время, когда рассылка должна быть отправлена.",
        default=timezone.now,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID задачи Celery",
        editable=False,
    )

    def __str__(self):
        return f"Рассылка от {self.scheduled_at.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-scheduled_at"]
