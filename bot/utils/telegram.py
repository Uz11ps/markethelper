from aiogram import types


def get_full_name(user: types.User) -> str | None:
    """Собирает имя и фамилию Telegram-пользователя в одну строку."""
    parts = [part for part in (user.first_name, user.last_name) if part]
    full_name = " ".join(parts).strip()
    return full_name or None
