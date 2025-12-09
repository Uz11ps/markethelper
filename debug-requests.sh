#!/bin/bash

# Скрипт для отладки проблем с заявками

cd /opt/markethelper

echo "🔍 Отладка проблем с заявками..."
echo ""

# Проверка логов backend
echo "📋 Последние логи backend (создание заявок):"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend | grep -i "create_request\|request\|заявк" || echo "Нет логов о заявках"

echo ""
echo "📋 Последние логи bot:"
docker-compose -f docker-compose.prod.yml logs --tail=50 bot | grep -i "create_request\|request\|заявк\|error" || echo "Нет логов о заявках"

echo ""
echo "🧪 Проверка API endpoint:"
curl -s http://localhost:8000/api/admin/requests/ | head -20 || echo "API недоступен"

echo ""
echo "📊 Проверка базы данных (количество заявок):"
docker-compose -f docker-compose.prod.yml exec -T backend python << EOF
import asyncio
from tortoise import Tortoise
from backend.core.db import TORTOISE_ORM
from backend.models import Request

async def check():
    await Tortoise.init(config=TORTOISE_ORM)
    count = await Request.all().count()
    print(f"Всего заявок: {count}")
    
    from backend.models import Status
    pending_status = await Status.get_or_none(type="request", code="PENDING")
    if pending_status:
        pending_count = await Request.filter(status=pending_status).count()
        print(f"Заявок в статусе 'В ожидании': {pending_count}")
    
    # Последние 5 заявок
    recent = await Request.all().order_by("-created_at").limit(5).prefetch_related("user", "tariff", "status")
    print("\nПоследние 5 заявок:")
    for req in recent:
        print(f"  ID: {req.id}, User: {req.user.tg_id}, Tariff: {req.tariff.code}, Status: {req.status.name}, Created: {req.created_at}")
    
    await Tortoise.close_connections()

asyncio.run(check())
EOF

echo ""
echo "✅ Проверка завершена"

