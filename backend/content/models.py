# backend/content/models.py
from django.db import models


class SiteSettings(models.Model):
    support_link = models.URLField(
        max_length=200,
        verbose_name="Ссылка на тех. поддержку",
        help_text="URL-адрес на чат поддержки.",
        default="https://t.me/your_support_username",
    )

    def __str__(self):
        return "Тех. поддержка"

    class Meta:
        verbose_name = "Тех. поддержка"
        verbose_name_plural = "Тех. поддержка"


class FAQ(models.Model):
    class MediaType(models.TextChoices):
        PHOTO = "PHOTO", "Фото"
        VIDEO = "VIDEO", "Видео"
        DOCUMENT = "DOCUMENT", "Документ"
        AUDIO = "AUDIO", "Аудио"

    question = models.CharField(
        max_length=255, verbose_name="Вопрос", help_text="Краткий текст вопроса."
    )
    answer = models.TextField(verbose_name="Ответ", help_text="Полный текст ответа.")
    media_file = models.FileField(
        upload_to="faq_media/",
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
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Чем меньше число, тем выше в списке будет вопрос.",
    )

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["order", "question"]
