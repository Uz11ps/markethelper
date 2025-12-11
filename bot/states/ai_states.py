from aiogram.fsm.state import State, StatesGroup

class AIChatStates(StatesGroup):
    choosing_gpt_model = State()  # Выбор модели GPT перед началом чата
    chatting = State() 