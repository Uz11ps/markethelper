#!/bin/bash

# Создание администратора с логином 123 и паролем 123

cd /opt/markethelper

USERNAME="123"
PASSWORD="123123"  # Удваиваем для соответствия требованиям (минимум 6 символов)

echo "🔐 Создание/обновление администратора: $USERNAME"

# Используем docker-compose exec для продакшена
docker-compose -f docker-compose.prod.yml exec -T backend python << EOF
import asyncio
import sys
from tortoise import Tortoise
from backend.models.admin import Admin
from backend.core.db import TORTOISE_ORM

async def create_or_update_admin():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    username = "$USERNAME"
    password = "$PASSWORD"
    
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

asyncio.run(create_or_update_admin())
EOF

echo ""
echo "✅ Готово!"
echo ""
echo "📋 Учетные данные для входа:"
echo "   Логин: 123"
echo "   Пароль: 123123"
echo ""
echo "🌐 Админ-панель доступна по адресу:"
echo "   http://80.76.43.75 (или http://iawuuw.com после настройки DNS)"

