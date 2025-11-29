from aiogram.fsm.state import State, StatesGroup


class InfographicStates(StatesGroup):
    choose_type = State()
    enter_title = State()
    upload_product_images = State()
    upload_reference_images = State()
    enter_user_prompt = State()
    choose_concept = State()
    edit_style = State()
    generate_final = State()
    view_result = State()