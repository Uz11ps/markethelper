from aiogram import Router, types, F
from bot.services.api_client import APIClient
from bot.keyboards.main_menu import main_menu_kb
from bot.keyboards.profile_menu import profile_menu_kb
from bot.keyboards import subscription
from datetime import datetime

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
            f"{tg.first_name or ''} {tg.last_name or ''}".strip(),
        )
    except Exception as e:
        print(f"[ERROR create_user] {e}")

    if referrer_id and referrer_id != tg.id:
        await api.bind_referral(referred_tg=tg.id, referrer_tg=referrer_id)

    # Получаем профиль пользователя
    profile = await api.get_profile(tg.id)

    # Временно для тестирования - всегда показываем как будто подписка есть
    has_active = True  # Отключена проверка подписки для тестирования

    # Отправляем приветствие с минималистичной клавиатурой
    await message.answer(
        "👋 Добро пожаловать в <b>MarketHelper</b>!",
        reply_markup=main_menu_kb(has_active_sub=has_active)
    )

    # Показываем профиль
    active_until = profile.get("active_until") if profile else None
    text = (
        f"👤 <b>Пользователь:</b> @{profile.get('username') or tg.username or '—'}\n"
        f"⭐️ <b>Тариф:</b> {profile.get('tariff_name') or 'Тестовый режим'}\n"
        f"🗓️ <b>Активен до:</b> {_fmt_date(active_until) if active_until else 'Бессрочно (тест)'}\n"
        f"📁 <b>Файл:</b> {(profile.get('access_file_path') or '').rsplit('/', 1)[-1] or '—'}\n"
        f"💰 <b>Бонусы:</b> {profile.get('bonus_balance') or 0}"
    )

    await message.answer(text, reply_markup=profile_menu_kb())
