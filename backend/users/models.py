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
    courses = models.ManyToManyField(
        "courses.Course",
        blank=True,
        related_name="whitelisted_phones",
        verbose_name="Доступные курсы",
        help_text="Выберите курсы, к которым будет предоставлен доступ по этому номеру.",
    )

    def __str__(self):
        return str(self.phone_number)

    class Meta:
        verbose_name = "Запись в белом списке"
        verbose_name_plural = "Белый список"


class CourseAccess(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_accesses",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="user_accesses",
        verbose_name="Курс",
    )

    def __str__(self):
        return f"Доступ для {self.user} к курсу '{self.course}'"

    class Meta:
        verbose_name = "Доступ к курсу"
        verbose_name_plural = "Доступы к курсам"
        unique_together = ("user", "course")
