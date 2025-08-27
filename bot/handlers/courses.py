from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from backend.courses.models import User, UserTaskStatus
from bot.keyboards.callbacks import NavigationCallback
from bot.keyboards.inline_keyboards import (
    get_courses_kb,
    get_levels_kb,
    get_modules_kb,
    get_task_view_kb,
    get_tasks_kb,
)
from bot.states.check import CodeCheck
from bot.utils.db import (
    get_bot_texts,
    get_course_modules,
    get_level_tasks,
    get_module_levels,
    get_task_details,
    get_user_courses,
    get_user_task_status,
)

router = Router()


@router.callback_query(NavigationCallback.filter(F.level == "courses"))
async def show_courses(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    texts = await get_bot_texts()
    courses = await get_user_courses(callback.from_user.id)
    if not courses:
        await callback.answer(texts.no_courses_available_message, show_alert=True)
        return
    await callback.message.edit_text(
        texts.choose_course_message, reply_markup=get_courses_kb(courses)
    )
    await callback.answer()


@router.callback_query(NavigationCallback.filter(F.level == "modules"))
async def show_modules(
    callback: CallbackQuery, callback_data: NavigationCallback, state: FSMContext
):
    await state.clear()
    texts = await get_bot_texts()
    modules = await get_course_modules(callback_data.course_id, callback.from_user.id)
    await callback.message.edit_text(
        texts.choose_module_message,
        reply_markup=get_modules_kb(modules, callback_data.course_id),
    )
    await callback.answer()


@router.callback_query(NavigationCallback.filter(F.level == "levels"))
async def show_levels(
    callback: CallbackQuery, callback_data: NavigationCallback, state: FSMContext
):
    await state.clear()
    texts = await get_bot_texts()
    levels = await get_module_levels(callback_data.module_id, callback.from_user.id)
    await callback.message.edit_text(
        texts.choose_level_message,
        reply_markup=get_levels_kb(
            levels, callback_data.module_id, callback_data.course_id
        ),
    )
    await callback.answer()


@router.callback_query(NavigationCallback.filter(F.level == "tasks"))
async def show_tasks(
    callback: CallbackQuery, callback_data: NavigationCallback, state: FSMContext
):
    await state.clear()
    texts = await get_bot_texts()
    tasks = await get_level_tasks(callback_data.level_id, callback.from_user.id)
    text = texts.choose_task_message
    keyboard = get_tasks_kb(
        tasks,
        callback_data.level_id,
        callback_data.module_id,
        callback_data.course_id,
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(NavigationCallback.filter(F.level == "task_view"))
async def show_task_view(
    callback: CallbackQuery, callback_data: NavigationCallback, user: User
):
    task = await get_task_details(callback_data.task_id, user.telegram_id)
    if not task:
        await callback.answer(
            "Задача не найдена или у вас нет к ней доступа.", show_alert=True
        )
        return

    status = await get_user_task_status(user.telegram_id, task.id)
    status_text = ""
    if status and status.status == UserTaskStatus.Status.SOLVED:
        status_text = "✅ *Решение принято*\n\n"

    message_text = (
        f"**Задача #{task.number}: {task.title}**\n\n{status_text}{task.description}"
    )

    keyboard = get_task_view_kb(
        task_id=task.id,
        level_id=callback_data.level_id,
        module_id=callback_data.module_id,
        course_id=callback_data.course_id,
    )

    if task.image:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(task.image.path),
            caption=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(NavigationCallback.filter(F.level == "solve_task"))
async def start_solving_task(
    callback: CallbackQuery,
    callback_data: NavigationCallback,
    state: FSMContext,
    user: User,
):
    task = await get_task_details(callback_data.task_id, user.telegram_id)
    if not task:
        await callback.answer("Задача не найдена либо доступ запрещен", show_alert=True)
        return
    await state.set_state(CodeCheck.waiting_for_code)
    await state.update_data(task_id=callback_data.task_id)

    texts = await get_bot_texts()
    await callback.message.answer(texts.request_code_message)
    await callback.answer()
