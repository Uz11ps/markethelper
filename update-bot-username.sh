#!/bin/bash

# Скрипт для обновления BOT_USERNAME в .env файле

cd /opt/markethelper

if [ -z "$1" ]; then
    echo "Использование: $0 <bot_username>"
    echo "Пример: $0 fghghhjgk_bot"
    echo ""
    echo "Текущее значение BOT_USERNAME:"
    grep "^BOT_USERNAME=" .env 2>/dev/null || echo "BOT_USERNAME не найден в .env"
    exit 1
fi

BOT_USERNAME=$1

# Удаляем @ если пользователь его указал
BOT_USERNAME=$(echo "$BOT_USERNAME" | sed 's/^@//')

echo "🔧 Обновление BOT_USERNAME на: $BOT_USERNAME"

# Проверяем существование .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю новый..."
    touch .env
fi

# Проверяем, есть ли уже BOT_USERNAME в .env
if grep -q "^BOT_USERNAME=" .env; then
    # Обновляем существующее значение
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^BOT_USERNAME=.*/BOT_USERNAME=$BOT_USERNAME/" .env
    else
        # Linux
        sed -i "s/^BOT_USERNAME=.*/BOT_USERNAME=$BOT_USERNAME/" .env
    fi
    echo "✅ BOT_USERNAME обновлен"
else
    # Добавляем новую строку
    echo "BOT_USERNAME=$BOT_USERNAME" >> .env
    echo "✅ BOT_USERNAME добавлен"
fi

echo ""
echo "📋 Текущее значение:"
grep "^BOT_USERNAME=" .env

echo ""
echo "🔄 Перезапуск backend для применения изменений..."
docker-compose -f docker-compose.prod.yml restart backend

echo ""
echo "✅ Готово! BOT_USERNAME обновлен и backend перезапущен."

