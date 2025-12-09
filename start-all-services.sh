#!/bin/bash

# Запуск всех сервисов

set -e

cd /opt/markethelper

echo "🚀 Запуск всех сервисов..."

# Проверка статуса backend
echo "📋 Проверка backend..."
if docker-compose ps backend | grep -q "healthy"; then
    echo "✅ Backend работает и healthy"
else
    echo "⚠️ Backend не healthy, ожидание..."
    sleep 30
fi

# Запуск всех сервисов
echo ""
echo "▶️  Запуск всех сервисов..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска всех сервисов (15 секунд)..."
sleep 15

# Проверка статуса
echo ""
echo "📊 Статус всех контейнеров:"
docker-compose ps

# Проверка работы
echo ""
echo "🧪 Проверка работы:"
echo "1. Backend API:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs

echo ""
echo "2. Frontend:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080

echo ""
echo "3. Через Nginx:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost/api/docs

echo ""
echo "4. Через домен (если DNS настроен):"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://iawuuw.com/api/docs || echo "Домен недоступен"

echo ""
echo "✅ Все сервисы запущены!"

