#!/bin/bash

# Скрипт для исправления всех проблем в проекте

set -e

cd /opt/markethelper

echo "🔧 Исправление всех проблем..."
echo ""

# Обновляем код
echo "📥 Обновление кода..."
git pull origin master

# Проверяем переменные окружения
echo ""
echo "📝 Проверка переменных окружения..."
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю..."
    touch .env
fi

# Добавляем BOT_USERNAME если его нет
if ! grep -q "^BOT_USERNAME=" .env; then
    echo "BOT_USERNAME=fghghhjgk_bot" >> .env
    echo "✅ BOT_USERNAME добавлен в .env"
fi

# Добавляем BOT_API_URL если его нет
if ! grep -q "^BOT_API_URL=" .env; then
    echo "BOT_API_URL=http://bot:8001" >> .env
    echo "✅ BOT_API_URL добавлен в .env"
fi

echo ""
echo "📋 Текущие переменные окружения:"
grep -E "^BOT_|^BACKEND_URL" .env || echo "Переменные не найдены"

# Перезапускаем сервисы
echo ""
echo "🔄 Перезапуск сервисов..."
docker-compose -f docker-compose.prod.yml stop backend bot frontend
docker-compose -f docker-compose.prod.yml up -d --build backend bot frontend

echo ""
echo "⏳ Ожидание запуска сервисов (15 секунд)..."
sleep 15

# Проверяем статус
echo ""
echo "📊 Статус сервисов:"
docker-compose -f docker-compose.prod.yml ps

# Проверяем логи на ошибки
echo ""
echo "📋 Проверка логов на ошибки (последние 20 строк):"
echo "Backend:"
docker-compose -f docker-compose.prod.yml logs --tail=20 backend | grep -i error || echo "Ошибок не найдено"
echo ""
echo "Bot:"
docker-compose -f docker-compose.prod.yml logs --tail=20 bot | grep -i error || echo "Ошибок не найдено"

echo ""
echo "✅ Исправления применены!"
echo ""
echo "🧪 Проверка работы:"
echo "Backend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/docs || echo 'недоступен')"
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080 || echo 'недоступен')"

