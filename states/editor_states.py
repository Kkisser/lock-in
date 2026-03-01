from aiogram.fsm.state import StatesGroup, State


class EditorFSM(StatesGroup):
    waiting_name = State()
    waiting_rename = State()
