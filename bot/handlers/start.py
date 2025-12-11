from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatMemberStatus
from bot.services.api_client import APIClient
from bot.keyboards.main_menu import main_menu_kb
from bot.keyboards.profile_menu import profile_menu_kb
from bot.keyboards import subscription
from datetime import datetime
from bot.utils import get_full_name
from bot.loader import bot
import os

router = Router()
api = APIClient()

def _fmt_date(dt_iso: str | None) -> str:
    if not dt_iso:
        return "—"
    try:
        return datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except Exception:
        return dt_iso

@router.message(F.text.startswith("/start"))
async def cmd_start(message: types.Message):
    tg = message.from_user
    args = message.text.split(maxsplit=1)
    referrer_id = None

    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except ValueError:
            referrer_id = None

    try:
        await api.create_user(
            tg.id,
            tg.username,
            get_full_name(tg),
        )
    except Exception as e:
        print(f"[ERROR create_user] {e}")

    if referrer_id and referrer_id != tg.id:
        await api.bind_referral(referred_tg=tg.id, referrer_tg=referrer_id)

    # Проверка подписки на канал и начисление бонуса
    # Получаем username канала из настроек через API
    try:
        channel_settings = await api.get_channel_settings()
        channel_username = channel_settings.get("channel_username", "") if isinstance(channel_settings, dict) else ""
    except Exception as e:
        print(f"[WARNING] Не удалось получить настройки канала: {e}")
        channel_username = os.getenv("CHANNEL_USERNAME", "")
    
    if channel_username:
        try:
            # Убираем @ если есть
            channel_username = channel_username.lstrip("@")
            chat_member = await bot.get_chat_member(f"@{channel_username}", tg.id)
            
            # Проверяем, что пользователь подписан (member, administrator, creator)
            if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                # Проверяем и начисляем бонус через API
                try:
                    bonus_result = await api.check_channel_subscription(tg.id)
                    if bonus_result.get("bonus_given"):
                        # Показываем уведомление о начисленном бонусе
                        await message.answer(
                            f"🎉 {bonus_result.get('message', 'Вам начислен бонус за подписку на канал!')}\n"
                            f"💰 Новый баланс: {bonus_result.get('new_balance', 0)} токенов"
                        )
                except Exception as e:
                    print(f"[ERROR check_channel_subscription] {e}")
        except Exception as e:
            # Если не удалось проверить подписку (канал не найден, бот не админ и т.д.)
            print(f"[WARNING] Не удалось проверить подписку на канал: {e}")

    # Получаем профиль пользователя
    profile = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))

    active_until = profile.get("active_until") if profile else None
    has_active = active_until is not None
    has_file_access = bool(profile.get("access_file_path"))  # Файл есть только у складчины

    # Отправляем приветствие с обновленной клавиатурой (с кнопкой Пополнить)
    # Важно: отправляем клавиатуру ПЕРВЫМ сообщением для гарантии обновления
    keyboard = main_menu_kb(has_active_sub=has_active)
    await message.answer(
        "👋 Добро пожаловать в <b>MarketHelper</b>!\n\n"
        "💡 Используйте кнопки ниже для навигации.\n\n"
        "📌 Доступные кнопки:\n"
        "• 👤Профиль\n"
        "• 💰 Пополнить\n"
        "• ❓FAQ",
        reply_markup=keyboard
    )

    # Показываем профиль
    text = (
        f"👤 <b>Пользователь:</b> @{profile.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {profile.get('tariff_name') or 'Тестовый режим'}\n"
        f"🗓️ <b>Активен до:</b> {_fmt_date(active_until) if active_until else 'Бессрочно (тест)'}\n"
    )
    
    # Показываем файл только для складчины
    if has_file_access:
        text += f"📁 <b>Файл:</b> {(profile.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
    
    text += f"💰 <b>Токены:</b> {profile.get('bonus_balance') or 0}"

    await message.answer(text, reply_markup=profile_menu_kb(has_active_sub=has_active, has_file_access=has_file_access))


@router.message(F.text == "/menu")
async def cmd_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    tg = message.from_user
    profile = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))
    active_until = profile.get("active_until") if profile else None
    has_active = active_until is not None
    has_file_access = bool(profile.get("access_file_path"))  # Файл есть только у складчины

    keyboard = main_menu_kb(has_active_sub=has_active)
    
    # Отправляем клавиатуру ПЕРВЫМ сообщением с явным списком кнопок
    await message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие на клавиатуре ниже.\n\n"
        "📌 Доступные кнопки:\n"
        "• 👤Профиль\n"
        "• 💰 Пополнить\n"
        "• ❓FAQ",
        reply_markup=keyboard
    )

    text = (
        f"👤 <b>Пользователь:</b> @{profile.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {profile.get('tariff_name') or 'Тестовый режим'}\n"
        f"🗓️ <b>Активен до:</b> {_fmt_date(active_until) if active_until else 'Бессрочно (тест)'}\n"
    )
    
    # Показываем файл только для складчины
    if has_file_access:
        text += f"📁 <b>Файл:</b> {(profile.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
    
    text += f"💰 <b>Токены:</b> {profile.get('bonus_balance') or 0}"

    await message.answer(text, reply_markup=profile_menu_kb(has_active_sub=has_active, has_file_access=has_file_access))
