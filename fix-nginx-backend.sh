#!/bin/bash

# Исправление подключения Nginx к backend

set -e

cd /opt/markethelper

echo "🔧 Исправление подключения Nginx к backend..."

# Обновление docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml

# Перезапуск backend с проброшенным портом
echo "🔄 Перезапуск backend..."
docker-compose down backend
docker-compose up -d backend

# Ожидание запуска backend
echo "⏳ Ожидание запуска backend (30 секунд)..."
sleep 30

# Проверка что backend работает
echo ""
echo "📋 Проверка backend:"
if curl -s http://localhost:8000/api/docs > /dev/null; then
    echo "✅ Backend доступен на localhost:8000"
else
    echo "⚠️ Backend недоступен на localhost:8000"
    echo "Проверка внутри контейнера:"
    docker-compose exec -T backend curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs || echo "Недоступен"
fi

# Проверка порта
echo ""
echo "🔍 Проверка порта 8000:"
netstat -tulpn | grep 8000 || echo "Порт не слушается"

# Обновление конфигурации Nginx
echo ""
echo "🌐 Обновление конфигурации Nginx..."
cp nginx.conf.temp /etc/nginx/sites-available/markethelper
ln -sf /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
nginx -t

# Перезапуск Nginx
systemctl reload nginx

# Проверка работы через Nginx
echo ""
echo "🧪 Проверка через Nginx:"
sleep 2
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost/api/docs || echo "Недоступен"

echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "✅ Проверка завершена!"

