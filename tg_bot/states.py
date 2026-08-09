from aiogram.fsm.state import State, StatesGroup


class ParseFlow(StatesGroup):
    waiting_for_html = State()
    waiting_for_description = State()
    waiting_for_web_app = State()
    waiting_for_confirm = State()
    processing = State()