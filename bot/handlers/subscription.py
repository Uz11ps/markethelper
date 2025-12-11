from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import subscription
from bot.services.api_client import APIClient

router = Router()
api = APIClient()


class SubscriptionStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_group = State()


@router.message(F.text == "🛒Тарифы и подписка")
async def choose_subscription_type(message: Message):
    """Выбор типа подписки: складчина или индивидуальный доступ"""
    await message.answer(
        "Выберите тип подписки:",
        reply_markup=subscription.subscription_type_kb()
    )


@router.callback_query(F.data.startswith("sub_type:"))
async def choose_tariff(callback: CallbackQuery):
    """Выбор тарифа после выбора типа подписки"""
    subscription_type = callback.data.split(":")[1]
    
    # Для совместимости используем старую логику с тарифами
    # В будущем можно добавить выбор тарифа
    tariff_code = "INDIVIDUAL" if subscription_type == "individual" else "GROUP"
    
    await callback.message.edit_text(
        "Выберите срок подписки:",
        reply_markup=subscription.durations_kb(tariff_code, subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("duration:"))
async def process_duration(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора длительности подписки"""
    try:
        parts = callback.data.split(":")
        if len(parts) == 4:
            # Новый формат: duration:tariff_code:subscription_type:months
            _, tariff_code, subscription_type, months = parts
            months = int(months)
        else:
            # Старый формат для совместимости
            _, tariff_code, months = parts
            months = int(months)
            subscription_type = "group"  # По умолчанию складчина
        
        # Сохраняем данные в состояние
        await state.update_data(
            tariff_code=tariff_code,
            subscription_type=subscription_type,
            months=months
        )
        
        if subscription_type == "individual":
            # Для индивидуального доступа запрашиваем email
            user_data = await api.get_user(callback.from_user.id)
            user_email = user_data.get("email")
            
            if user_email:
                # Email уже есть, можно создать заявку
                await create_request_final(
                    callback, 
                    tariff_code, 
                    months, 
                    subscription_type,
                    user_email=user_email
                )
            else:
                # Запрашиваем email
                await callback.message.edit_text(
                    "Для индивидуального доступа укажите ваш email адрес.\n"
                    "Вы можете пропустить этот шаг, если email уже был указан ранее."
                )
                await callback.message.answer(
                    "Введите ваш email или нажмите 'Пропустить':",
                    reply_markup=subscription.email_request_kb(tariff_code, months)
                )
                await state.set_state(SubscriptionStates.waiting_for_email)
                await callback.answer()
        else:
            # Для складчины создаем заявку без выбора группы (админ назначит группу)
            await create_request_final(
                callback,
                tariff_code,
                months,
                subscription_type,
                group_id=None
            )
            await callback.answer()
            
    except Exception as e:
        print(f"[ERROR process_duration] {e}")
        await callback.message.edit_text(
            f"❌ Ошибка: {str(e)}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("email_skip:"))
async def skip_email(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода email"""
    parts = callback.data.split(":")
    tariff_code = parts[1]
    months = int(parts[2])
    
    data = await state.get_data()
    subscription_type = data.get("subscription_type", "individual")
    
    await create_request_final(
        callback,
        tariff_code,
        months,
        subscription_type,
        user_email=None
    )
    await state.clear()


@router.callback_query(F.data.startswith("email_input:"))
async def request_email_input(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода email"""
    await callback.message.edit_text(
        "Введите ваш email адрес:"
    )
    await state.set_state(SubscriptionStates.waiting_for_email)
    await callback.answer()


@router.message(SubscriptionStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    """Обработка введенного email"""
    email = message.text.strip()
    
    # Простая валидация email
    if "@" not in email or "." not in email.split("@")[1]:
        await message.answer(
            "❌ Неверный формат email. Попробуйте еще раз:"
        )
        return
    
    data = await state.get_data()
    tariff_code = data.get("tariff_code")
    months = data.get("months")
    subscription_type = data.get("subscription_type", "individual")
    
    await create_request_final(
        message,
        tariff_code,
        months,
        subscription_type,
        user_email=email
    )
    await state.clear()


@router.callback_query(F.data.startswith("group:"))
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора группы для складчины"""
    try:
        parts = callback.data.split(":")
        group_id = int(parts[1])
        tariff_code = parts[2]
        months = int(parts[3])
        
        data = await state.get_data()
        subscription_type = data.get("subscription_type", "group")
        
        await create_request_final(
            callback,
            tariff_code,
            months,
            subscription_type,
            group_id=group_id
        )
        await state.clear()
        
    except Exception as e:
        print(f"[ERROR process_group_selection] {e}")
        await callback.message.edit_text(
            f"❌ Ошибка: {str(e)}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )
        await callback.answer("Ошибка", show_alert=True)


async def create_request_final(
    message_or_callback,
    tariff_code: str,
    months: int,
    subscription_type: str,
    group_id: int = None,
    user_email: str = None
):
    """Финальное создание заявки"""
    try:
        tg_id = message_or_callback.from_user.id
        
        print(f"[create_request_final] Создание заявки: tg_id={tg_id}, tariff_code={tariff_code}, months={months}, subscription_type={subscription_type}, group_id={group_id}, user_email={user_email}")
        
        result = await api.create_request(
            tg_id=tg_id,
            tariff_code=tariff_code,
            duration_months=months,
            subscription_type=subscription_type,
            group_id=group_id,
            user_email=user_email
        )

        print(f"[SUCCESS] Request created: {result}")

        success_message = (
            "✅ Заявка отправлена, ожидайте.\n"
            "Администратор скоро свяжется с вами для подтверждения."
        )
        
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(success_message)
            await message_or_callback.answer("Заявка создана успешно")
        else:
            await message_or_callback.answer(success_message)
            
    except Exception as e:
        print(f"[ERROR create_request_final] {e}")
        error_msg = str(e)
        error_message = (
            f"❌ Ошибка при создании заявки:\n{error_msg}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )
        
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(error_message)
            await message_or_callback.answer("Ошибка при создании заявки", show_alert=True)
        else:
            await message_or_callback.answer(error_message)


# Старые обработчики для совместимости
@router.callback_query(F.data.startswith("tariff:"))
async def choose_duration_old(callback: CallbackQuery):
    """Старый обработчик для совместимости"""
    tariff_code = callback.data.split(":")[1]
    await callback.message.edit_text(
        "Выберите срок подписки:",
        reply_markup=subscription.durations_kb(tariff_code, "group")
    )
