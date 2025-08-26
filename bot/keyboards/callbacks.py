from aiogram.filters.callback_data import CallbackData


class NavigationCallback(CallbackData, prefix="nav"):
    level: str
    course_id: int | None = None
    module_id: int | None = None
    level_id: int | None = None
    task_id: int | None = None


class FeedbackCallback(CallbackData, prefix="feedback"):
    check_id: int


class FaqCallback(CallbackData, prefix="faq"):
    id: int
