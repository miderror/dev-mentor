from django.db import models

from backend.users.models import User


class Course(models.Model):
    title = models.CharField(max_length=200, unique=True, verbose_name="Название курса")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["title"]


class Module(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="modules", verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Название модуля")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        unique_together = ("course", "title")
        ordering = ["course", "order", "title"]


class DifficultyLevel(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="levels",
        verbose_name="Модуль",
    )
    title = models.CharField(max_length=50, verbose_name="Уровень сложности")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return f"{self.module} - {self.title}"

    class Meta:
        verbose_name = "Уровень сложности"
        verbose_name_plural = "Уровни сложности"
        unique_together = ("module", "title")
        ordering = ["module", "order", "title"]


def get_default_task_tests():
    return {
        "tests": [
            {"input": ["test_input"], "expected": "test_output"},
        ]
    }


class Task(models.Model):
    level = models.ForeignKey(
        DifficultyLevel,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Уровень",
    )
    number = models.PositiveIntegerField(verbose_name="Номер задачи")
    title = models.CharField(max_length=255, verbose_name="Название задачи")
    description = models.TextField(
        verbose_name="Описание задачи (Markdown)",
        help_text="Поддерживает форматирование Markdown для отображения в боте.",
    )
    image = models.ImageField(
        upload_to="tasks_images/",
        blank=True,
        null=True,
        verbose_name="Изображение к задаче",
        help_text="Опциональное изображение, которое будет показано вместе с описанием.",
    )
    tests = models.JSONField(
        verbose_name="Проверочные тесты (JSON)",
        help_text='JSON-объект со списком тестов. Формат: {"tests": [{"input": [...], "expected": ...}]}',
        default=get_default_task_tests,
    )

    def __str__(self):
        return f"#{self.number}. {self.title}"

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        unique_together = ("level", "number")
        ordering = ["level", "number"]


class UserTaskStatus(models.Model):
    class Status(models.TextChoices):
        NOT_ATTEMPTED = "NOT_ATTEMPTED", "Не решена"
        SOLVED = "SOLVED", "Решена"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="task_statuses",
        verbose_name="Пользователь",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="user_statuses",
        verbose_name="Задача",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_ATTEMPTED,
        verbose_name="Статус",
    )
    solved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Время решения"
    )

    def __str__(self):
        return f"{self.user} - {self.task.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Статус решения задачи"
        verbose_name_plural = "Статусы решений задач"
        unique_together = ("user", "task")
