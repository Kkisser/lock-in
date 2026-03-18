from aiogram.fsm.state import State, StatesGroup


class LongtermFSM(StatesGroup):
    waiting_counter_target = State()
    waiting_counter_unit = State()
    waiting_timer_target = State()
    waiting_custom_amount = State()
