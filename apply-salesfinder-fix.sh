#!/bin/bash
# Применение исправлений для работы с SalesFinder API

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "📝 Проверка переменных окружения..."
if grep -q "SALESFINDER_LOGIN_URL" .env 2>/dev/null; then
    echo "✅ SALESFINDER_LOGIN_URL найден в .env"
    grep "SALESFINDER_LOGIN_URL" .env
else
    echo "⚠️ SALESFINDER_LOGIN_URL не найден в .env, будет использован URL по умолчанию"
fi

echo ""
echo "🛑 Остановка backend..."
docker-compose -f docker-compose.prod.yml stop backend

echo "🔨 Пересборка backend контейнера..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo "▶️ Запуск backend..."
docker-compose -f docker-compose.prod.yml up -d backend

echo "⏳ Ожидание запуска backend (40 секунд)..."
sleep 40

echo ""
echo "✅ Проверка работы backend:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs)

if [ "$response" = "200" ]; then
    echo "✅ Backend работает (HTTP $response)"
else
    echo "⚠️ Backend вернул код (HTTP $response)"
fi

echo ""
echo "📋 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "💡 Для настройки URL SalesFinder API добавьте в .env:"
echo "   SALESFINDER_LOGIN_URL=https://salesfinder.ru/api/user/signIn"
echo "   SALESFINDER_CHECK_URL=https://salesfinder.ru/api/user/getUser"

