"""
Прямое создание администратора с логином 123 и паролем 123
Использование: python create-admin-123-direct.py
"""
import asyncio
import sys
from tortoise import Tortoise
from backend.models.admin import Admin
from backend.core.db import TORTOISE_ORM

async def create_or_update_admin():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    username = "123"
    password = "123123"  # Удваиваем для соответствия требованиям (минимум 6 символов)
    
    # Проверка существования
    existing = await Admin.filter(username=username).first()
    
    if existing:
        print(f"⚠️  Пользователь с username '{username}' уже существует!")
        print(f"🔄 Обновление пароля...")
        
        # Обновляем пароль
        existing.password_hash = Admin.hash_password(password)
        existing.is_super_admin = True
        existing.is_active = True
        await existing.save()
        
        print(f"\n✅ Пароль администратора обновлен!")
        print(f"   ID: {existing.id}")
        print(f"   Username: {existing.username}")
    else:
        # Создание админа
        admin = await Admin.create(
            username=username,
            password_hash=Admin.hash_password(password),
            full_name="Admin",
            is_super_admin=True,
            is_active=True
        )
        
        print(f"\n✅ Суперадмин успешно создан!")
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    try:
        asyncio.run(create_or_update_admin())
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

