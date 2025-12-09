#!/bin/bash
# Применение исправлений для /api/admin/settings/all

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "🛑 Перезапуск backend..."
docker-compose -f docker-compose.prod.yml restart backend

echo "⏳ Ожидание запуска backend (30 секунд)..."
sleep 30

echo "✅ Проверка работы endpoint:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/admin/settings/all)

if [ "$response" = "200" ]; then
    echo "✅ Endpoint работает корректно (HTTP $response)"
elif [ "$response" = "401" ]; then
    echo "⚠️ Требуется аутентификация (HTTP $response) - это нормально"
else
    echo "❌ Endpoint вернул ошибку (HTTP $response)"
    echo ""
    echo "📋 Последние логи backend:"
    docker-compose -f docker-compose.prod.yml logs --tail=30 backend
fi

