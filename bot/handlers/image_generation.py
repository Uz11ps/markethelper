import os
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from bot.states.image_generation import ImageGenerationStates
from bot.keyboards.inline import (
    generation_keyboard,
    skip_keyboard,
    result_keyboard,
    prompt_edit_keyboard,
    prompt_preview_keyboard,
    custom_prompt_preview_keyboard,
    aspect_ratio_keyboard,
    skip_text_keyboard
)
from bot.keyboards.main_menu import main_menu_kb
from bot.services.fal_service import FALService
from bot.services.prompt_generator import PromptGeneratorService
from bot.services.api_client import APIClient, InsufficientTokensError, APIClientError
from bot.loader import bot
from bot.utils import get_full_name

router = Router()
logger = logging.getLogger(__name__)
api_client = APIClient()

# Временная директория для сохранения фото
TEMP_PHOTO_DIR = "/tmp/bot_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)

# Хранилище для медиа-групп (альбомов)
media_groups = {}


async def safe_delete_message(message_or_callback):
    """Безопасное удаление сообщения (игнорирует ошибки если сообщение нельзя удалить)"""
    try:
        if isinstance(message_or_callback, CallbackQuery):
            if message_or_callback.message:
                await message_or_callback.message.delete()
        else:
            await message_or_callback.delete()
    except Exception:
        # Игнорируем ошибки удаления (сообщение может быть старше 48 часов или уже удалено)
        pass


async def delete_messages(chat_id: int, message_ids: list):
    """Удаление списка сообщений"""
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение {msg_id}: {e}")


async def charge_image_generation(message: Message, state: FSMContext, user_id: int):
    """Списание токенов перед генерацией изображения"""
    try:
        # Получаем стоимость модели из state
        data = await state.get_data()
        model_cost = data.get("model_cost", 5)
        
        # Используем endpoint для списания с указанием стоимости модели
        result = await api_client.charge_tokens(user_id, "image_generation", cost=model_cost)
        
        return result
    except InsufficientTokensError:
        await message.answer(
            "❌ Недостаточно токенов для генерации.\n"
            "Пополните баланс или обратитесь в поддержку."
        )
        await state.set_state(None)
        return None
    except APIClientError as exc:
        error_msg = str(exc)
        logger.error(f"[charge_image_generation] Ошибка API при списании токенов: {error_msg}")
        await message.answer(
            f"⚠️ Не удалось списать токены!\n\n"
            f"Ошибка: {error_msg}\n\n"
            f"Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )
        await state.set_state(None)
        return None
    except Exception as exc:
        logger.error(f"[charge_image_generation] Неожиданная ошибка при списании токенов: {exc}", exc_info=True)
        await message.answer(
            "⚠️ Произошла ошибка при списании токенов.\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )
        await state.set_state(None)
        return None


# Обработчики для кнопок "🖼 Картинки" и "📊 Инфографика"
@router.message(F.text == "🖼 Картинки")
async def start_images_mode(message: Message, state: FSMContext):
    """Начало режима генерации простых картинок"""
    await state.clear()
    await state.set_state(ImageGenerationStates.choosing_model_images)
    await state.update_data(mode="images")
    
    try:
        models = await api_client.get_image_models()
    except Exception as exc:
        logger.warning(f"Не удалось получить список моделей: {exc}")
        models = {}
    
    selected_model_key = None
    try:
        user_settings = await api_client.get_user_generation_settings(message.from_user.id)
        selected_model_key = user_settings.get("selected_model_key")
    except Exception as exc:
        logger.warning(f"Не удалось получить настройки пользователя: {exc}")
    
    try:
        profile = await api_client.get_profile(
            message.from_user.id,
            username=message.from_user.username,
            full_name=get_full_name(message.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        balance = 0
    
    from bot.keyboards.inline import model_selection_keyboard
    
    models_text = "\n".join([
        f"• {info.get('name', key)}: {info.get('cost', 0)} токенов - {info.get('description', '')}"
        for key, info in models.items()
    ]) if models else "• Nano Banana: 5 токенов - Быстрая генерация"
    
    selected_model_text = ""
    if selected_model_key and selected_model_key in models:
        selected_model = models[selected_model_key]
        selected_model_text = f"\n\n✅ <b>Ваша сохраненная модель:</b> {selected_model.get('name', selected_model_key)}"
    
    await message.answer(
        "🖼 <b>Генерация картинок</b>\n\n"
        "Выберите модель для генерации:\n\n"
        f"{models_text}"
        f"{selected_model_text}\n\n"
        f"💰 Ваш баланс: <b>{balance} токенов</b>",
        reply_markup=model_selection_keyboard(models, selected_model_key)
    )


@router.message(F.text == "📊 Инфографика")
async def start_infographics_mode(message: Message, state: FSMContext):
    """Начало режима генерации инфографики (с загрузкой фото)"""
    await state.clear()
    await state.set_state(ImageGenerationStates.choosing_model_infographics)
    await state.update_data(mode="infographics", product_photos=[], reference_photos=[])
    
    try:
        all_models = await api_client.get_image_models()
        # Для инфографики оставляем только nano-banana и pro (убираем sd/seedream)
        models = {k: v for k, v in all_models.items() if k in ["nano-banana", "pro"]}
    except Exception as exc:
        logger.warning(f"Не удалось получить список моделей: {exc}")
        models = {}
    
    selected_model_key = None
    try:
        user_settings = await api_client.get_user_generation_settings(message.from_user.id)
        selected_model_key = user_settings.get("selected_model_key")
        # Если выбранная модель не поддерживается для инфографики, сбрасываем выбор
        if selected_model_key and selected_model_key not in models:
            selected_model_key = None
    except Exception as exc:
        logger.warning(f"Не удалось получить настройки пользователя: {exc}")
    
    try:
        profile = await api_client.get_profile(
            message.from_user.id,
            username=message.from_user.username,
            full_name=get_full_name(message.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        balance = 0
    
    from bot.keyboards.inline import model_selection_keyboard
    
    models_text = "\n".join([
        f"• {info.get('name', key)}: {info.get('cost', 0)} токенов - {info.get('description', '')}"
        for key, info in models.items()
    ]) if models else "• Nano Banana: 5 токенов - Быстрая генерация"
    
    selected_model_text = ""
    if selected_model_key and selected_model_key in models:
        selected_model = models[selected_model_key]
        selected_model_text = f"\n\n✅ <b>Ваша сохраненная модель:</b> {selected_model.get('name', selected_model_key)}"
    
    await message.answer(
        "📊 <b>Генерация инфографики</b>\n\n"
        "Выберите модель для генерации:\n\n"
        f"{models_text}"
        f"{selected_model_text}\n\n"
        f"💰 Ваш баланс: <b>{balance} токенов</b>\n\n"
        "После выбора модели вы сможете загрузить фото товара и референсы.",
        reply_markup=model_selection_keyboard(models, selected_model_key)
    )


# Обработчик для кнопки "🎨Генерация карточки" удалён - теперь используется inline кнопка из профиля


@router.callback_query(F.data == "generate_image")
async def start_generation(callback: CallbackQuery, state: FSMContext):
    """Начало процесса генерации изображения - выбор модели"""
    await callback.answer()
    await safe_delete_message(callback)

    await state.clear()
    await state.set_state(ImageGenerationStates.choosing_model)
    # По умолчанию режим инфографики для этого обработчика
    await state.update_data(mode="infographics", product_photos=[], reference_photos=[])

    try:
        all_models = await api_client.get_image_models()
        # Для инфографики оставляем только nano-banana и pro (убираем sd/seedream)
        models = {k: v for k, v in all_models.items() if k in ["nano-banana", "pro"]}
    except Exception as exc:
        logger.warning(f"Не удалось получить список моделей: {exc}")
        models = {}
    
    # Получаем сохраненную модель пользователя
    selected_model_key = None
    try:
        user_settings = await api_client.get_user_generation_settings(callback.from_user.id)
        selected_model_key = user_settings.get("selected_model_key")
    except Exception as exc:
        logger.warning(f"Не удалось получить настройки пользователя: {exc}")
    
    try:
        profile = await api_client.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        profile = {}
    balance = profile.get("bonus_balance", 0) if profile else 0

    from bot.keyboards.inline import model_selection_keyboard
    
    # Формируем текст с информацией о моделях
    if models:
        models_text = "\n".join([
            f"• {info.get('name', key)}: {info.get('cost', 0)} токенов - {info.get('description', '')}"
            for key, info in models.items()
        ])
    else:
        models_text = "• Nano Banana: 5 токенов - Быстрая генерация"
    
    selected_model_text = ""
    if selected_model_key and selected_model_key in models:
        selected_model = models[selected_model_key]
        selected_model_text = f"\n\n✅ <b>Ваша сохраненная модель:</b> {selected_model.get('name', selected_model_key)}"

    await callback.message.answer(
        "🎨 <b>Генерация карточки товара</b>\n\n"
        "Выберите модель для генерации:\n\n"
        f"{models_text}"
        f"{selected_model_text}\n\n"
        f"💰 Ваш баланс: <b>{balance} токенов</b>",
        reply_markup=model_selection_keyboard(models, selected_model_key)
    )


@router.callback_query(F.data.startswith("select_model:"))
async def select_model(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора модели генерации"""
    await callback.answer()
    
    model_key = callback.data.split(":")[1]
    data = await state.get_data()
    mode = data.get("mode", "infographics")  # По умолчанию инфографика для совместимости
    
    # Проверяем, что для инфографики не выбрана модель sd/seedream
    if mode == "infographics" and model_key == "sd":
        await safe_delete_message(callback)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="❌ Модель Seedream не поддерживает генерацию инфографики с фото товара и референсами.\n\n"
                 "Пожалуйста, выберите модель Nano Banana или Nano Banana Pro.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к выбору модели", callback_data="back_to_menu")]
            ])
        )
        return
    
    # Удаляем предыдущее сообщение (если оно еще существует)
    await safe_delete_message(callback)
    
    try:
        models = await api_client.get_image_models()
        selected_model = models.get(model_key, {})
        model_name = selected_model.get("name", model_key)
        model_cost = selected_model.get("cost", 5)
        model_id = selected_model.get("model_id", "fal-ai/nano-banana")
        
        # Сохраняем выбранную модель в настройках пользователя
        try:
            await api_client.update_user_generation_settings(
                callback.from_user.id,
                selected_model_key=model_key
            )
        except Exception as e:
            logger.warning(f"Не удалось сохранить модель в настройках: {e}")
    except Exception as exc:
        logger.warning(f"Не удалось получить информацию о модели: {exc}")
        model_name = model_key
        model_cost = 5
        model_id = "fal-ai/nano-banana"
    
    await state.update_data(
        selected_model=model_key,
        model_name=model_name,
        model_cost=model_cost,
        model_id=model_id
    )
    
    try:
        profile = await api_client.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        balance = 0
    
    # Разделяем логику для разных режимов
    if mode == "images":
        # Режим простых картинок - запрашиваем промпт
        await state.set_state(ImageGenerationStates.waiting_for_image_prompt)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"✅ Выбрана модель: <b>{model_name}</b>\n"
                 f"💰 Стоимость: <b>{model_cost} токенов</b>\n\n"
                 f"💼 Ваш баланс: <b>{balance} токенов</b>\n\n"
                 "📝 Введите текстовый промпт для генерации картинки:\n\n"
                 "Опишите, что вы хотите увидеть на изображении. Например:\n"
                 "• 'Красивый закат над морем'\n"
                 "• 'Кот в космическом костюме'\n"
                 "• 'Современный интерьер гостиной'",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
            ])
        )
    else:
        # Режим инфографики - продолжаем стандартный поток
        await state.set_state(ImageGenerationStates.choosing_aspect_ratio)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"✅ Выбрана модель: <b>{model_name}</b>\n"
                 f"💰 Стоимость: <b>{model_cost} токенов</b>\n\n"
                 "Выберите формат изображения для вашей площадки:\n\n"
                 f"📦 Доступно фото товара: загрузите до 5 штук.\n"
                 f"🎯 Референсы: до 5 примеров стиля.\n"
                 f"💼 Ваш баланс: <b>{balance} токенов</b>.\n\n"
                 "Токены списываются при запуске генерации.",
            reply_markup=aspect_ratio_keyboard()
        )


@router.callback_query(F.data.startswith("aspect_"))
async def choose_aspect_ratio(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора формата изображения"""
    await callback.answer()
    await safe_delete_message(callback)

    aspect_ratio_map = {
        "aspect_3_4": "3:4",
        "aspect_2_3": "2:3",
        "aspect_1_1": "1:1"
    }

    aspect_ratio = aspect_ratio_map.get(callback.data, "3:4")
    await state.update_data(aspect_ratio=aspect_ratio)

    await state.set_state(ImageGenerationStates.waiting_for_product_photos)

    await callback.message.answer(
        f"✅ Выбран формат: <b>{aspect_ratio}</b>\n\n"
        "📸 Теперь отправьте от 1 до 5 фотографий вашего товара.\n"
        "После отправки всех фото нажмите кнопку 'Готово'.",
        reply_markup=skip_keyboard("product_photos_done")
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_product_photos), F.photo)
async def collect_product_photos(message: Message, state: FSMContext):
    """Сбор фотографий товара (поддержка альбомов)"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])

    if len(product_photos) >= 5:
        await message.answer("⚠️ Максимум 5 фотографий товара!")
        return

    # Проверяем, отправлено ли несколько фото разом (альбом)
    media_group_id = message.media_group_id

    if media_group_id:
        # Это альбом - собираем все фото из группы
        if media_group_id not in media_groups:
            media_groups[media_group_id] = []

        media_groups[media_group_id].append(message)

        # Только первое сообщение должно обработать весь альбом
        is_first = len(media_groups[media_group_id]) == 1

        if not is_first:
            return

        # Ждём 1 секунду, чтобы получить все фото из альбома
        await asyncio.sleep(1)

        # Проверяем, что группа ещё существует (может быть удалена другим обработчиком)
        if media_group_id not in media_groups:
            return

        # Обрабатываем все фото из альбома
        messages_to_process = media_groups[media_group_id]
        del media_groups[media_group_id]

        uploaded_count = 0
        for msg in messages_to_process:
            if len(product_photos) >= 5:
                break

            photo = msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)

            # Скачиваем фото
            file_path = os.path.join(TEMP_PHOTO_DIR, f"{msg.from_user.id}_product_{len(product_photos)}.jpg")
            await bot.download_file(file_info.file_path, file_path)

            # Загружаем в FAL storage
            fal_url = await FALService.upload_image_to_fal(file_path)
            product_photos.append(fal_url)
            uploaded_count += 1

        await state.update_data(product_photos=product_photos)

        # Показываем краткое подтверждение (без кнопок)
        confirm_msg = await message.answer(
            f"✅ Добавлено {uploaded_count} фото товара! Всего: {len(product_photos)}/5"
        )

        # Удаляем подтверждение через 2 секунды
        await asyncio.sleep(2)
        try:
            await confirm_msg.delete()
        except:
            pass

        # Показываем постоянное сообщение с кнопкой "Готово"
        await message.answer(
            f"📸 <b>Фото товара загружены: {len(product_photos)}/5</b>\n\n"
            f"Отправьте ещё фото или нажмите 'Готово' для продолжения.",
            reply_markup=skip_keyboard("product_photos_done")
        )
    else:
        # Одиночное фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        # Скачиваем фото
        file_path = os.path.join(TEMP_PHOTO_DIR, f"{message.from_user.id}_product_{len(product_photos)}.jpg")
        await bot.download_file(file_info.file_path, file_path)

        # Загружаем в FAL storage
        fal_url = await FALService.upload_image_to_fal(file_path)

        product_photos.append(fal_url)
        await state.update_data(product_photos=product_photos)

        # Показываем краткое подтверждение (без кнопок)
        confirm_msg = await message.answer(
            f"✅ Фото товара добавлено! Всего: {len(product_photos)}/5"
        )

        # Удаляем подтверждение через 2 секунды
        await asyncio.sleep(2)
        try:
            await confirm_msg.delete()
        except:
            pass

        # Показываем постоянное сообщение с кнопкой "Готово"
        await message.answer(
            f"📸 <b>Фото товара загружены: {len(product_photos)}/5</b>\n\n"
            f"Отправьте ещё фото или нажмите 'Готово' для продолжения.",
            reply_markup=skip_keyboard("product_photos_done")
        )


@router.callback_query(F.data == "product_photos_done")
async def product_photos_done(callback: CallbackQuery, state: FSMContext):
    """Завершение сбора фото товара, переход к референсам"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])

    if not product_photos:
        await callback.answer("❌ Отправьте хотя бы одно фото товара!", show_alert=True)
        return

    await callback.answer()
    await safe_delete_message(callback)
    await state.set_state(ImageGenerationStates.waiting_for_reference_photos)

    await callback.message.answer(
        "📸 <b>Отлично!</b>\n\n"
        f"Фото товара получено: {len(product_photos)} шт.\n\n"
        "Теперь отправьте от 1 до 5 референсных изображений "
        "(примеры карточек товаров, стиль которых вы хотите использовать).\n\n"
        "После отправки всех референсов нажмите 'Готово'.",
        reply_markup=skip_keyboard("reference_photos_done")
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_reference_photos), F.photo)
async def collect_reference_photos(message: Message, state: FSMContext):
    """Сбор референсных фотографий (поддержка альбомов)"""
    data = await state.get_data()
    reference_photos = data.get("reference_photos", [])

    if len(reference_photos) >= 5:
        await message.answer("⚠️ Максимум 5 референсных изображений!")
        return

    # Проверяем, отправлено ли несколько фото разом (альбом)
    media_group_id = message.media_group_id

    if media_group_id:
        # Это альбом - собираем все фото из группы
        if media_group_id not in media_groups:
            media_groups[media_group_id] = []

        media_groups[media_group_id].append(message)

        # Только первое сообщение должно обработать весь альбом
        is_first = len(media_groups[media_group_id]) == 1

        if not is_first:
            return

        # Ждём 1 секунду, чтобы получить все фото из альбома
        await asyncio.sleep(1)

        # Проверяем, что группа ещё существует (может быть удалена другим обработчиком)
        if media_group_id not in media_groups:
            return

        # Обрабатываем все фото из альбома
        messages_to_process = media_groups[media_group_id]
        del media_groups[media_group_id]

        uploaded_count = 0
        for msg in messages_to_process:
            if len(reference_photos) >= 5:
                break

            photo = msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)

            # Скачиваем фото
            file_path = os.path.join(TEMP_PHOTO_DIR, f"{msg.from_user.id}_ref_{len(reference_photos)}.jpg")
            await bot.download_file(file_info.file_path, file_path)

            # Загружаем в FAL storage
            fal_url = await FALService.upload_image_to_fal(file_path)
            reference_photos.append(fal_url)
            uploaded_count += 1

        await state.update_data(reference_photos=reference_photos)

        # Показываем краткое подтверждение (без кнопок)
        confirm_msg = await message.answer(
            f"✅ Добавлено {uploaded_count} референсов! Всего: {len(reference_photos)}/5"
        )

        # Удаляем подтверждение через 2 секунды
        await asyncio.sleep(2)
        try:
            await confirm_msg.delete()
        except:
            pass

        # Показываем постоянное сообщение с кнопкой "Готово"
        await message.answer(
            f"📸 <b>Референсы загружены: {len(reference_photos)}/5</b>\n\n"
            f"Отправьте ещё референсы или нажмите 'Готово' для продолжения.",
            reply_markup=skip_keyboard("reference_photos_done")
        )
    else:
        # Одиночное фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        # Скачиваем фото
        file_path = os.path.join(TEMP_PHOTO_DIR, f"{message.from_user.id}_ref_{len(reference_photos)}.jpg")
        await bot.download_file(file_info.file_path, file_path)

        # Загружаем в FAL storage
        fal_url = await FALService.upload_image_to_fal(file_path)

        reference_photos.append(fal_url)
        await state.update_data(reference_photos=reference_photos)

        # Показываем краткое подтверждение (без кнопок)
        confirm_msg = await message.answer(
            f"✅ Референс добавлен! Всего: {len(reference_photos)}/5"
        )

        # Удаляем подтверждение через 2 секунды
        await asyncio.sleep(2)
        try:
            await confirm_msg.delete()
        except:
            pass

        # Показываем постоянное сообщение с кнопкой "Готово"
        await message.answer(
            f"📸 <b>Референсы загружены: {len(reference_photos)}/5</b>\n\n"
            f"Отправьте ещё референсы или нажмите 'Готово' для продолжения.",
            reply_markup=skip_keyboard("reference_photos_done")
        )


@router.callback_query(F.data == "reference_photos_done")
async def reference_photos_done(callback: CallbackQuery, state: FSMContext):
    """Завершение сбора референсов, переход к вводу текста на карточке"""
    data = await state.get_data()
    reference_photos = data.get("reference_photos", [])

    if not reference_photos:
        await callback.answer("❌ Отправьте хотя бы один референс!", show_alert=True)
        return

    await callback.answer()
    await safe_delete_message(callback)
    await state.set_state(ImageGenerationStates.waiting_for_card_text)

    product_photos = data.get("product_photos", [])

    await callback.message.answer(
        "✅ <b>Отлично!</b>\n\n"
        f"📦 Фото товара: {len(product_photos)} шт.\n"
        f"🎨 Референсов: {len(reference_photos)} шт.\n\n"
        "📝 <b>Хотите добавить текст на карточку?</b>\n\n"
        "Введите текст, который должен отображаться на карточке товара\n"
        "(например: 'SALE -50%', 'NEW', 'TOP SELLER' и т.д.)\n\n"
        "Или нажмите 'Пропустить', если текст не нужен.",
        reply_markup=skip_text_keyboard()
    )


@router.callback_query(F.data == "skip_card_text")
async def skip_card_text(callback: CallbackQuery, state: FSMContext):
    """Пропуск текста на карточке"""
    await callback.answer()
    await state.update_data(card_text=None)
    await proceed_to_prompt_choice(callback.message, state)


@router.message(StateFilter(ImageGenerationStates.waiting_for_card_text))
async def receive_card_text(message: Message, state: FSMContext):
    """Получение текста для карточки"""
    card_text = message.text.strip()

    if len(card_text) > 100:
        await message.answer("⚠️ Текст слишком длинный. Максимум 100 символов.")
        return

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    await state.update_data(card_text=card_text)

    # Показываем подтверждение
    confirm_msg = await message.answer(
        f"✅ Текст на карточке: <b>{card_text}</b>\n\n"
        "Переходим к настройке промпта..."
    )

    # Удаляем подтверждение через 2 секунды
    await asyncio.sleep(2)
    try:
        await confirm_msg.delete()
    except:
        pass

    await proceed_to_prompt_choice(message, state)


async def proceed_to_prompt_choice(message: Message, state: FSMContext):
    """Переход к выбору способа создания промпта"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])

    await state.set_state(ImageGenerationStates.choosing_prompt_mode)
    
    # Получаем стоимость модели из state, если не указана - получаем из настроек
    model_cost = data.get("model_cost")
    if model_cost is None:
        try:
            models = await api_client.get_image_models()
            selected_model_key = data.get("selected_model")
            if selected_model_key and selected_model_key in models:
                model_cost = models[selected_model_key].get("cost", 5)
            else:
                # Используем стоимость nano-banana по умолчанию
                model_cost = models.get("nano-banana", {}).get("cost", 5) if models else 5
        except Exception as exc:
            logger.warning(f"Не удалось получить стоимость модели: {exc}")
            model_cost = 5

    await message.answer(
        "✅ <b>Готово!</b>\n\n"
        f"📦 Фото товара: {len(product_photos)} шт.\n"
        f"🎨 Референсов: {len(reference_photos)} шт.\n\n"
        f"💰 Стоимость генерации: <b>{model_cost} токенов</b>.\n"
        "Выберите способ создания промпта:",
        reply_markup=prompt_edit_keyboard()
    )


@router.callback_query(F.data == "use_auto_prompt")
async def use_auto_prompt(callback: CallbackQuery, state: FSMContext):
    """Сгенерировать и показать автоматический промпт для предварительного просмотра"""
    await callback.answer()
    
    data = await state.get_data()
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    card_text = data.get("card_text")
    
    await state.set_state(ImageGenerationStates.previewing_prompt)
    
    # Список ID сообщений для удаления
    temp_messages = []
    
    try:
        msg1 = await callback.message.answer("🤖 Анализирую товар и создаю промпт...")
        temp_messages.append(msg1.message_id)
        
        prompt_data = await PromptGeneratorService.generate_prompt_from_images(
            product_image_urls=product_photos,
            reference_image_urls=reference_photos,
            tg_id=callback.from_user.id
        )
        
        generated_prompt = prompt_data["generated_text_prompt"]
        analysis = prompt_data["deconstruction_analysis"]
        logger.info(f"[IMAGE_GENERATION] Промпт сгенерирован GPT-4o (длина: {len(generated_prompt)} символов):\n{generated_prompt}")
        
        # Если указан текст на карточке, добавляем его в промпт
        original_prompt = generated_prompt
        if card_text:
            generated_prompt = f"{generated_prompt}. Add text on the card: '{card_text}'"
            logger.info(f"[IMAGE_GENERATION] Добавлен текст на карточку. Промпт до: {original_prompt[:200]}... Промпт после: {generated_prompt[:200]}...")
        
        # Сохраняем промпт и анализ
        await state.update_data(generated_prompt=generated_prompt, analysis=analysis)
        
        # Удаляем временные сообщения
        await delete_messages(callback.message.chat.id, temp_messages)
        
        # Показываем пользователю промпт с возможностью редактирования
        await callback.message.answer(
            f"🤖 <b>Автоматически сгенерированный промпт:</b>\n\n"
            f"📝 <b>Товар:</b> {analysis['product_identified']}\n"
            f"🎨 <b>Стиль:</b> {analysis['style_source']}\n"
            f"📐 <b>Композиция:</b> {analysis['layout_source']}\n"
            f"🎨 <b>Палитра:</b> {analysis['palette_source']}\n\n"
            f"<b>Промпт:</b>\n<code>{generated_prompt}</code>\n\n"
            f"Вы можете использовать этот промпт или отредактировать его:",
            reply_markup=prompt_preview_keyboard()
        )
        
    except Exception as e:
        # Удаляем временные сообщения даже при ошибке
        await delete_messages(callback.message.chat.id, temp_messages)
        
        await callback.message.answer(
            f"❌ <b>Ошибка при генерации промпта:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Попробуйте ещё раз позже."
        )


@router.callback_query(F.data == "confirm_auto_prompt")
async def confirm_auto_prompt(callback: CallbackQuery, state: FSMContext):
    """Подтверждение использования автоматически сгенерированного промпта"""
    await callback.answer()
    await safe_delete_message(callback)

    data = await state.get_data()
    generated_prompt = data.get("generated_prompt")
    
    if not generated_prompt:
        await callback.message.answer("❌ Ошибка: промпт не найден. Попробуйте ещё раз.")
        return
    
    await generate_with_confirmed_prompt(
        callback.message,
        state,
        generated_prompt,
        user_id=callback.from_user.id
    )


@router.callback_query(F.data == "edit_auto_prompt")
async def edit_auto_prompt(callback: CallbackQuery, state: FSMContext):
    """Редактирование автоматически сгенерированного промпта"""
    await callback.answer()
    await safe_delete_message(callback)
    
    data = await state.get_data()
    generated_prompt = data.get("generated_prompt")
    
    if not generated_prompt:
        await callback.message.answer("❌ Ошибка: промпт не найден. Попробуйте ещё раз.")
        return
    
    await state.set_state(ImageGenerationStates.editing_auto_prompt)
    
    await callback.message.answer(
        f"✏️ <b>Редактирование промпта</b>\n\n"
        f"<b>Текущий промпт:</b>\n<code>{generated_prompt}</code>\n\n"
        f"Введите ваш отредактированный промпт:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оставить как есть", callback_data="confirm_auto_prompt")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])
    )


@router.message(StateFilter(ImageGenerationStates.editing_auto_prompt))
async def receive_edited_prompt(message: Message, state: FSMContext):
    """Получение отредактированного промпта от пользователя"""
    edited_prompt = message.text.strip()
    
    if len(edited_prompt) < 10:
        await message.answer("⚠️ Промпт слишком короткий. Опишите детальнее (минимум 10 символов).")
        return
    
    await state.update_data(generated_prompt=edited_prompt)
    
    await message.answer(
        f"✅ <b>Промпт обновлён!</b>\n\n"
        f"<code>{edited_prompt}</code>\n\n"
        "Начинаю генерацию...",
        reply_markup=None
    )
    
    await generate_with_confirmed_prompt(
        message,
        state,
        edited_prompt,
        user_id=message.from_user.id
    )


async def generate_with_confirmed_prompt(message: Message, state: FSMContext, prompt: str, user_id: int | None = None):
    """Генерация изображения с подтверждённым промптом (без повторной генерации промпта)"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    aspect_ratio = data.get("aspect_ratio", "3:4")
    card_text = data.get("card_text")
    
    await state.set_state(ImageGenerationStates.generating)
    
    # Список ID сообщений для удаления
    temp_messages = []
    
    try:
        tg_id = user_id or message.chat.id
        charge = await charge_image_generation(message, state, tg_id)
        if not charge:
            return

        # Если указан текст на карточке, добавляем его в промпт
        original_prompt = prompt
        if card_text:
            prompt = f"{prompt}. Add text on the card: '{card_text}'"
            logger.info(f"[IMAGE_GENERATION] Добавлен текст на карточку. Промпт до: {original_prompt[:200]}... Промпт после: {prompt[:200]}...")

        data = await state.get_data()
        model_name = data.get("model_name", "Nano Banana")
        model_id = data.get("model_id")
        
        # Если model_id не установлен, пытаемся получить из настроек
        if not model_id:
            try:
                models = await api_client.get_image_models()
                selected_model_key = data.get("selected_model")
                if selected_model_key and selected_model_key in models:
                    selected_model = models[selected_model_key]
                    model_id = selected_model.get("model_id")
                    logger.info(f"[IMAGE_GENERATION] Получен model_id из настроек: {model_id}")
            except Exception as e:
                logger.warning(f"[IMAGE_GENERATION] Не удалось получить model_id из настроек: {e}")
        
        logger.info(f"[IMAGE_GENERATION] Используется модель: model_name={model_name}, model_id={model_id}")
        logger.info(f"[IMAGE_GENERATION] Промпт перед отправкой в FAL (длина: {len(prompt)} символов):\n{prompt}")
        logger.info(f"[IMAGE_GENERATION] Параметры: product_images={len(product_photos)}, reference_images={len(reference_photos)}, aspect_ratio={aspect_ratio}, model_id={model_id}")
        
        msg1 = await message.answer(
            f"🎨 Генерирую изображение через {model_name}...\n\n"
            f"💰 Списано: <b>{charge['cost']} токенов</b>\n"
            f"💼 Остаток: <b>{charge['balance']} токенов</b>"
        )
        temp_messages.append(msg1.message_id)
        
        image_urls = await FALService.generate_product_image(
            prompt=prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio,
            model_id=model_id
        )
        
        if not image_urls:
            # Удаляем временные сообщения
            await delete_messages(message.chat.id, temp_messages)
            
            await message.answer(
                "❌ Не удалось сгенерировать изображение. Попробуйте ещё раз."
            )
            await state.clear()
            return
        
        # Сохраняем результат
        await state.update_data(last_generated_image=image_urls[0], generated_prompt=prompt)
        
        # Удаляем все временные сообщения
        await delete_messages(message.chat.id, temp_messages)
        
        # Отправляем результат с кнопками
        await message.answer_photo(
            photo=image_urls[0],
            caption=(
                "✨ <b>Готово!</b>\n\n"
                "Ваша карточка товара успешно сгенерирована!\n\n"
                "Выберите действие:"
            ),
            reply_markup=result_keyboard(image_url=image_urls[0])
        )
        
        logger.info(f"Пользователь успешно сгенерировал изображение")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        
        # Удаляем временные сообщения даже при ошибке
        await delete_messages(message.chat.id, temp_messages)
        
        await message.answer(
            f"❌ <b>Ошибка при генерации:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Попробуйте ещё раз позже."
        )
    
    finally:
        await state.set_state(None)


@router.callback_query(F.data == "edit_prompt")
async def edit_prompt_handler(callback: CallbackQuery, state: FSMContext):
    """Запрос на редактирование промпта"""
    await callback.answer()
    await safe_delete_message(callback)
    await state.set_state(ImageGenerationStates.waiting_for_custom_prompt)

    await callback.message.answer(
        "✏️ <b>Введите ваш промпт для генерации</b>\n\n"
        "Опишите, как должна выглядеть карточка товара.\n"
        "Например: 'Product on white background, professional lighting, centered composition'\n\n"
        "Или нажмите кнопку ниже для автоматической генерации.",
        reply_markup=prompt_edit_keyboard()
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_image_prompt))
async def receive_image_prompt(message: Message, state: FSMContext):
    """Обработка ввода промпта для простых картинок"""
    prompt = message.text.strip()
    
    if len(prompt) < 5:
        await message.answer("⚠️ Промпт слишком короткий. Опишите детальнее (минимум 5 символов).")
        return
    
    data = await state.get_data()
    model_name = data.get("model_name", "Nano Banana")
    model_cost = data.get("model_cost", 5)
    
    try:
        profile = await api_client.get_profile(
            message.from_user.id,
            username=message.from_user.username,
            full_name=get_full_name(message.from_user),
        )
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as exc:
        logger.warning(f"Не удалось получить профиль пользователя: {exc}")
        balance = 0
    
    if balance < model_cost:
        await message.answer(
            f"❌ Недостаточно токенов для генерации.\n"
            f"💰 Требуется: {model_cost} токенов\n"
            f"💼 Ваш баланс: {balance} токенов\n\n"
            "Пополните баланс или обратитесь в поддержку."
        )
        await state.clear()
        return
    
    # Сохраняем промпт и переходим к генерации
    await state.update_data(custom_prompt=prompt, aspect_ratio="3:4")
    
    # Генерируем изображение с кастомным промптом
    await generate_with_custom_prompt(message, state, prompt)


@router.message(StateFilter(ImageGenerationStates.waiting_for_custom_prompt))
async def receive_custom_prompt(message: Message, state: FSMContext):
    """Получение кастомного промпта от пользователя (для генерации или настроек)"""
    data = await state.get_data()
    
    # Проверяем, редактируем ли мы промпт в настройках
    if data.get("editing_generation_prompt"):
        # Сохраняем промпт в настройках пользователя
        custom_prompt = message.text.strip()
        if len(custom_prompt) < 10:
            await message.answer("⚠️ Промпт слишком короткий. Опишите детальнее (минимум 10 символов).")
            return
        
        try:
            await api_client.update_user_generation_settings(
                message.from_user.id,
                custom_prompt=custom_prompt
            )
            await message.answer(
                "✅ Промпт успешно сохранен!\n\n"
                "Теперь этот промпт будет использоваться для генерации вместо системного."
            )
            await state.clear()
            return
        except Exception as e:
            logger.error(f"Ошибка сохранения промпта: {e}")
            await message.answer(f"❌ Ошибка сохранения промпта: {str(e)}")
            return
    
    # Обычная логика для генерации
    custom_prompt = message.text.strip()

    if len(custom_prompt) < 10:
        await message.answer("⚠️ Промпт слишком короткий. Опишите детальнее (минимум 10 символов).")
        return

    await state.update_data(custom_prompt=custom_prompt)
    await state.set_state(ImageGenerationStates.confirming_custom_prompt)

    await message.answer(
        f"📝 <b>Ваш промпт:</b>\n<code>{custom_prompt}</code>\n\n"
        "Нажмите «Запустить генерацию» или измените текст.",
        reply_markup=custom_prompt_preview_keyboard()
    )


@router.callback_query(F.data == "confirm_custom_prompt")
async def confirm_custom_prompt(callback: CallbackQuery, state: FSMContext):
    """Запуск генерации по кастомному промпту"""
    await callback.answer()
    await safe_delete_message(callback)

    data = await state.get_data()
    custom_prompt = data.get("custom_prompt")

    if not custom_prompt:
        await callback.message.answer("❌ Кастомный промпт не найден. Введите его заново.")
        await state.set_state(ImageGenerationStates.waiting_for_custom_prompt)
        return

    await generate_with_custom_prompt(callback.message, state, custom_prompt)


@router.callback_query(F.data == "reenter_custom_prompt")
async def reenter_custom_prompt(callback: CallbackQuery, state: FSMContext):
    """Повторный ввод кастомного промпта"""
    await callback.answer()
    await safe_delete_message(callback)
    await state.set_state(ImageGenerationStates.waiting_for_custom_prompt)

    await callback.message.answer(
        "✏️ <b>Введите новый промпт</b>\n\n"
        "Опишите вид карточки или вернитесь к автоматической генерации.",
        reply_markup=prompt_edit_keyboard()
    )


async def generate_with_ai_prompt(message: Message, state: FSMContext):
    """Генерация с AI промптом"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    aspect_ratio = data.get("aspect_ratio", "3:4")
    card_text = data.get("card_text")
    mode = data.get("mode", "infographics")  # По умолчанию инфографика
    
    # Получаем сохраненные настройки пользователя
    try:
        user_settings = await api_client.get_user_generation_settings(message.from_user.id)
        # Используем сохраненную модель, если она не выбрана в текущей сессии
        if not data.get("selected_model") and user_settings.get("selected_model_key"):
            models = await api_client.get_image_models()
            selected_model_key = user_settings.get("selected_model_key")
            # Для инфографики не используем модель sd/seedream
            if mode == "infographics" and selected_model_key == "sd":
                logger.warning(f"Модель Seedream не поддерживается для инфографики, используем nano-banana")
                selected_model_key = "nano-banana"
            
            if selected_model_key in models:
                selected_model = models[selected_model_key]
                data["selected_model"] = selected_model_key
                data["model_name"] = selected_model.get("name", selected_model_key)
                data["model_cost"] = selected_model.get("cost", 5)
                data["model_id"] = selected_model.get("model_id", "fal-ai/nano-banana")
                await state.update_data(**data)
    except Exception as e:
        logger.warning(f"Не удалось получить настройки пользователя: {e}")

    await state.set_state(ImageGenerationStates.generating)

    # Список ID сообщений для удаления
    temp_messages = []

    msg1 = await message.answer(
        "⏳ <b>Начинаю генерацию...</b>\n\n"
        f"📦 Фото товара: {len(product_photos)} шт.\n"
        f"🎨 Референсов: {len(reference_photos)} шт.\n"
        f"📐 Формат: {aspect_ratio}\n\n"
        "Это может занять 1-2 минуты. Пожалуйста, подождите..."
    )
    temp_messages.append(msg1.message_id)

    try:
        # Проверяем, есть ли сохраненный кастомный промпт пользователя
        user_custom_prompt = None
        try:
            user_settings = await api_client.get_user_generation_settings(message.from_user.id)
            user_custom_prompt = user_settings.get("custom_prompt")
        except Exception as e:
            logger.warning(f"Не удалось получить настройки пользователя: {e}")
        
        # Если есть кастомный промпт, используем его вместо генерации
        if user_custom_prompt:
            msg2 = await message.answer("📝 Использую ваш сохраненный промпт...")
            temp_messages.append(msg2.message_id)
            generated_prompt = user_custom_prompt
            analysis = {
                "product_identified": "Используется кастомный промпт",
                "style_source": "Из настроек пользователя",
                "layout_source": "Из настроек пользователя",
                "palette_source": "Из настроек пользователя"
            }
        else:
            # Шаг 1: Генерация промпта через GPT-4o
            msg2 = await message.answer("🤖 Анализирую товар и создаю промпт...")
            temp_messages.append(msg2.message_id)

            prompt_data = await PromptGeneratorService.generate_prompt_from_images(
                product_image_urls=product_photos,
                reference_image_urls=reference_photos,
                tg_id=message.from_user.id
            )

            generated_prompt = prompt_data["generated_text_prompt"]
            analysis = prompt_data["deconstruction_analysis"]
            logger.info(f"[IMAGE_GENERATION] Промпт сгенерирован выбранной GPT моделью (длина: {len(generated_prompt)} символов):\n{generated_prompt}")

        # Если указан текст на карточке, добавляем его в промпт
        if card_text:
            original_prompt = generated_prompt
            generated_prompt = f"{generated_prompt}. Add text on the card: '{card_text}'"
            logger.info(f"[IMAGE_GENERATION] Добавлен текст на карточку. Промпт до: {original_prompt[:200]}... Промпт после: {generated_prompt[:200]}...")

        # Сохраняем промпт и анализ
        await state.update_data(generated_prompt=generated_prompt, analysis=analysis)

        # Показываем пользователю анализ (временно)
        msg3 = await message.answer(
            f"✅ <b>Анализ завершён!</b>\n\n"
            f"📝 <b>Товар:</b> {analysis['product_identified']}\n"
            f"🎨 <b>Стиль:</b> {analysis['style_source']}\n"
            f"📐 <b>Композиция:</b> {analysis['layout_source']}\n"
            f"🎨 <b>Палитра:</b> {analysis['palette_source']}\n\n"
            f"<b>Промпт:</b>\n<code>{generated_prompt}</code>"
        )
        temp_messages.append(msg3.message_id)

        tg_id = message.chat.id
        charge = await charge_image_generation(message, state, tg_id)
        if not charge:
            return

        data = await state.get_data()
        model_name = data.get("model_name", "Nano Banana")
        model_id = data.get("model_id")
        
        # Если model_id не установлен, пытаемся получить из настроек
        if not model_id:
            try:
                models = await api_client.get_image_models()
                selected_model_key = data.get("selected_model")
                if selected_model_key and selected_model_key in models:
                    selected_model = models[selected_model_key]
                    model_id = selected_model.get("model_id")
                    logger.info(f"[generate_with_ai_prompt] Получен model_id из настроек: {model_id}")
            except Exception as e:
                logger.warning(f"[generate_with_ai_prompt] Не удалось получить model_id из настроек: {e}")
        
        logger.info(f"[IMAGE_GENERATION] Используется модель: model_name={model_name}, model_id={model_id}")
        logger.info(f"[IMAGE_GENERATION] Промпт перед отправкой в FAL (длина: {len(generated_prompt)} символов):\n{generated_prompt}")
        logger.info(f"[IMAGE_GENERATION] Параметры: product_images={len(product_photos)}, reference_images={len(reference_photos)}, aspect_ratio={aspect_ratio}, model_id={model_id}")
        
        # Шаг 2: Генерация изображения через FAL
        msg4 = await message.answer(
            f"🎨 Генерирую изображение через {model_name}...\n\n"
            f"💰 Списано: <b>{charge['cost']} токенов</b>\n"
            f"💼 Остаток: <b>{charge['balance']} токенов</b>"
        )
        temp_messages.append(msg4.message_id)
        
        image_urls = await FALService.generate_product_image(
            prompt=generated_prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio,
            model_id=model_id
        )

        if not image_urls:
            # Удаляем временные сообщения
            await delete_messages(message.chat.id, temp_messages)

            await message.answer(
                "❌ Не удалось сгенерировать изображение. Попробуйте ещё раз."
            )
            await state.clear()
            return

        # Сохраняем результат
        await state.update_data(last_generated_image=image_urls[0])

        # Удаляем все временные сообщения
        await delete_messages(message.chat.id, temp_messages)

        # Отправляем результат с кнопками
        await message.answer_photo(
            photo=image_urls[0],
            caption=(
                "✨ <b>Готово!</b>\n\n"
                "Ваша карточка товара успешно сгенерирована!\n\n"
                "Выберите действие:"
            ),
            reply_markup=result_keyboard(image_url=image_urls[0])
        )

        logger.info(f"Пользователь успешно сгенерировал изображение")

    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")

        # Удаляем временные сообщения даже при ошибке
        await delete_messages(message.chat.id, temp_messages)

        await message.answer(
            f"❌ <b>Ошибка при генерации:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Попробуйте ещё раз позже."
        )

    finally:
        await state.set_state(None)


async def generate_with_custom_prompt(message: Message, state: FSMContext, custom_prompt: str):
    """Генерация с кастомным промптом"""
    data = await state.get_data()
    mode = data.get("mode", "infographics")  # По умолчанию инфографика для совместимости
    
    # Для режима простых картинок не требуются фото товара
    if mode == "images":
        product_photos = []
        reference_photos = []
    else:
        product_photos = data.get("product_photos", [])
        reference_photos = data.get("reference_photos", [])
    
    aspect_ratio = data.get("aspect_ratio", "1:1" if mode == "images" else "3:4")
    card_text = data.get("card_text")

    await state.set_state(ImageGenerationStates.generating)

    # Список ID сообщений для удаления
    temp_messages = []

    try:
        tg_id = message.chat.id
        charge = await charge_image_generation(message, state, tg_id)
        if not charge:
            return

        # Если указан текст на карточке, добавляем его в промпт
        original_custom_prompt = custom_prompt
        if card_text:
            custom_prompt = f"{custom_prompt}. Add text on the card: '{card_text}'"
            logger.info(f"[IMAGE_GENERATION] Добавлен текст на карточку. Промпт до: {original_custom_prompt[:200]}... Промпт после: {custom_prompt[:200]}...")

        data = await state.get_data()
        model_name = data.get("model_name", "Nano Banana")
        model_id = data.get("model_id")
        
        # Если model_id не установлен, пытаемся получить из настроек
        if not model_id:
            try:
                models = await api_client.get_image_models()
                selected_model_key = data.get("selected_model")
                if selected_model_key and selected_model_key in models:
                    selected_model = models[selected_model_key]
                    model_id = selected_model.get("model_id")
                    logger.info(f"[IMAGE_GENERATION] Получен model_id из настроек: {model_id}")
            except Exception as e:
                logger.warning(f"[IMAGE_GENERATION] Не удалось получить model_id из настроек: {e}")
        
        logger.info(f"[IMAGE_GENERATION] Используется модель: model_name={model_name}, model_id={model_id}")
        logger.info(f"[IMAGE_GENERATION] Кастомный промпт перед отправкой в FAL (длина: {len(custom_prompt)} символов):\n{custom_prompt}")
        logger.info(f"[IMAGE_GENERATION] Параметры: product_images={len(product_photos)}, reference_images={len(reference_photos)}, aspect_ratio={aspect_ratio}, model_id={model_id}")
        
        msg1 = await message.answer(
            f"🎨 Генерирую изображение с вашим промптом через {model_name}...\n\n"
            f"💰 Списано: <b>{charge['cost']} токенов</b>\n"
            f"💼 Остаток: <b>{charge['balance']} токенов</b>"
        )
        temp_messages.append(msg1.message_id)
        
        image_urls = await FALService.generate_product_image(
            prompt=custom_prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio,
            model_id=model_id
        )

        if not image_urls:
            # Удаляем временные сообщения
            await delete_messages(message.chat.id, temp_messages)

            await message.answer(
                "❌ Не удалось сгенерировать изображение. Попробуйте ещё раз."
            )
            await state.clear()
            return

        # Сохраняем результат
        await state.update_data(last_generated_image=image_urls[0], generated_prompt=custom_prompt)

        # Удаляем все временные сообщения
        await delete_messages(message.chat.id, temp_messages)

        # Определяем текст подписи в зависимости от режима
        mode = data.get("mode", "infographics")
        caption_text = "Ваша карточка товара успешно сгенерирована!" if mode == "infographics" else "Ваша картинка успешно сгенерирована!"

        # Отправляем результат с кнопками
        await message.answer_photo(
            photo=image_urls[0],
            caption=(
                f"✨ <b>Готово!</b>\n\n"
                f"{caption_text}\n\n"
                "Выберите действие:"
            ),
            reply_markup=result_keyboard(image_url=image_urls[0])
        )

        logger.info(f"Пользователь успешно сгенерировал изображение с кастомным промптом")

    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")

        # Удаляем временные сообщения даже при ошибке
        await delete_messages(message.chat.id, temp_messages)

        await message.answer(
            f"❌ <b>Ошибка при генерации:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Попробуйте ещё раз позже."
        )

    finally:
        # Сбрасываем только состояние, чтобы сохранить данные для дальнейшего редактирования
        await state.set_state(None)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await callback.answer()
    await safe_delete_message(callback)
    await state.clear()

    try:
        profile = await api_client.get_profile(
            callback.from_user.id,
            username=callback.from_user.username,
            full_name=get_full_name(callback.from_user),
        )
    except Exception:
        profile = {}

    active_until = profile.get("active_until")

    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие на клавиатуре.",
        reply_markup=main_menu_kb(has_active_sub=True)
    )

    await callback.message.answer(
        f"👤 <b>Пользователь:</b> @{profile.get('username') or callback.from_user.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {profile.get('tariff_name') or 'Тестовый режим'}\n"
        f"🗓️ <b>Активен до:</b> {active_until or 'Бессрочно (тест)'}\n"
        f"💰 <b>Токены:</b> {profile.get('bonus_balance') or 0}",
        reply_markup=None
    )


@router.callback_query(F.data == "refine_image")
async def refine_image_handler(callback: CallbackQuery, state: FSMContext):
    """Запрос на внесение правок в изображение"""
    await callback.answer()
    await safe_delete_message(callback)

    data = await state.get_data()
    last_image = data.get("last_generated_image")

    if not last_image:
        await callback.message.answer("❌ Нет сгенерированного изображения для редактирования.")
        return

    await state.set_state(ImageGenerationStates.waiting_for_refinement)

    await callback.message.answer(
        "✏️ <b>Внесение правок в изображение</b>\n\n"
        "Опишите, что нужно изменить в изображении.\n"
        "Например: 'Make the background brighter', 'Add more lighting', 'Change colors to warmer tones'\n\n"
        "Отправьте текстом ваши правки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_refinement))
async def receive_refinement(message: Message, state: FSMContext):
    """Получение правок для изображения"""
    refinement_text = message.text.strip()

    if len(refinement_text) < 5:
        await message.answer("⚠️ Описание правок слишком короткое. Опишите детальнее (минимум 5 символов).")
        return

    data = await state.get_data()
    last_image = data.get("last_generated_image")
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    aspect_ratio = data.get("aspect_ratio", "3:4")
    old_prompt = data.get("generated_prompt", "")

    # Создаём новый промпт с учётом правок
    new_prompt = f"{old_prompt}. {refinement_text}"

    await message.answer(
        "✅ <b>Правки приняты!</b>\n\n"
        f"📝 Ваше описание:\n<code>{refinement_text}</code>\n\n"
        "Начинаю генерацию с учётом правок...",
        reply_markup=None
    )

    await generate_with_custom_prompt(message, state, new_prompt)


@router.message(StateFilter(ImageGenerationStates.waiting_for_product_photos))
async def invalid_product_input(message: Message):
    """Обработка некорректного ввода при ожидании фото товара"""
    await message.answer(
        "⚠️ Пожалуйста, отправьте фотографию товара или нажмите 'Готово'."
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_reference_photos))
async def invalid_reference_input(message: Message):
    """Обработка некорректного ввода при ожидании референсов"""
    await message.answer(
        "⚠️ Пожалуйста, отправьте референсное изображение или нажмите 'Готово'."
    )


# Обработчик случайных фото вне процесса генерации
@router.message(F.photo)
async def handle_unexpected_photo(message: Message, state: FSMContext):
    """Обработка фотографий, отправленных вне процесса генерации"""
    current_state = await state.get_state()
    
    # Если пользователь не в процессе генерации, предлагаем начать
    if current_state is None:
        await message.answer(
            "📸 Вижу, что вы отправили фотографию!\n\n"
            "Хотите начать генерацию карточки товара с этим изображением?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎨 Начать генерацию", callback_data="generate_image")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_generation")]
            ])
        )
    else:
        # Если в другом состоянии - просто информируем
        await message.answer(
            "📸 Изображение получено, но сейчас не время для его загрузки.\n"
            "Пожалуйста, следуйте текущим инструкциям или начните новую генерацию."
        )


@router.callback_query(F.data == "cancel_generation")
async def cancel_generation(callback: CallbackQuery, state: FSMContext):
    """Отмена генерации"""
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "❌ Генерация отменена.\n\n"
        "Используйте /menu для просмотра доступных команд."
    )


@router.callback_query(F.data == "download_image")
async def download_image_handler(callback: CallbackQuery, state: FSMContext):
    """Скачивание изображения как файл"""
    await callback.answer("Загружаю файл...")
    
    try:
        # Получаем URL из state (он сохраняется при генерации)
        data = await state.get_data()
        image_url = data.get("last_generated_image")
        
        # Если URL не в state, пытаемся получить из сообщения с фото
        if not image_url:
            # Пытаемся найти последнее сообщение с фото в чате
            if callback.message.photo:
                # Если текущее сообщение содержит фото, берем его
                photo = callback.message.photo[-1]  # Берем самое большое фото
                file_info = await bot.get_file(photo.file_id)
                image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
            else:
                await callback.message.answer("❌ Не удалось найти изображение для скачивания. Попробуйте сгенерировать новое изображение.")
                return
        
        if not image_url:
            await callback.message.answer("❌ Не удалось найти изображение для скачивания.")
            return
        
        # Скачиваем изображение
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await callback.message.answer("❌ Не удалось загрузить изображение.")
                    return
                
                image_data = await resp.read()
                from aiogram.types import BufferedInputFile
                
                # Определяем расширение файла
                import os
                from urllib.parse import urlparse
                parsed_url = urlparse(image_url)
                file_ext = os.path.splitext(parsed_url.path)[1] or ".jpg"
                filename = f"generated_image{file_ext}"
                
                file = BufferedInputFile(image_data, filename=filename)
                await callback.message.answer_document(
                    document=file,
                    caption="📥 Ваше изображение готово!"
                )
                
    except Exception as e:
        logger.error(f"Ошибка при скачивании изображения: {e}")
        await callback.message.answer(f"❌ Ошибка при скачивании: {str(e)}")
