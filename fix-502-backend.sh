#!/bin/bash
# Скрипт для исправления ошибки 502 Bad Gateway

set -e

echo "🔍 Диагностика проблемы 502 Bad Gateway..."

cd /opt/markethelper

# 1. Проверка статуса контейнеров
echo ""
echo "📦 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

# 2. Проверка логов backend
echo ""
echo "📋 Последние 50 строк логов backend:"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend || echo "⚠️ Не удалось получить логи"

# 3. Проверка доступности backend на порту 8000
echo ""
echo "🌐 Проверка доступности backend на localhost:8000:"
if curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs; then
    echo "✅ Backend доступен"
else
    echo "❌ Backend недоступен"
    
    # 4. Проверка внутри контейнера
    echo ""
    echo "🔍 Проверка внутри контейнера backend:"
    docker-compose -f docker-compose.prod.yml exec -T backend curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs || echo "⚠️ Backend не отвечает внутри контейнера"
    
    # 5. Проверка портов
    echo ""
    echo "🔌 Проверка портов:"
    netstat -tlnp | grep 8000 || ss -tlnp | grep 8000 || echo "⚠️ Порт 8000 не слушается"
fi

# 6. Обновление кода и перезапуск
echo ""
echo "🔄 Обновление кода и перезапуск backend..."
git pull origin master || echo "⚠️ Не удалось обновить код"

echo ""
echo "🛑 Остановка backend..."
docker-compose -f docker-compose.prod.yml stop backend

echo ""
echo "▶️ Запуск backend..."
docker-compose -f docker-compose.prod.yml up -d backend

echo ""
echo "⏳ Ожидание запуска backend (30 секунд)..."
sleep 30

# 7. Проверка после перезапуска
echo ""
echo "✅ Проверка после перезапуска:"
if curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs; then
    echo "✅ Backend успешно запущен!"
else
    echo "❌ Backend все еще недоступен"
    echo ""
    echo "📋 Последние ошибки:"
    docker-compose -f docker-compose.prod.yml logs --tail=30 backend
fi

echo ""
echo "✅ Диагностика завершена"

