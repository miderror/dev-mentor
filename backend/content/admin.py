from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import FAQ, BotTexts, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse("admin:content_sitesettings_change", args=(obj.pk,))
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "media_type")
    list_editable = ("order",)
    search_fields = ("question", "answer")
    list_filter = ("media_type",)


@admin.register(BotTexts)
class BotTextsAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse("admin:content_bottexts_change", args=(obj.pk,))
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
