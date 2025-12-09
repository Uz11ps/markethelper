#!/bin/bash
# Пересборка backend для применения исправлений

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

echo "✅ Проверка работы endpoint:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/admin/settings/all)

if [ "$response" = "200" ]; then
    echo "✅ Endpoint работает корректно (HTTP $response)"
elif [ "$response" = "401" ]; then
    echo "⚠️ Требуется аутентификация (HTTP $response) - это нормально, endpoint работает!"
    echo ""
    echo "Проверка содержимого ответа (без аутентификации):"
    curl -s http://localhost:8000/api/admin/settings/all | head -5
else
    echo "❌ Endpoint вернул ошибку (HTTP $response)"
    echo ""
    echo "📋 Последние логи backend:"
    docker-compose -f docker-compose.prod.yml logs --tail=50 backend | grep -A 10 -B 5 "settings/all\|AttributeError\|description"
fi

echo ""
echo "📋 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

