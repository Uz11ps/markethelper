"""
Скрипт для создания суперадмина через командную строку
"""
import asyncio
import sys
from getpass import getpass
from tortoise import Tortoise
from backend.models.admin import Admin
from backend.core.db import TORTOISE_ORM


async def create_superadmin():
    """Создание суперадмина"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

    print("=== Создание суперадминистратора ===\n")

    username = input("Введите username: ").strip()
    if not username:
        print("❌ Username не может быть пустым!")
        return

    # Проверка существования
    existing = await Admin.filter(username=username).first()
    if existing:
        print(f"❌ Пользователь с username '{username}' уже существует!")
        return

    password = getpass("Введите пароль: ").strip()
    password_confirm = getpass("Подтвердите пароль: ").strip()

    if password != password_confirm:
        print("❌ Пароли не совпадают!")
        return

    if len(password) < 6:
        print("❌ Пароль должен быть не менее 6 символов!")
        return

    full_name = input("Введите полное имя (опционально): ").strip() or None
    email = input("Введите email (опционально): ").strip() or None

    # Создание админа
    admin = await Admin.create(
        username=username,
        password_hash=Admin.hash_password(password),
        full_name=full_name,
        email=email,
        is_super_admin=True
    )

    print(f"\n✅ Суперадмин успешно создан!")
    print(f"   ID: {admin.id}")
    print(f"   Username: {admin.username}")
    print(f"   Full name: {admin.full_name or 'N/A'}")
    print(f"   Email: {admin.email or 'N/A'}")

    await Tortoise.close_connections()


if __name__ == "__main__":
    try:
        asyncio.run(create_superadmin())
    except KeyboardInterrupt:
        print("\n\n❌ Операция отменена")
        sys.exit(1)
