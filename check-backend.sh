#!/bin/bash

# Скрипт для диагностики проблем с backend

cd /opt/markethelper

echo "🔍 Диагностика проблем с backend..."
echo ""

echo "📋 Статус контейнеров:"
docker-compose ps
echo ""

echo "📋 Логи backend (последние 50 строк):"
docker-compose logs --tail=50 backend
echo ""

echo "📋 Проверка файла базы данных:"
ls -la db.sqlite3
echo ""

echo "📋 Проверка прав на директории:"
ls -ld chroma_db cookie logs
echo ""

echo "📋 Попытка подключения к backend:"
curl -v http://localhost:8000/api/docs 2>&1 | head -20
echo ""

echo "📋 Проверка процессов в контейнере:"
docker-compose exec backend ps aux 2>&1 || echo "Контейнер не запущен"
echo ""

echo "📋 Проверка переменных окружения:"
docker-compose exec backend env | grep -E "DATABASE|PYTHON|BACKEND" 2>&1 || echo "Контейнер не запущен"

