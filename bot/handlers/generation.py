import base64
import html
from contextlib import suppress
from typing import Any

import aiohttp
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import main_menu_kb
from bot.services.api_client import APIClient
from bot.states.generation_states import GenerationStates

router = Router()
api = APIClient()

CANCEL_COMMANDS = {"/cancel", "cancel", "отмена", "стоп"}


def _is_cancel(text: str | None) -> bool:
    if not text:
        return False
    return text.strip().casefold() in CANCEL_COMMANDS


def _collect_urls(payload: Any) -> list[str]:
    urls: list[str] = []

    def _walk(value: Any):
        if isinstance(value, str) and value.startswith("http"):
            urls.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                _walk(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                _walk(item)

    _walk(payload)
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


async def _fetch_image(session: aiohttp.ClientSession, url: str, index: int) -> tuple[bytes, str]:
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.read()
        content_type = resp.headers.get("Content-Type") or "image/jpeg"
    extension = ".jpg"
    if "png" in content_type:
        extension = ".png"
    elif "webp" in content_type:
        extension = ".webp"
    filename = f"generated_{index + 1}{extension}"
    return data, filename


async def _send_generated_output(message: types.Message, payload: Any) -> None:
    urls = _collect_urls(payload)
    if not urls:
        await message.answer("⚠️ Не удалось получить ссылку на результат генерации.")
        return

    sent = 0
    async with aiohttp.ClientSession() as session:
        for idx, url in enumerate(urls):
            if sent >= 4:
                break
            try:
                file_bytes, filename = await _fetch_image(session, url, idx)
                await message.answer_document(
                    document=types.BufferedInputFile(file_bytes, filename=filename)
                )
                sent += 1
            except Exception:
                await message.answer(f"🔗 {url}")
                sent += 1


def _format_concept_summary(concept: dict[str, Any] | None) -> str | None:
    if not isinstance(concept, dict):
        return None

    def _norm(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return ""
        return str(value).strip()

    lines: list[str] = ["🧠 Концепция"]

    concept_name = _norm(concept.get("concept_name"))
    if concept_name:
        lines.append(f"<b>{html.escape(concept_name)}</b>")

    description = _norm(concept.get("🔍 Описание"))
    if description:
        lines.append(f"• Стиль: {html.escape(description)}")

    usage = _norm(concept.get("📍 Использование товара"))
    if usage:
        lines.append(f"• Использование: {html.escape(usage)}")

    background = _norm(concept.get("🏞️ Фон"))
    if background:
        lines.append(f"• Фон: {html.escape(background)}")

    offers = concept.get("💥 Офферы") or []
    if isinstance(offers, list) and offers:
        lines.append("• Офферы:")
        for offer in offers[:4]:
            offer_text = _norm(offer)
            if offer_text:
                lines.append(f"  • {html.escape(offer_text)}")

    palette = _norm(concept.get("cvetovaya_palitra"))
    if palette:
        lines.append(f"• Палитра: {html.escape(palette)}")

    layout = _norm(concept.get("🧩 Расположение иконок"))
    if layout:
        lines.append(f"• Иконки: {html.escape(layout)}")

    if len(lines) <= 1:
        return None
    return "\n".join(lines)


async def _send_meta(message: types.Message, result: dict[str, Any]) -> None:
    parts: list[str] = []
    analysis = result.get("image_description")
    if analysis:
        parts.append(f"🔍 <b>Анализ товара:</b>\n{html.escape(analysis)}")

    final_prompt = result.get("final_prompt")
    if final_prompt:
        parts.append(f"📝 <b>Финальный промпт:</b>\n<pre>{html.escape(final_prompt)}</pre>")

    concept_summary = _format_concept_summary(result.get("concept"))
    if concept_summary:
        parts.append(concept_summary)

    if parts:
        await message.answer("\n\n".join(parts), parse_mode="HTML")


async def _return_to_menu(message: types.Message):
    has_access = True
    try:
        profile = await api.get_profile(message.from_user.id)
        has_access = bool(profile.get("active_until"))
    except Exception:
        pass

    await message.answer(
        "↩️ Возвращаю в главное меню.",
        reply_markup=main_menu_kb(has_active_sub=has_access),
    )


@router.message(Command("generate"))
@router.message(F.text == "🎨 Создать инфографику")
async def start_autogen(message: types.Message, state: FSMContext):
    await _start_flow(message, state)


async def _start_flow(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(GenerationStates.awaiting_photo)
    await state.update_data(user_prompt=None)
    await message.answer(
        "Пришлите фото товара (можно с подписью). "
        "По картинке я сам обращусь к GPT, соберу промпт из файла и отправлю его в FAL. "
        "Хотите уточнить требования — пришлите текст, затем фото."
    )


@router.message(GenerationStates.awaiting_photo, F.text)
async def capture_text_prompt(message: types.Message, state: FSMContext):
    if _is_cancel(message.text):
        await state.clear()
        await message.answer("❌ Автогенерация отменена.")
        await _return_to_menu(message)
        return

    clean = (message.text or "").strip()
    if not clean:
        await message.answer("Пришлите описание или сразу фото товара.")
        return

    await state.update_data(user_prompt=clean)
    await message.answer("Принял описание. Теперь отправьте фото товара.")


@router.message(GenerationStates.awaiting_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if _is_cancel(message.caption):
        await state.clear()
        await message.answer("❌ Автогенерация отменена.")
        await _return_to_menu(message)
        return

    largest = message.photo[-1]
    file_info = await message.bot.get_file(largest.file_id)
    downloaded = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(downloaded.getvalue()).decode("utf-8")

    data = await state.get_data()
    user_prompt_parts: list[str] = []
    stored_prompt = data.get("user_prompt")
    if stored_prompt:
        user_prompt_parts.append(stored_prompt)
    caption = (message.caption or "").strip()
    if caption:
        user_prompt_parts.append(caption)
    user_prompt = "\n\n".join(user_prompt_parts)

    await state.set_state(GenerationStates.processing)
    waiting = await message.answer("⌛ Анализирую фото, формирую промпт и отправляю в FAL...")
    try:
        result = await api.auto_generate_card(
            title=caption or "Авто карточка",
            product_images_b64=[image_b64],
            reference_images_b64=None,
            user_prompt=user_prompt,
        )
    except Exception as exc:
        with suppress(Exception):
            await waiting.delete()
        await message.answer(f"⚠️ Не удалось сгенерировать карточку: {exc}")
        await state.set_state(GenerationStates.awaiting_photo)
        return

    with suppress(Exception):
        await waiting.delete()

    fal_payload = result.get("fal_result")
    if fal_payload:
        await _send_generated_output(message, fal_payload)
    else:
        await message.answer("⚠️ Ответ получен, но изображение отсутствует.")

    await _send_meta(message, result)
    await message.answer("Готово! Можете прислать новое фото или отправьте /cancel для выхода.")
    await state.set_state(GenerationStates.awaiting_photo)
    await state.update_data(user_prompt=None)


@router.message(GenerationStates.processing)
async def mute_processing(message: types.Message):
    await message.answer("⌛ Подождите, я ещё формирую карточку.")


@router.callback_query(F.data == "profile:open_generation")
async def open_from_profile(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_flow(callback.message, state)
