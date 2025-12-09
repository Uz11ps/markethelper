#!/bin/bash

# Скрипт для исправления реферальной ссылки

set -e

cd /opt/markethelper

echo "🔧 Исправление реферальной ссылки..."
echo ""

# Обновляем код
echo "📥 Обновление кода..."
git pull origin master

# Проверяем/добавляем BOT_USERNAME в .env
echo ""
echo "📝 Настройка BOT_USERNAME в .env..."
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю новый..."
    touch .env
fi

BOT_USERNAME="fghghhjgk_bot"

if grep -q "^BOT_USERNAME=" .env; then
    # Обновляем существующее значение
    sed -i "s/^BOT_USERNAME=.*/BOT_USERNAME=$BOT_USERNAME/" .env
    echo "✅ BOT_USERNAME обновлен"
else
    # Добавляем новую строку
    echo "BOT_USERNAME=$BOT_USERNAME" >> .env
    echo "✅ BOT_USERNAME добавлен"
fi

echo ""
echo "📋 Текущее значение BOT_USERNAME:"
grep "^BOT_USERNAME=" .env

# Перезапускаем backend с пересборкой
echo ""
echo "🔄 Перезапуск backend..."
docker-compose -f docker-compose.prod.yml stop backend
docker-compose -f docker-compose.prod.yml up -d --build backend

echo ""
echo "⏳ Ожидание запуска backend (10 секунд)..."
sleep 10

# Проверяем логи
echo ""
echo "📋 Последние строки логов backend:"
docker-compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo "✅ Готово!"
echo ""
echo "🧪 Проверка API:"
curl -s http://localhost:8000/api/docs | head -5 || echo "Backend еще запускается..."

echo ""
echo "📝 Инструкция:"
echo "1. Проверьте, что BOT_USERNAME установлен: grep BOT_USERNAME .env"
echo "2. Проверьте логи backend: docker-compose -f docker-compose.prod.yml logs backend"
echo "3. Попробуйте получить реферальную ссылку через бота"

