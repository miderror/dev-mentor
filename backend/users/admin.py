# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User as AuthUser
from django.urls import reverse
from django.utils.html import format_html

from .models import User, Whitelist


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id",
        "username",
        "phone_number",
        "checks_count",
        "successful_checks_count",
        "failed_checks_count",
        "last_activity_at",
        "view_checks_link",
    )
    search_fields = ("telegram_id", "username", "phone_number")
    list_filter = ("last_activity_at", "date_joined")
    readonly_fields = (
        "telegram_id",
        "username",
        "phone_number",
        "date_joined",
        "checks_count",
        "successful_checks_count",
        "failed_checks_count",
        "last_activity_at",
    )

    fieldsets = (
        ("Контактная информация", {"fields": ("telegram_id", "username", "phone_number")}),
        (
            "Статистика активности",
            {
                "fields": (
                    "date_joined",
                    "last_activity_at",
                    "checks_count",
                    ("successful_checks_count", "failed_checks_count"),
                )
            },
        ),
    )

    @admin.display(description="Проверки кода")
    def view_checks_link(self, obj):
        if obj.checks_count > 0:
            url = (
                reverse("admin:checker_check_changelist")
                + f"?user__telegram_id__exact={obj.telegram_id}"
            )
            return format_html('<a href="{}">Смотреть ({})</a>', url, obj.checks_count)
        return "Нет проверок"


@admin.register(Whitelist)
class WhitelistAdmin(admin.ModelAdmin):
    list_display = ("phone_number",)
    search_fields = ("phone_number",)


admin.site.unregister(AuthUser)
admin.site.unregister(Group)