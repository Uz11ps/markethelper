from io import BytesIO
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
from backend.services.file_service import FileService
from tortoise.exceptions import DoesNotExist
# file_actions_kb больше не используется, так как кнопка "обновить куки" удалена
from bot.services.api_client import APIClient
from bot.keyboards.profile_menu import profile_menu_kb
from bot.keyboards import subscription
from aiogram.types import CallbackQuery, BufferedInputFile
from bot.utils import get_full_name
import logging

router = Router()
api = APIClient()
logger = logging.getLogger(__name__)

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
    from bot.keyboards.main_menu import main_menu_kb
    
    tg = message.from_user
    data = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))

    active_until = data.get("active_until") if data else None
    has_active_sub = active_until is not None
    tariff_code = data.get('tariff_code')
    is_group_subscription = tariff_code == "GROUP"  # Проверяем тариф "Складчина"

    # Определяем статус пользователя
    tariff_name = data.get('tariff_name')
    if not active_until:
        status_text = "Обычный пользователь"
        active_until_text = "Нет активной подписки"
    else:
        status_text = tariff_name or "Активная подписка"
        active_until_text = _fmt_date(active_until)
    
    text = (
        f"👤 <b>Пользователь:</b> @{data.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {status_text}\n"
        f"🗓️ <b>Активен до:</b> {active_until_text}\n"
    )
    
    # Показываем файл только для складчины
    if is_group_subscription and data.get("access_file_path"):
        text += f"📁 <b>Файл:</b> {(data.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
    
    text += f"💰 <b>Токены:</b> {data.get('bonus_balance') or 0}"

    # Отправляем профиль с inline клавиатурой
    await message.answer(
        text, 
        reply_markup=profile_menu_kb(has_active_sub=has_active_sub, is_group_subscription=is_group_subscription)
    )
    # Обновляем главную клавиатуру с кнопкой "Пополнить" - отправляем отдельным сообщением
    await message.answer(
        "💡 <b>Доступные действия:</b>\n\n"
        "Используйте кнопки ниже для навигации.",
        reply_markup=main_menu_kb(has_active_sub=has_active_sub)
    )

@router.callback_query(F.data == "profile:referral")
async def referral_info(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    try:
        data = await api.get_referral_info(tg_id)
    except Exception as e:
        await callback.message.answer(f"error {str(e)}")
        print(f"[ERROR referral_info] {e}")
        await callback.answer()
        return

    ref_link = data.get("ref_link", "")
    ref_count = data.get("ref_count", 0)
    rub_per_referral = data.get("rub_per_referral", 0)
    total_rub = data.get("total_rub", 0)
    pending_rub = data.get("pending_rub", 0)
    approved_rub = data.get("approved_rub", 0)
    available_rub = data.get("available_rub", 0)

    text = (
        f"🎁 <b>Реферальная программа</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"👥 <b>Приглашено пользователей:</b> {ref_count}\n\n"
        f"💰 <b>Финансовая информация:</b>\n"
        f"• За одного реферала: <b>{rub_per_referral:.2f}₽</b>\n"
        f"• Всего заработано: <b>{total_rub:.2f}₽</b>\n"
        f"• Ожидает подтверждения: <b>{pending_rub:.2f}₽</b>\n"
        f"• Уже выплачено: <b>{approved_rub:.2f}₽</b>\n"
        f"• Доступно к выводу: <b>{available_rub:.2f}₽</b>\n\n"
        f"💡 Поделитесь ссылкой с друзьями и получайте деньги за каждого приглашенного!"
    )

    # Добавляем кнопку для создания заявки на выплату если есть доступные средства
    keyboard = None
    if available_rub > 0:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💵 Запросить выплату ({available_rub:.2f}₽)",
                callback_data="referral:request_payout"
            )]
        ])

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "referral:request_payout")
async def request_referral_payout(callback: types.CallbackQuery):
    """Создание заявки на выплату рублей за рефералов"""
    await callback.answer()
    
    tg_id = callback.from_user.id
    
    try:
        # Получаем информацию о рефералах
        data = await api.get_referral_info(tg_id)
        available_rub = data.get("available_rub", 0)
        ref_count = data.get("ref_count", 0)
        
        if available_rub <= 0:
            await callback.message.answer("❌ У вас нет доступных средств для вывода.")
            return
        
        # Создаем заявку на выплату всех доступных рефералов
        # Вычисляем количество рефералов для выплаты
        rub_per_referral = data.get("rub_per_referral", 0)
        if rub_per_referral <= 0:
            await callback.message.answer("❌ Ошибка: не установлена стоимость реферала.")
            return
        
        # Вычисляем сколько рефералов можно выплатить
        referral_count = int(available_rub / rub_per_referral)
        
        result = await api.create_referral_payout(tg_id, referral_count)
        
        await callback.message.answer(
            f"✅ <b>Заявка на выплату создана!</b>\n\n"
            f"💰 Сумма: <b>{result.get('amount_rub', 0):.2f}₽</b>\n"
            f"👥 Рефералов: <b>{result.get('referral_count', 0)}</b>\n"
            f"📋 Номер заявки: <b>#{result.get('id', 'N/A')}</b>\n\n"
            f"⏳ Ожидайте подтверждения администратора."
        )
    except Exception as e:
        logger.error(f"Ошибка создания заявки на выплату: {e}")
        await callback.message.answer(
            f"❌ Ошибка при создании заявки: {str(e)}\n\n"
            f"Попробуйте позже или обратитесь к администратору."
        )
    
@router.callback_query(F.data == "profile:support")
async def support_handler(callback: types.CallbackQuery):
    support_username = "gorrrd"
    await callback.message.answer(
        f"📞 Связаться с оператором можно здесь: @{support_username}"
    )
    await callback.answer()


@router.callback_query(F.data == "profile:topup")
async def topup_from_profile(callback: types.CallbackQuery):
    """Обработка кнопки пополнения из профиля"""
    await callback.answer()
    
    if not callback.message:
        await callback.message.answer("❌ Ошибка: не удалось обработать запрос")
        return
    
    # Импортируем необходимые функции и классы
    from bot.handlers.topup import topup_amounts_kb
    from bot.utils import get_full_name
    
    tg = callback.from_user
    
    try:
        profile = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        balance = 0
    
    # Получаем настройки пополнения из базы данных
    try:
        topup_settings = await api.get_topup_settings()
        topup_options = topup_settings.get("topup_options", [])
        token_price = topup_settings.get("token_price", 1.0)
    except Exception as e:
        logger.error(f"Ошибка получения настроек пополнения: {e}")
        # Используем значения по умолчанию
        topup_options = [
            {"tokens": 100, "price": 100},
            {"tokens": 250, "price": 225},
            {"tokens": 500, "price": 400},
            {"tokens": 1000, "price": 700},
        ]
        token_price = 1.0
    
    text = (
        "💰 <b>Пополнение баланса</b>\n\n"
        f"💼 Ваш текущий баланс: <b>{balance} токенов</b>\n"
        f"💵 Стоимость 1 токена: <b>{token_price:.2f}₽</b>\n\n"
        "Выберите сумму для пополнения:"
    )
    
    await callback.message.answer(text, reply_markup=topup_amounts_kb(topup_options))

@router.callback_query(F.data == "profile:chatgpt")
async def chatgpt_handler(callback: types.CallbackQuery, state: FSMContext):
    """Переход в режим ChatGPT из профиля - сначала выбор модели"""
    from bot.states.ai_states import AIChatStates
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await callback.answer()
    
    # Получаем сохраненную модель пользователя
    selected_gpt_model = None
    try:
        user_settings = await api.get_user_generation_settings(callback.from_user.id)
        selected_gpt_model = user_settings.get("selected_gpt_model")
    except Exception as exc:
        logger.warning(f"Не удалось получить настройки пользователя: {exc}")
    
    # Список доступных моделей GPT
    gpt_models = {
        "gpt-4o": {"name": "GPT-4o", "description": "Самая мощная"},
        "gpt-4o-mini": {"name": "GPT 5 NANO MINI", "description": "Быстрая и экономичная"},
        "gpt-4-turbo": {"name": "GPT-4 Turbo", "description": "Баланс скорости и качества"},
    }
    
    # Формируем клавиатуру выбора модели
    buttons = []
    for model_key, model_info in gpt_models.items():
        checkmark = "✅" if model_key == selected_gpt_model else "⚪"
        buttons.append([
            InlineKeyboardButton(
                text=f"{checkmark} {model_info['name']} - {model_info['description']}",
                callback_data=f"chatgpt:select_model:{model_key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        pricing = await api.get_token_pricing()
        gpt_cost = pricing.get("gpt_request_cost", 0) if pricing else 0
    except Exception:
        gpt_cost = 1
    
    selected_model_text = ""
    if selected_gpt_model and selected_gpt_model in gpt_models:
        selected_model = gpt_models[selected_gpt_model]
        selected_model_text = f"\n\n✅ <b>Ваша сохраненная модель:</b> {selected_model.get('name', selected_gpt_model)}"
    
    # Пытаемся отредактировать исходное сообщение, если не получается - отправляем новое
    try:
        await callback.message.edit_text(
            "🤖 <b>Выберите модель ChatGPT</b>\n\n"
            "Выберите модель для использования в чате:\n\n"
            f"💰 Стоимость одного вопроса: <b>{gpt_cost} токенов</b>"
            f"{selected_model_text}",
            reply_markup=keyboard
        )
    except Exception:
        # Если не удалось отредактировать, отправляем новое сообщение
        await callback.message.answer(
            "🤖 <b>Выберите модель ChatGPT</b>\n\n"
            "Выберите модель для использования в чате:\n\n"
            f"💰 Стоимость одного вопроса: <b>{gpt_cost} токенов</b>"
            f"{selected_model_text}",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("chatgpt:select_model:"))
async def select_chatgpt_model_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора модели GPT для ChatGPT"""
    from bot.states.ai_states import AIChatStates
    from bot.keyboards.exit_ai import chatgpt_kb
    
    await callback.answer()
    
    model_key = callback.data.replace("chatgpt:select_model:", "")
    
    # Сохраняем выбранную модель в настройках пользователя
    try:
        await api.update_user_generation_settings(
            callback.from_user.id,
            selected_gpt_model=model_key
        )
    except Exception as e:
        logger.warning(f"Не удалось сохранить модель GPT в настройках: {e}")
    
    # Сохраняем модель в state для текущей сессии
    await state.update_data(selected_gpt_model=model_key)
    
    gpt_models = {
        "gpt-4o": {"name": "GPT-4o", "description": "Самая мощная"},
        "gpt-4o-mini": {"name": "GPT 5 NANO MINI", "description": "Быстрая и экономичная"},
        "gpt-4-turbo": {"name": "GPT-4 Turbo", "description": "Баланс скорости и качества"},
    }
    
    model_info = gpt_models.get(model_key, {})
    model_name = model_info.get("name", model_key)
    
    try:
        pricing = await api.get_token_pricing()
        gpt_cost = pricing.get("gpt_request_cost", 0) if pricing else 0
    except Exception:
        gpt_cost = 1
    
    await state.set_state(AIChatStates.chatting)
    
    # Пытаемся отредактировать сообщение, если не получается - отправляем новое
    try:
        await callback.message.edit_text(
            f"🤖 <b>Режим ChatGPT активирован!</b>\n\n"
            f"✅ Выбрана модель: <b>{model_name}</b>\n\n"
            "💬 Отправьте мне свой вопрос, и я спрошу у ChatGPT.\n"
            f"💰 Стоимость одного вопроса: <b>{gpt_cost} токенов</b>.\n\n"
            "Для выхода нажмите кнопку ниже 👇",
            reply_markup=chatgpt_kb()
        )
    except Exception:
        # Если не удалось отредактировать (сообщение было отправлено через answer), отправляем новое
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"🤖 <b>Режим ChatGPT активирован!</b>\n\n"
            f"✅ Выбрана модель: <b>{model_name}</b>\n\n"
            "💬 Отправьте мне свой вопрос, и я спрошу у ChatGPT.\n"
            f"💰 Стоимость одного вопроса: <b>{gpt_cost} токенов</b>.\n\n"
            "Для выхода нажмите кнопку ниже 👇",
            reply_markup=chatgpt_kb()
        )

@router.callback_query(F.data == "profile:generate")
async def generate_handler(callback: types.CallbackQuery, state: FSMContext):
    """Переход к генерации изображений из профиля - выбор режима"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await callback.answer()
    
    await state.clear()
    
    # Показываем выбор режима генерации
    buttons = [
        [InlineKeyboardButton(text="🖼 Картинки", callback_data="generate:mode:images")],
        [InlineKeyboardButton(text="📊 Инфографика", callback_data="generate:mode:infographics")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        profile = await api.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception:
        balance = 0
    
    await callback.message.answer(
        "🎨 <b>Генерация изображений</b>\n\n"
        "Выберите режим генерации:\n\n"
        "🖼 <b>Картинки</b> - простая генерация по текстовому промпту\n"
        "📊 <b>Инфографика</b> - генерация с загрузкой фото товара и референсов\n\n"
        f"💼 Ваш баланс: <b>{balance} токенов</b>",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("generate:mode:"))
async def generate_mode_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора режима генерации"""
    await callback.answer()
    
    mode = callback.data.replace("generate:mode:", "")
    
    # Вызываем логику выбора модели напрямую, без создания Message объекта
    from bot.states.image_generation import ImageGenerationStates
    from bot.keyboards.inline import model_selection_keyboard
    
    await state.clear()
    
    if mode == "images":
        await state.set_state(ImageGenerationStates.choosing_model_images)
        await state.update_data(mode="images")
    elif mode == "infographics":
        await state.set_state(ImageGenerationStates.choosing_model_infographics)
        await state.update_data(mode="infographics", product_photos=[], reference_photos=[])
    
    try:
        models = await api.get_image_models()
    except Exception as exc:
        logger.warning(f"Не удалось получить список моделей: {exc}")
        models = {}
    
    selected_model_key = None
    try:
        user_settings = await api.get_user_generation_settings(callback.from_user.id)
        selected_model_key = user_settings.get("selected_model_key")
    except Exception as exc:
        logger.warning(f"Не удалось получить настройки пользователя: {exc}")
    
    try:
        profile = await api.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        balance = 0
    
    models_text = "\n".join([
        f"• {info.get('name', key)}: {info.get('cost', 0)} токенов - {info.get('description', '')}"
        for key, info in models.items()
    ]) if models else "• Nano Banana: 5 токенов - Быстрая генерация"
    
    selected_model_text = ""
    if selected_model_key and selected_model_key in models:
        selected_model = models[selected_model_key]
        selected_model_text = f"\n\n✅ <b>Ваша сохраненная модель:</b> {selected_model.get('name', selected_model_key)}"
    
    if mode == "images":
        text = (
            "🖼 <b>Генерация картинок</b>\n\n"
            "Выберите модель для генерации:\n\n"
            f"{models_text}"
            f"{selected_model_text}\n\n"
            f"💰 Ваш баланс: <b>{balance} токенов</b>"
        )
    else:
        text = (
            "📊 <b>Генерация инфографики</b>\n\n"
            "Выберите модель для генерации:\n\n"
            f"{models_text}"
            f"{selected_model_text}\n\n"
            f"💰 Ваш баланс: <b>{balance} токенов</b>\n\n"
            "После выбора модели вы сможете загрузить фото товара и референсы."
        )
    
    await callback.message.answer(
        text,
        reply_markup=model_selection_keyboard(models, selected_model_key)
    )


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к профилю"""
    await callback.answer()
    await state.clear()
    
    try:
        profile = await api.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
    except Exception:
        profile = {}
    
    active_until = profile.get("active_until")
    has_active = active_until is not None
    tariff_code = profile.get('tariff_code')
    is_group_subscription = tariff_code == "GROUP"  # Проверяем тариф "Складчина"
    
    from bot.keyboards.profile_menu import profile_menu_kb
    
    text = (
        f"👤 <b>Пользователь:</b> @{profile.get('username') or callback.from_user.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {profile.get('tariff_name') or 'Обычный пользователь'}\n"
        f"🗓️ <b>Активен до:</b> {active_until if active_until else 'Нет активной подписки'}\n"
    )
    
    if is_group_subscription and profile.get("access_file_path"):
        text += f"📁 <b>Файл:</b> {(profile.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
    
    text += f"💰 <b>Токены:</b> {profile.get('bonus_balance') or 0}"
    
    await callback.message.answer(text, reply_markup=profile_menu_kb(has_active_sub=has_active, is_group_subscription=is_group_subscription))

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
                f"❌ Файл куков пустой.\n\n📅 Последнее обновление: {updated_at or 'нет данных'}"
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
            caption=f"📅 Последнее обновление: {updated_str}"
        )

    except Exception as e:
        error_msg = str(e)
        # Улучшаем сообщения об ошибках для пользователя
        if "Нет файлов для этой группы" in error_msg:
            await callback.message.answer(
                "❌ <b>Файл куков недоступен</b>\n\n"
                "Для вашей группы доступа еще не загружен файл куков.\n"
                "Пожалуйста, обратитесь к администратору для загрузки файла."
            )
        elif "нет активной подписки" in error_msg.lower() or "нет подписки" in error_msg.lower():
            await callback.message.answer(
                "❌ <b>Доступ к файлу недоступен</b>\n\n"
                "У вас нет активной подписки с доступом к файлам.\n"
                "Обратитесь к администратору для получения доступа."
            )
        elif "Файл отсутствует или пуст" in error_msg:
            await callback.message.answer(
                "❌ <b>Файл куков пуст или отсутствует</b>\n\n"
                "Файл для вашей группы существует, но он пустой или был удален.\n"
                "Обратитесь к администратору для обновления файла."
            )
        else:
            await callback.message.answer(
                f"❌ <b>Ошибка при получении файла</b>\n\n"
                f"{error_msg}\n\n"
                "Если проблема повторяется, обратитесь к администратору."
            )
