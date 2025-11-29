from aiogram.fsm.state import State, StatesGroup


class GenerationStates(StatesGroup):
    awaiting_photo = State()
    processing = State()
