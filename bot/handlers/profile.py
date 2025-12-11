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
from bot.utils import get_full_name

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
    from bot.keyboards.main_menu import main_menu_kb
    
    tg = message.from_user
    data = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))

    active_until = data.get("active_until") if data else None
    has_active_sub = active_until is not None
    has_file_access = bool(data.get("access_file_path"))  # Файл есть только у складчины

    # Определяем статус пользователя
    tariff_name = data.get('tariff_name')
    if not active_until:
        if tariff_name:
            status_text = "Обычный пользователь"
        else:
            status_text = "Тестовый режим"
    else:
        status_text = tariff_name or "Активная подписка"
    
    text = (
        f"👤 <b>Пользователь:</b> @{data.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {status_text}\n"
        f"🗓️ <b>Активен до:</b> {_fmt_date(active_until) if active_until else 'Нет активной подписки'}\n"
    )
    
    # Показываем файл только для складчины
    if has_file_access:
        text += f"📁 <b>Файл:</b> {(data.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
    
    text += f"💰 <b>Токены:</b> {data.get('bonus_balance') or 0}"

    # Отправляем профиль с inline клавиатурой
    await message.answer(
        text, 
        reply_markup=profile_menu_kb(has_active_sub=has_active_sub, has_file_access=has_file_access)
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

@router.callback_query(F.data == "profile:generation_settings")
async def generation_settings_handler(callback: types.CallbackQuery, state: FSMContext):
    """Показать настройки промптов и моделей для генерации"""
    await callback.answer()
    
    try:
        # Получаем настройки пользователя
        settings_data = await api.get_user_generation_settings(callback.from_user.id)
        
        available_models = settings_data.get("available_models", {})
        system_prompt = settings_data.get("system_prompt", "")
        selected_model_key = settings_data.get("selected_model_key")
        custom_prompt = settings_data.get("custom_prompt")
        
        # Формируем текст с моделями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        buttons = []
        for key, info in available_models.items():
            checkmark = "✅" if key == selected_model_key else ""
            buttons.append([
                InlineKeyboardButton(
                    text=f"{checkmark} {info.get('name', key)} ({info.get('cost', 0)} токенов)",
                    callback_data=f"genset:model:{key}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton(text="📝 Изменить промпт", callback_data="genset:prompt:edit"),
            InlineKeyboardButton(text="🔄 Сбросить промпт", callback_data="genset:prompt:reset")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Текущий промпт
        current_prompt = custom_prompt if custom_prompt else system_prompt
        prompt_preview = current_prompt[:200] + "..." if len(current_prompt) > 200 else current_prompt
        
        selected_model_name = "Не выбрана"
        if selected_model_key and selected_model_key in available_models:
            selected_model_name = available_models[selected_model_key].get("name", selected_model_key)
        
        text = (
            "⚙️ <b>Настройки генерации</b>\n\n"
            f"🎨 <b>Выбранная модель:</b> {selected_model_name}\n\n"
            "📝 <b>Текущий промпт:</b>\n"
            f"<code>{prompt_preview}</code>\n\n"
            "Выберите модель для генерации или измените промпт:"
        )
        
        await callback.message.answer(text, reply_markup=keyboard)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка получения настроек генерации: {e}")
        await callback.message.answer(
            f"❌ Ошибка при получении настроек: {str(e)}"
        )

@router.callback_query(F.data.startswith("genset:model:"))
async def select_model_handler(callback: types.CallbackQuery):
    """Выбор модели для генерации"""
    await callback.answer()
    
    model_key = callback.data.replace("genset:model:", "")
    
    try:
        await api.update_user_generation_settings(
            callback.from_user.id,
            selected_model_key=model_key
        )
        
        # Получаем информацию о модели
        settings_data = await api.get_user_generation_settings(callback.from_user.id)
        available_models = settings_data.get("available_models", {})
        
        if model_key in available_models:
            model_info = available_models[model_key]
            await callback.message.answer(
                f"✅ Модель <b>{model_info.get('name', model_key)}</b> выбрана!\n\n"
                f"Стоимость: {model_info.get('cost', 0)} токенов\n"
                f"Описание: {model_info.get('description', '')}"
            )
        else:
            await callback.message.answer("✅ Модель выбрана!")
        
        # Обновляем меню настроек
        await generation_settings_handler(callback, None)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка выбора модели: {e}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "genset:prompt:edit")
async def edit_prompt_handler(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование промпта"""
    await callback.answer()
    
    from bot.states.image_generation import ImageGenerationStates
    await state.set_state(ImageGenerationStates.waiting_for_custom_prompt)
    await state.update_data(editing_generation_prompt=True)
    
    await callback.message.answer(
        "✏️ <b>Введите новый промпт для генерации</b>\n\n"
        "Этот промпт будет использоваться вместо системного промпта.\n"
        "Отправьте текст промпта или /cancel для отмены."
    )

@router.callback_query(F.data == "genset:prompt:reset")
async def reset_prompt_handler(callback: types.CallbackQuery):
    """Сброс промпта к системному"""
    await callback.answer()
    
    try:
        await api.update_user_generation_settings(
            callback.from_user.id,
            custom_prompt=None
        )
        await callback.message.answer("✅ Промпт сброшен к системному значению!")
        
        # Обновляем меню настроек
        await generation_settings_handler(callback, None)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка сброса промпта: {e}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "profile:topup")
async def topup_from_profile(callback: types.CallbackQuery):
    """Обработка кнопки пополнения из профиля"""
    await callback.answer()
    
    # Импортируем функцию и вызываем её
    from bot.handlers.topup import show_topup_menu
    from aiogram.types import Message
    
    # Создаем объект Message из callback для совместимости
    # Используем callback.message как основу
    if callback.message:
        # Создаем Message объект из CallbackQuery.message
        message = Message(
            message_id=callback.message.message_id,
            date=callback.message.date,
            chat=callback.message.chat,
            from_user=callback.from_user,
            text="💰 Пополнить"
        )
        await show_topup_menu(message)
    else:
        await callback.message.answer("❌ Ошибка: не удалось обработать запрос")

@router.callback_query(F.data == "profile:chatgpt")
async def chatgpt_handler(callback: types.CallbackQuery, state: FSMContext):
    """Переход в режим ChatGPT из профиля"""
    from bot.states.ai_states import AIChatStates
    from bot.keyboards.exit_ai import chatgpt_kb

    pricing = await api.get_token_pricing()
    gpt_cost = pricing.get("gpt_request_cost", 0) if pricing else 0

    await state.set_state(AIChatStates.chatting)

    await callback.message.answer(
        "🤖 <b>Режим ChatGPT активирован!</b>\n\n"
        "💬 Отправьте мне свой вопрос, и я спрошу у ChatGPT.\n"
        f"💰 Стоимость одного вопроса: <b>{gpt_cost} токенов</b>.\n\n"
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

    try:
        pricing = await api.get_token_pricing()
    except Exception:
        pricing = {}
    await state.update_data(token_pricing=pricing)

    try:
        profile = await api.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
    except Exception:
        profile = {}
    balance = profile.get("bonus_balance", 0) if profile else 0
    image_cost = pricing.get("image_generation_cost", 0) if pricing else 0

    await callback.message.answer(
        "🎨 <b>Генерация карточки товара</b>\n\n"
        "Отправьте от 1 до 5 фотографий вашего товара.\n"
        "После отправки всех фото нажмите кнопку 'Готово'.\n\n"
        f"💰 Стоимость генерации: <b>{image_cost} токенов</b>.\n"
        f"💼 Ваш баланс: <b>{balance} токенов</b>.\n"
        "Токены списываются при запуске генерации.",
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
