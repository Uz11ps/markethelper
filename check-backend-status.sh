#!/bin/bash

# Проверка статуса backend

cd /opt/markethelper

echo "🔍 Проверка статуса backend..."
echo ""

echo "📊 Статус контейнеров:"
docker-compose ps
echo ""

echo "📋 Логи backend (последние 50 строк):"
docker-compose logs --tail=50 backend
echo ""

echo "🔍 Проверка файла базы данных внутри контейнера:"
docker-compose exec backend ls -la /app/data/db.sqlite3 2>/dev/null || echo "Контейнер не запущен"
echo ""

echo "🔍 Проверка прав на директорию внутри контейнера:"
docker-compose exec backend ls -ld /app/data 2>/dev/null || echo "Контейнер не запущен"
echo ""

echo "🧪 Попытка подключения к backend:"
curl -v http://localhost:8000/api/docs 2>&1 | head -20 || echo "Backend недоступен"
echo ""

echo "📋 Проверка процессов в контейнере:"
docker-compose exec backend ps aux 2>/dev/null | head -10 || echo "Контейнер не запущен"

