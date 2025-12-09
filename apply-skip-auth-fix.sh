#!/bin/bash
# Применение исправлений для возможности создания файлов без авторизации

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

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
echo "💡 Теперь в админ-панели на странице 'Файлы' доступна опция:"
echo "   'Пропустить авторизацию на внешнем сервисе'"
echo "   Это позволит создавать файлы даже если SalesFinder API недоступен"

