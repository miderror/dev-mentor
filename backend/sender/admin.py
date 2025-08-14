from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from backend.core.celery import app as celery_app

from .models import Broadcast
from .tasks import send_broadcast_task


def schedule_broadcast_task(broadcast: Broadcast):
    task = send_broadcast_task.apply_async(
        args=[broadcast.id], eta=broadcast.scheduled_at
    )
    Broadcast.objects.filter(pk=broadcast.pk).update(task_id=task.id)


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_text",
        "scheduled_at",
        "status_colored",
        "media_type",
        "actions_column",
    )
    list_filter = ("status", "media_type", "scheduled_at")
    search_fields = ("text",)
    ordering = ("-scheduled_at",)

    readonly_fields = ("status", "task_id")

    fieldsets = (
        (
            "Содержимое рассылки",
            {
                "fields": ("text", ("media_file", "media_type")),
                "description": "Заполните текст и, при необходимости, прикрепите медиафайл.",
            },
        ),
        (
            "Планирование и Статус",
            {
                "fields": ("scheduled_at", "status"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("status",)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != Broadcast.Status.SCHEDULED:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def save_model(self, request, obj: Broadcast, form, change):
        if obj.media_file and not obj.media_type:
            messages.error(
                request, "Если вы загрузили файл, необходимо указать его тип."
            )
            return

        if change and obj.task_id:
            celery_app.control.revoke(obj.task_id, terminate=True)
            messages.info(
                request, f"Старая запланированная задача {obj.task_id} отменена."
            )

        obj.status = Broadcast.Status.SCHEDULED
        super().save_model(request, obj, form, change)

        transaction.on_commit(lambda: schedule_broadcast_task(obj))

        self.message_user(
            request,
            f"Рассылка запланирована на {obj.scheduled_at.strftime('%d.%m.%Y %H:%M')}",
            messages.SUCCESS,
        )

    @admin.display(description="Текст", ordering="text")
    def short_text(self, obj: Broadcast):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    @admin.display(description="Статус", ordering="status")
    def status_colored(self, obj: Broadcast):
        colors = {
            Broadcast.Status.SCHEDULED: "teal",
            Broadcast.Status.SENT: "green",
            Broadcast.Status.ERROR: "red",
            Broadcast.Status.CANCELED: "gray",
        }
        return format_html(
            '<b style="color: {};">{}</b>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    @admin.display(description="Действия")
    def actions_column(self, obj):
        if obj.status == Broadcast.Status.SCHEDULED:
            cancel_url = reverse("admin:sender_broadcast_cancel", args=[obj.pk])
            return format_html('<a class="button" href="{}">Отменить</a>', cancel_url)
        return "—"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/cancel/",
                self.admin_site.admin_view(self.process_cancel),
                name="sender_broadcast_cancel",
            )
        ]
        return custom_urls + urls

    def process_cancel(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)
        if obj and obj.task_id and obj.status == Broadcast.Status.SCHEDULED:
            celery_app.control.revoke(obj.task_id, terminate=True)
            obj.status = Broadcast.Status.CANCELED
            obj.save()
            self.message_user(request, f"Рассылка {obj.id} отменена.", messages.WARNING)
        else:
            self.message_user(
                request, "Невозможно отменить эту рассылку.", messages.ERROR
            )

        return HttpResponseRedirect(reverse("admin:sender_broadcast_changelist"))
