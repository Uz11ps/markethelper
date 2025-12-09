#!/bin/bash

# Проверка здоровья backend

cd /opt/markethelper

echo "🔍 Проверка здоровья backend..."
echo ""

echo "📋 Логи backend (последние 50 строк):"
docker-compose logs --tail=50 backend
echo ""

echo "🧪 Тестирование endpoints:"
echo ""
echo "1. Проверка /docs:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/docs || echo "Недоступен"
echo ""

echo "2. Проверка /api/docs:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/api/docs || echo "Недоступен"
echo ""

echo "3. Проверка /api:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/api || echo "Недоступен"
echo ""

echo "4. Проверка внутри контейнера:"
docker-compose exec -T backend python3 << 'PYTHON'
import urllib.request
import sys

endpoints = [
    "http://localhost:8000/docs",
    "http://localhost:8000/api/docs",
    "http://localhost:8000/api"
]

for endpoint in endpoints:
    try:
        req = urllib.request.urlopen(endpoint, timeout=2)
        print(f"✅ {endpoint}: {req.getcode()}")
    except Exception as e:
        print(f"❌ {endpoint}: {e}")
PYTHON

echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "🔍 Проверка процессов в контейнере:"
docker-compose exec -T backend ps aux | head -5

