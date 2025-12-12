#!/usr/bin/env python3
"""
Скрипт для установки логина и пароля админа
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from tortoise import Tortoise
from backend.core.db import TORTOISE_ORM
from backend.models.admin import Admin


async def set_admin_password(username: str, password: str, admin_id: int = 1):
    """Установить логин и пароль для админа"""
    
    await Tortoise.init(config=TORTOISE_ORM)
    
    print("=" * 60)
    print("УСТАНОВКА ЛОГИНА И ПАРОЛЯ АДМИНА")
    print("=" * 60)
    
    # Получаем админа
    admin = await Admin.get_or_none(id=admin_id)
    
    if not admin:
        # Создаем нового админа, если его нет
        print(f"Админ с ID={admin_id} не найден. Создаем нового...")
        admin = await Admin.create(
            id=admin_id,
            username=username,
            password_hash=Admin.hash_password(password),
            is_active=True,
            is_super_admin=True
        )
        print(f"✅ Создан новый админ: ID={admin.id}, логин={admin.username}")
    else:
        # Обновляем существующего админа
        admin.username = username
        admin.password_hash = Admin.hash_password(password)
        admin.is_active = True
        await admin.save()
        print(f"✅ Обновлен админ: ID={admin.id}, логин={admin.username}")
    
    print(f"\nЛогин: {username}")
    print(f"Пароль: {password}")
    print("\n✅ ГОТОВО!")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "123"
    password = sys.argv[2] if len(sys.argv) > 2 else "123123"
    admin_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    asyncio.run(set_admin_password(username, password, admin_id))

