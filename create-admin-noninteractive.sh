#!/bin/bash

# Неинтерактивное создание администратора

cd /opt/markethelper

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Использование: $0 <username> <password>"
    echo "Пример: $0 admin mypassword123"
    exit 1
fi

USERNAME=$1
PASSWORD=$2

echo "🔐 Создание администратора: $USERNAME"

docker-compose exec -T backend python << EOF
import asyncio
import sys
from tortoise import Tortoise
from backend.models.admin import Admin
from backend.core.db import TORTOISE_ORM

async def create_admin():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    # Проверка существования
    existing = await Admin.filter(username="$USERNAME").first()
    if existing:
        print(f"❌ Пользователь с username '$USERNAME' уже существует!")
        await Tortoise.close_connections()
        sys.exit(1)
    
    # Создание админа
    admin = await Admin.create(
        username="$USERNAME",
        password_hash=Admin.hash_password("$PASSWORD"),
        full_name="Admin",
        is_super_admin=True,
        is_active=True
    )
    
    print(f"\n✅ Суперадмин успешно создан!")
    print(f"   ID: {admin.id}")
    print(f"   Username: {admin.username}")
    
    await Tortoise.close_connections()

asyncio.run(create_admin())
EOF

