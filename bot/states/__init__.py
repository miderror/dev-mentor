from aiogram.fsm.state import State, StatesGroup


class CodeCheck(StatesGroup):
    waiting_for_code = State()
