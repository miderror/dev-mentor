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


class BotTexts(models.Model):
    welcome_message = models.TextField(
        verbose_name="Приветственное сообщение",
        default="Привет! Я бот для проверки python-кода. Отправь мне свой код, и я скажу, есть ли в нем ошибки и как их решить.",
        help_text="Отображается после успешной авторизации.",
    )
    request_contact_message = models.TextField(
        verbose_name="Запрос номера телефона",
        default="Здравствуйте! Для использования бота, пожалуйста, подтвердите свой номер телефона.",
        help_text="Первое сообщение пользователю при команде /start, если он не авторизован.",
    )

    already_authorized_message = models.TextField(
        verbose_name="Сообщение для уже авторизованных",
        default="Вы уже авторизованы.",
        help_text="Когда пользователь с контактом пытается снова отправить контакт.",
    )
    whitelist_success_message = models.TextField(
        verbose_name="Успешная проверка в белом списке",
        default="Ваш номер подтвержден и есть в списке. Добро пожаловать!",
        help_text="Сообщение после успешной сверки номера с белым списком.",
    )
    whitelist_fail_message = models.TextField(
        verbose_name="Неуспешная проверка в белом списке",
        default="К сожалению, вашего номера нет в белом списке. Доступ запрещен.",
        help_text="Сообщение, если номера пользователя нет в белом списке.",
    )

    main_menu_message = models.TextField(
        verbose_name="Сообщение главного меню",
        default="Вы в главном меню.",
        help_text="Текст, который видит пользователь в главном меню.",
    )
    menu_return_message = models.TextField(
        verbose_name="Сообщение о возврате в меню",
        default="Вы вернулись в главное меню.",
        help_text="Отображается при нажатии на кнопку 'Вернуться в меню'.",
    )

    request_code_message = models.TextField(
        verbose_name="Запрос кода для проверки",
        default="Отправьте мне свой python-код текстом или файлом (.txt, .py, .docx).",
        help_text="Сообщение после нажатия кнопки 'Проверить код'.",
    )

    code_in_review_message = models.TextField(
        verbose_name="Сообщение о принятии кода на проверку",
        default="Код получен и отправлен на проверку. Это может занять несколько минут. Ожидайте...",
        help_text="Сообщение сразу после того, как пользователь отправил код.",
    )

    faq_list_title = models.TextField(
        verbose_name="Заголовок списка FAQ",
        default="Часто задаваемые вопросы:",
        help_text="Текст, который отображается над списком вопросов в разделе FAQ."
    )

    def __str__(self):
        return "Тексты бота"

    class Meta:
        verbose_name = "Тексты бота"
        verbose_name_plural = "Тексты бота"
