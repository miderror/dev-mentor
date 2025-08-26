from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.db import get_support_link

from .callbacks import FaqCallback, FeedbackCallback, NavigationCallback


async def get_main_menu_kb() -> InlineKeyboardMarkup:
    support_link = await get_support_link()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Выбор курса",
                    callback_data=NavigationCallback(level="courses").pack(),
                )
            ],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="show_faq_list")],
            [InlineKeyboardButton(text="👨‍💻 Тех. поддержка", url=support_link)],
        ]
    )


def get_courses_kb(courses: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=NavigationCallback(level="modules", course_id=pk).pack(),
            )
        ]
        for pk, title in courses
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ В главное меню", callback_data="back_to_main_menu"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_modules_kb(
    modules: list[tuple[int, str]], course_id: int
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=NavigationCallback(
                    level="levels", module_id=pk, course_id=course_id
                ).pack(),
            )
        ]
        for pk, title in modules
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к курсам",
                callback_data=NavigationCallback(level="courses").pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_levels_kb(
    levels: list[tuple[int, str]], module_id: int, course_id: int
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=title,
                callback_data=NavigationCallback(
                    level="tasks", level_id=pk, module_id=module_id, course_id=course_id
                ).pack(),
            )
        ]
        for pk, title in levels
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к модулям",
                callback_data=NavigationCallback(
                    level="modules", course_id=course_id
                ).pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tasks_kb(
    tasks: list[dict], level_id: int, module_id: int, course_id: int
) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        status_icon = "✅" if task["is_solved"] else ""
        text = f"{status_icon} #{task['number']}. {task['title']}"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=NavigationCallback(
                        level="task_view",
                        task_id=task["id"],
                        level_id=level_id,
                        module_id=module_id,
                        course_id=course_id,
                    ).pack(),
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к уровням",
                callback_data=NavigationCallback(
                    level="levels", module_id=module_id, course_id=course_id
                ).pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_task_view_kb(
    task_id: int, level_id: int, module_id: int, course_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Решить задачу",
                    callback_data=NavigationCallback(
                        level="solve_task",
                        task_id=task_id,
                        level_id=level_id,
                        module_id=module_id,
                        course_id=course_id,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к задачам",
                    callback_data=NavigationCallback(
                        level="tasks",
                        level_id=level_id,
                        module_id=module_id,
                        course_id=course_id,
                    ).pack(),
                )
            ],
        ]
    )


def get_feedback_kb(check_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Дать обратную связь на решение",
                    callback_data=FeedbackCallback(check_id=check_id).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ В главное меню", callback_data="back_to_main_menu"
                )
            ],
        ]
    )


def get_after_check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Вернуться в меню", callback_data="back_to_main_menu"
                )
            ],
        ]
    )


def get_faq_list_kb(faq_list: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=question, callback_data=FaqCallback(id=faq_id).pack()
            )
        ]
        for faq_id, question in faq_list
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ В главное меню", callback_data="back_to_main_menu"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
