#!/bin/bash
# Применение исправлений для авторизации в /api/files/add

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "🛑 Остановка backend..."
docker-compose -f docker-compose.prod.yml stop backend

echo "🔨 Пересборка backend контейнера..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo "▶️ Запуск backend..."
docker-compose -f docker-compose.prod.yml up -d backend

echo "⏳ Ожидание запуска backend (40 секунд)..."
sleep 40

echo "✅ Проверка работы endpoint (должен вернуть 401 без токена):"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/files/add \
  -H "Content-Type: application/json" \
  -d '{"login":"test","password":"test"}')

if [ "$response" = "401" ]; then
    echo "✅ Endpoint требует авторизацию (HTTP $response) - это правильно!"
else
    echo "⚠️ Endpoint вернул неожиданный код (HTTP $response)"
fi

echo ""
echo "📋 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

