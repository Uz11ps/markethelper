from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.keyboards.exit_ai import chatgpt_kb
from bot.keyboards.main_menu import main_menu_kb
from bot.services.api_client import APIClient, InsufficientTokensError, APIClientError
from bot.states.ai_states import AIChatStates

router = Router()
api = APIClient()

# Обработчик для кнопки "🤖ChatGPT" удалён - теперь используется inline кнопка из профиля


@router.message(F.text.in_({"/exit", "🚪 Выйти"}))
async def exit_chatgpt(message: types.Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    user = await api.get_profile(user_id)  
    has_active_sub = user.get("active_sub", True)

    await message.answer(
        "✅ Вы вышли из режима ChatGPT",
        reply_markup=main_menu_kb(has_active_sub)
    )

@router.message(AIChatStates.chatting)
async def gpt_chat(message: types.Message, state: FSMContext):
    question = message.text
    thinking_msg = await message.answer("⌛ Думаю...")
    tg_id = message.from_user.id

    try:
        charge = await api.charge_tokens(tg_id, "ai_chat")
        await thinking_msg.edit_text(
            "⌛ Думаю...\n"
            f"💰 Списано {charge['cost']} токенов. Остаток: {charge['balance']}."
        )
    except InsufficientTokensError as e:
        await thinking_msg.delete()
        await message.answer(
            "❌ Недостаточно токенов для вопроса к GPT.\n"
            "Пополните баланс или обратитесь в поддержку."
        )
        await state.clear()
        return
    except APIClientError as e:
        await thinking_msg.delete()
        await message.answer(f"⚠️ Не удалось списать токены: {e}")
        await state.clear()
        return

    try:
        answer = await api.query_ai(question, tg_id=tg_id)
        await thinking_msg.delete()
        await message.answer(answer, parse_mode="Markdown")
    except Exception as e:
        await thinking_msg.delete()
        await message.answer(f"⚠️ Ошибка: {str(e)}")
