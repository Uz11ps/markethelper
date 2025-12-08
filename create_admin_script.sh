#!/bin/bash

# Скрипт для создания первого администратора
# Использование: ./create_admin_script.sh

echo "🔐 Создание администратора..."

read -p "Имя пользователя: " username
read -sp "Пароль: " password
echo
read -p "Полное имя: " full_name
read -p "Email: " email
read -p "Супер-админ? (y/n): " is_super

if [ "$is_super" = "y" ] || [ "$is_super" = "Y" ]; then
    is_super_admin="true"
else
    is_super_admin="false"
fi

# Создание через Python скрипт
docker-compose exec -T backend python << EOF
import asyncio
from backend.models.admin import Admin
from backend.core.db import init_db, close_db

async def create_admin():
    await init_db()
    
    admin = await Admin.create(
        username="$username",
        password_hash=Admin.hash_password("$password"),
        full_name="$full_name",
        email="$email",
        is_super_admin=$is_super_admin,
        is_active=True
    )
    
    print(f"✅ Администратор создан: {admin.username} (ID: {admin.id})")
    await close_db()

asyncio.run(create_admin())
EOF

echo "✅ Готово!"

