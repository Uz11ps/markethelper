#!/bin/bash
# Быстрое исправление 502 Bad Gateway

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "🛑 Перезапуск backend..."
docker-compose -f docker-compose.prod.yml restart backend

echo "⏳ Ожидание 20 секунд..."
sleep 20

echo "✅ Проверка:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs || echo "❌ Backend все еще недоступен. Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"

