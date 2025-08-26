from aiogram.fsm.state import State, StatesGroup


class TaskNavigation(StatesGroup):
    solving_task = State()
