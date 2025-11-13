from io import BytesIO
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
from backend.services.file_service import FileService
from tortoise.exceptions import DoesNotExist
from bot.keyboards.cookie import file_actions_kb
from bot.services.api_client import APIClient
from bot.keyboards.profile_menu import profile_menu_kb
from bot.keyboards import subscription
from aiogram.types import CallbackQuery, BufferedInputFile

router = Router()
api = APIClient()

def _fmt_date(dt_iso: str | None) -> str:
    if not dt_iso:
        return "—"
    try:
        return datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except Exception:
        return dt_iso

@router.message(F.text == "❓FAQ")
async def choose_tariff(message: types.Message):
    await message.answer("Данный бот облегчит вам работу с SalesFinder! Можете приобрести как личный доступ, так и складчину!\n\nПо всем вопросам обращайтесь @gorrrd")

@router.message(F.text == "👤Профиль")
@router.message(F.text == "/profile")
async def show_profile(message: types.Message):
    tg = message.from_user
    data = await api.get_profile(tg.id)

    # Временно отключена проверка подписки для тестирования
    active_until = data.get("active_until") if data else None

    text = (
        f"👤 <b>Пользователь:</b> @{data.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {data.get('tariff_name') or 'Тестовый режим'}\n"
        f"🗓️ <b>Активен до:</b> {_fmt_date(active_until) if active_until else 'Бессрочно (тест)'}\n"
        f"📁 <b>Файл:</b> {(data.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
        f"💰 <b>Бонусы:</b> {data.get('bonus_balance') or 0}"
    )

    await message.answer(text, reply_markup=profile_menu_kb())

@router.callback_query(F.data == "profile:referral")
async def referral_info(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    try:
        data = await api.get_referral_info(tg_id)
    except Exception as e:
        await callback.message.answer(f"error {str(e)}")
        print(f"[ERROR referral_info] {e}")
        return

    link = data.get("ref_link")
    count = data.get("ref_count", 0)

    await callback.message.answer(
        f"🎁 Ваша реферальная ссылка:\n"
        f"<code>{link}</code>\n\n"
        f"👥 Количество рефералов: <b>{count}</b>"
    )
    await callback.answer()
    
@router.callback_query(F.data == "profile:support")
async def support_handler(callback: types.CallbackQuery):
    support_username = "gorrrd"
    await callback.message.answer(
        f"📞 Связаться с оператором можно здесь: @{support_username}"
    )
    await callback.answer()

@router.callback_query(F.data == "profile:chatgpt")
async def chatgpt_handler(callback: types.CallbackQuery, state: FSMContext):
    """Переход в режим ChatGPT из профиля"""
    from bot.states.ai_states import AIChatStates
    from bot.keyboards.exit_ai import chatgpt_kb

    await state.set_state(AIChatStates.chatting)

    await callback.message.answer(
        "🤖 <b>Режим ChatGPT активирован!</b>\n\n"
        "💬 Отправьте мне свой вопрос, и я спрошу у ChatGPT.\n\n"
        "Для выхода нажмите кнопку ниже 👇",
        reply_markup=chatgpt_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "profile:generate")
async def generate_handler(callback: types.CallbackQuery, state: FSMContext):
    """Переход к генерации изображений из профиля"""
    from bot.states.image_generation import ImageGenerationStates
    from bot.keyboards.inline import skip_keyboard

    await state.clear()
    await state.set_state(ImageGenerationStates.waiting_for_product_photos)
    await state.update_data(product_photos=[], reference_photos=[])

    await callback.message.answer(
        "🎨 <b>Генерация карточки товара</b>\n\n"
        "Отправьте от 1 до 5 фотографий вашего товара.\n"
        "После отправки всех фото нажмите кнопку 'Готово'.",
        reply_markup=skip_keyboard("product_photos_done")
    )
    await callback.answer()

@router.callback_query(F.data == "profile:renew")
async def renew_subscription(callback: types.CallbackQuery):
    await callback.message.answer(
        "Выберите тариф для продления:",
        reply_markup=subscription.tariffs_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "profile:get_file")
async def on_file_get(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await callback.answer("Готовлю файл...")

    res = None
    try:
        res = await api.get_user_file(tg_id)
        cookies_text = res.get("cookies", "")
        file_id = res.get("id") or res.get("file_id")
        updated_at = res.get("updated_at")

        if not cookies_text or not cookies_text.strip():
            await callback.message.answer(
                f"❌ Файл куков пустой.\n\n📅 Последнее обновление: {updated_at or 'нет данных'}",
                reply_markup=file_actions_kb(file_id) if file_id else None
            )
            return

        filename = (res.get("file") or f"group_{res.get('group_id')}_cookies.txt").split("/")[-1]

        bio = BytesIO(cookies_text.encode("utf-8"))
        bio.seek(0)
        file = BufferedInputFile(bio.read(), filename=filename)

        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                updated_str = dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                updated_str = updated_at
        else:
            updated_str = "нет данных"
        await callback.message.answer_document(
            document=file,
            caption=f"📅 Последнее обновление: {updated_str}",
            reply_markup=file_actions_kb(file_id) if file_id else None
        )

    except Exception as e:
        file_id_safe = None
        if res:
            file_id_safe = res.get("id") or res.get("file_id")

        await callback.message.answer(
            f"Ошибка при получении файла: {e}",
            reply_markup=file_actions_kb(file_id_safe) if file_id_safe else None
        )