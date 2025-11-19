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
    aspect_ratio_keyboard,
    skip_text_keyboard
)
from bot.services.fal_service import FALService
from bot.services.prompt_generator import PromptGeneratorService
from bot.loader import bot

router = Router()
logger = logging.getLogger(__name__)

# Временная директория для сохранения фото
TEMP_PHOTO_DIR = "/tmp/bot_photos"
os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)

# Хранилище для медиа-групп (альбомов)
media_groups = {}


async def delete_messages(chat_id: int, message_ids: list):
    """Удаление списка сообщений"""
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение {msg_id}: {e}")


# Обработчик для кнопки "🎨Генерация карточки" удалён - теперь используется inline кнопка из профиля


@router.callback_query(F.data == "generate_image")
async def start_generation(callback: CallbackQuery, state: FSMContext):
    """Начало процесса генерации изображения - выбор формата"""
    await callback.answer()

    await state.clear()
    await state.set_state(ImageGenerationStates.choosing_aspect_ratio)
    await state.update_data(product_photos=[], reference_photos=[])

    await callback.message.answer(
        "🎨 <b>Генерация карточки товара</b>\n\n"
        "Выберите формат изображения для вашей площадки:",
        reply_markup=aspect_ratio_keyboard()
    )


@router.callback_query(F.data.startswith("aspect_"))
async def choose_aspect_ratio(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора формата изображения"""
    await callback.answer()

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

    await message.answer(
        "✅ <b>Готово!</b>\n\n"
        f"📦 Фото товара: {len(product_photos)} шт.\n"
        f"🎨 Референсов: {len(reference_photos)} шт.\n\n"
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
            reference_image_urls=reference_photos
        )
        
        generated_prompt = prompt_data["generated_text_prompt"]
        analysis = prompt_data["deconstruction_analysis"]
        
        # Если указан текст на карточке, добавляем его в промпт
        if card_text:
            generated_prompt = f"{generated_prompt}. Add text on the card: '{card_text}'"
        
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
    
    data = await state.get_data()
    generated_prompt = data.get("generated_prompt")
    
    if not generated_prompt:
        await callback.message.answer("❌ Ошибка: промпт не найден. Попробуйте ещё раз.")
        return
    
    await generate_with_confirmed_prompt(callback.message, state, generated_prompt)


@router.callback_query(F.data == "edit_auto_prompt")
async def edit_auto_prompt(callback: CallbackQuery, state: FSMContext):
    """Редактирование автоматически сгенерированного промпта"""
    await callback.answer()
    
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
    
    await generate_with_confirmed_prompt(message, state, edited_prompt)


async def generate_with_confirmed_prompt(message: Message, state: FSMContext, prompt: str):
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
        # Если указан текст на карточке, добавляем его в промпт
        if card_text:
            prompt = f"{prompt}. Add text on the card: '{card_text}'"
        
        msg1 = await message.answer("🎨 Генерирую изображение через Nano Banana AI...")
        temp_messages.append(msg1.message_id)
        
        image_urls = await FALService.generate_product_image(
            prompt=prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio
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
            reply_markup=result_keyboard()
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
    await state.set_state(ImageGenerationStates.waiting_for_custom_prompt)

    await callback.message.answer(
        "✏️ <b>Введите ваш промпт для генерации</b>\n\n"
        "Опишите, как должна выглядеть карточка товара.\n"
        "Например: 'Product on white background, professional lighting, centered composition'\n\n"
        "Или нажмите кнопку ниже для автоматической генерации.",
        reply_markup=prompt_edit_keyboard()
    )


@router.message(StateFilter(ImageGenerationStates.waiting_for_custom_prompt))
async def receive_custom_prompt(message: Message, state: FSMContext):
    """Получение кастомного промпта от пользователя"""
    custom_prompt = message.text.strip()

    if len(custom_prompt) < 10:
        await message.answer("⚠️ Промпт слишком короткий. Опишите детальнее (минимум 10 символов).")
        return

    await state.update_data(custom_prompt=custom_prompt)

    await message.answer(
        f"✅ <b>Промпт сохранён!</b>\n\n"
        f"<code>{custom_prompt}</code>\n\n"
        "Начинаю генерацию...",
        reply_markup=None
    )

    await generate_with_custom_prompt(message, state, custom_prompt)


async def generate_with_ai_prompt(message: Message, state: FSMContext):
    """Генерация с AI промптом"""
    data = await state.get_data()
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    aspect_ratio = data.get("aspect_ratio", "3:4")
    card_text = data.get("card_text")

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
        # Шаг 1: Генерация промпта через GPT-4o
        msg2 = await message.answer("🤖 Анализирую товар и создаю промпт...")
        temp_messages.append(msg2.message_id)

        prompt_data = await PromptGeneratorService.generate_prompt_from_images(
            product_image_urls=product_photos,
            reference_image_urls=reference_photos
        )

        generated_prompt = prompt_data["generated_text_prompt"]
        analysis = prompt_data["deconstruction_analysis"]

        # Если указан текст на карточке, добавляем его в промпт
        if card_text:
            generated_prompt = f"{generated_prompt}. Add text on the card: '{card_text}'"

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

        # Шаг 2: Генерация изображения через FAL
        msg4 = await message.answer("🎨 Генерирую изображение через Nano Banana AI...")
        temp_messages.append(msg4.message_id)

        image_urls = await FALService.generate_product_image(
            prompt=generated_prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio
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
            reply_markup=result_keyboard()
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
    product_photos = data.get("product_photos", [])
    reference_photos = data.get("reference_photos", [])
    aspect_ratio = data.get("aspect_ratio", "3:4")
    card_text = data.get("card_text")

    await state.set_state(ImageGenerationStates.generating)

    # Список ID сообщений для удаления
    temp_messages = []

    try:
        # Если указан текст на карточке, добавляем его в промпт
        if card_text:
            custom_prompt = f"{custom_prompt}. Add text on the card: '{card_text}'"

        msg1 = await message.answer("🎨 Генерирую изображение с вашим промптом через Nano Banana AI...")
        temp_messages.append(msg1.message_id)

        image_urls = await FALService.generate_product_image(
            prompt=custom_prompt,
            product_images=product_photos,
            reference_images=reference_photos,
            num_images=1,
            aspect_ratio=aspect_ratio
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

        # Отправляем результат с кнопками
        await message.answer_photo(
            photo=image_urls[0],
            caption=(
                "✨ <b>Готово!</b>\n\n"
                "Ваша карточка товара успешно сгенерирована!\n\n"
                "Выберите действие:"
            ),
            reply_markup=result_keyboard()
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
    await state.clear()

    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Вы вернулись в главное меню. Используйте /menu для просмотра доступных команд."
    )


@router.callback_query(F.data == "refine_image")
async def refine_image_handler(callback: CallbackQuery, state: FSMContext):
    """Запрос на внесение правок в изображение"""
    await callback.answer()

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
        f"✅ <b>Правки приняты!</b>\n\n"
        f"<b>Обновлённый промпт:</b>\n<code>{new_prompt}</code>\n\n"
        "Начинаю генерацию с правками...",
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
