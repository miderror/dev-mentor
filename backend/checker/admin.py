import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Check


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__telegram_id")

    @admin.display(description="Пользователь", ordering="user")
    def user_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>', url, obj.user.username or obj.user.telegram_id
        )

    fieldsets = (
        ("Основная информация", {"fields": ("user", "status", "created_at")}),
        (
            "Исходный код",
            {
                "classes": ("collapse",),
                "fields": ("formatted_code",),
            },
        ),
        (
            "Стандартный вывод (stdout)",
            {
                "classes": ("collapse",),
                "fields": ("formatted_stdout",),
            },
        ),
        (
            "Стандартная ошибка (stderr)",
            {
                "classes": ("collapse",),
                "fields": ("formatted_stderr",),
            },
        ),
        (
            "Контекст ошибки (если неверный ответ)",
            {"classes": ("collapse",), "fields": ("formatted_error_context",)},
        ),
        (
            "Анализ AI",
            {
                "classes": ("collapse",),
                "fields": ("formatted_ai_suggestion", "ai_response_seconds"),
            },
        ),
    )

    readonly_fields = (
        "user",
        "status",
        "created_at",
        "formatted_code",
        "formatted_stdout",
        "formatted_stderr",
        "formatted_error_context",
        "formatted_ai_suggestion",
        "ai_response_seconds",
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Контекст ошибки")
    def formatted_error_context(self, obj: Check):
        if not obj.error_context:
            return "—"
        formatted_json = json.dumps(obj.error_context, indent=2, ensure_ascii=False)
        return format_html("<pre>{}</pre>", formatted_json)

    @admin.display(description="Время ответа AI (сек)", ordering="ai_response_ms")
    def ai_response_seconds(self, obj: Check):
        if obj.ai_response_ms is None:
            return "—"
        seconds = round(obj.ai_response_ms / 1000, 2)
        return f"{seconds} сек."

    @admin.display(description="Исходный код")
    def formatted_code(self, obj: Check):
        return format_html("<pre>{}</pre>", obj.code)

    @admin.display(description="Стандартный вывод (stdout)")
    def formatted_stdout(self, obj: Check):
        if not obj.stdout:
            return "—"
        return format_html("<pre>{}</pre>", obj.stdout)

    @admin.display(description="Стандартная ошибка (stderr)")
    def formatted_stderr(self, obj: Check):
        if not obj.stderr:
            return "—"
        return format_html("<pre>{}</pre>", obj.stderr)

    @admin.display(description="Рекомендация от AI")
    def formatted_ai_suggestion(self, obj: Check):
        if not obj.ai_suggestion:
            return "—"
        return format_html("<div>{}</div>", obj.ai_suggestion)
