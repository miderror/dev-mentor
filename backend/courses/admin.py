from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from jsoneditor.forms import JSONEditor

from .models import Course, DifficultyLevel, Module, Task


class TaskAdminForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"

    def clean_tests(self):
        data = self.cleaned_data.get("tests")

        if not isinstance(data, dict):
            raise forms.ValidationError("Тесты должны быть JSON-объектом (словарем).")

        if "tests" not in data:
            raise forms.ValidationError("В JSON должен быть ключ 'tests'.")

        if not isinstance(data["tests"], list):
            raise forms.ValidationError("Значение ключа 'tests' должно быть списком.")

        if not data["tests"]:
            raise forms.ValidationError("Список 'tests' не может быть пустым.")

        for i, test in enumerate(data["tests"], 1):
            if not isinstance(test, dict):
                raise forms.ValidationError(
                    f"Элемент #{i} в списке 'tests' должен быть объектом."
                )
            if "input" not in test or "expected" not in test:
                raise forms.ValidationError(
                    f"В тесте #{i} отсутствуют обязательные ключи 'input' или 'expected'."
                )
            if not isinstance(test["input"], list):
                raise forms.ValidationError(
                    f"В тесте #{i} значение 'input' должно быть списком."
                )

        return data


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    ordering = ("order", "title")
    fields = ("title", "order", "edit_link")
    readonly_fields = ("edit_link",)

    @admin.display(description="Редактировать")
    def edit_link(self, obj):
        if obj.pk:
            url = reverse("admin:courses_module_change", args=[obj.pk])
            return format_html('<a href="{}">Перейти ➔</a>', url)
        return "Сначала сохраните"


class DifficultyLevelInline(admin.TabularInline):
    model = DifficultyLevel
    extra = 1
    ordering = ("order", "title")
    fields = ("title", "order", "edit_link")
    readonly_fields = ("edit_link",)

    @admin.display(description="Редактировать")
    def edit_link(self, obj):
        if obj.pk:
            url = reverse("admin:courses_difficultylevel_change", args=[obj.pk])
            return format_html('<a href="{}">Перейти ➔</a>', url)
        return "Сначала сохраните"


class TaskInline(admin.TabularInline):
    model = Task
    fields = ("number", "title", "edit_link")
    readonly_fields = (
        "number",
        "title",
        "edit_link",
    )
    ordering = ("number",)

    extra = 0
    max_num = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Редактировать")
    def edit_link(self, obj):
        if obj.pk:
            url = reverse("admin:courses_task_change", args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Открыть ➔</a>', url)
        return "—"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    admin_order = 1
    list_display = ("title",)
    search_fields = ("title",)
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    admin_order = 2
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    list_editable = ("order",)
    inlines = [DifficultyLevelInline]
    list_select_related = ("course",)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        course_id = request.GET.get("course__id__exact")
        if course_id:
            initial["course"] = course_id
        return initial


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    admin_order = 3
    list_display = ("title", "get_course", "get_module_title", "order")
    list_filter = ("module__course", "module")
    search_fields = ("title", "module__title")
    list_editable = ("order",)
    inlines = [TaskInline]
    autocomplete_fields = ("module",)
    list_select_related = ("module__course",)

    readonly_fields = ("add_task_link",)

    fieldsets = (
        (None, {"fields": ("module", "title", "order")}),
        (
            "Задачи этого уровня",
            {
                "fields": ("add_task_link",),
                "description": "Нажмите на ссылку ниже, чтобы добавить новую задачу. "
                "После сохранения она появится в списке выше.",
            },
        ),
    )

    @admin.display(description="Добавить задачу")
    def add_task_link(self, obj):
        add_url = reverse("admin:courses_task_add")
        params = urlencode({"level": obj.pk})
        full_url = f"{add_url}?{params}"
        return format_html(
            '<a href="{}" class="button" target="_blank">✚ Добавить новую задачу</a>',
            full_url,
        )

    @admin.display(description="Курс", ordering="module__course")
    def get_course(self, obj):
        return obj.module.course

    @admin.display(description="Модуль", ordering="module__title")
    def get_module_title(self, obj):
        return obj.module.title

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        module_id = request.GET.get("module__id__exact")
        if module_id:
            initial["module"] = module_id
        return initial


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    admin_order = 4
    form = TaskAdminForm
    list_display = (
        "number",
        "title",
        "get_level_title",
        "get_module_title",
        "get_course_title",
    )
    list_filter = ("level__module__course", "level__module", "level")
    search_fields = ("title", "description")
    ordering = ("level__module__course", "level__module", "level", "number")
    autocomplete_fields = ("level",)
    list_select_related = ("level__module__course",)

    formfield_overrides = {
        models.JSONField: {
            "widget": JSONEditor(
                init_options={
                    "mode": "code",
                    "modes": ["code", "tree", "view"],
                },
            )
        },
    }

    fieldsets = (
        ("Основная информация", {"fields": ("level", "number", "title")}),
        ("Содержание задачи", {"fields": ("description", "image", "tests")}),
    )

    @admin.display(description="Уровень", ordering="level__title")
    def get_level_title(self, obj):
        return obj.level.title

    @admin.display(description="Модуль", ordering="level__module__title")
    def get_module_title(self, obj):
        return obj.level.module.title

    @admin.display(description="Курс", ordering="level__module__course__title")
    def get_course_title(self, obj):
        return obj.level.module.course.title

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        level_id = request.GET.get("level__id__exact")
        if level_id:
            initial["level"] = level_id
        return initial

    class Media:
        js = ("admin/js/custom_jsoneditor.js",)
