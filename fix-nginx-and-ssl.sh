#!/bin/bash

# Исправление Nginx и получение SSL сертификата

set -e

cd /opt/markethelper

echo "🔧 Исправление Nginx и настройка SSL..."

# Обновление docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml

# Перезапуск backend для применения нового healthcheck
echo "🔄 Перезапуск backend..."
docker-compose restart backend

# Ожидание
sleep 5

# Проверка что backend работает
echo "📋 Проверка backend..."
docker-compose exec -T backend python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs', timeout=2)" && echo "✅ Backend работает!" || echo "⚠️ Backend еще запускается"

# Проверка Nginx конфигурации
echo ""
echo "🌐 Проверка Nginx..."
if [ -f "/etc/nginx/sites-available/markethelper" ]; then
    echo "Конфигурация найдена"
    nginx -t
else
    echo "⚠️ Конфигурация Nginx не найдена, создаю..."
    cp nginx.conf.temp /etc/nginx/sites-available/markethelper
    ln -sf /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl reload nginx
fi

# Проверка DNS
echo ""
echo "🔍 Проверка DNS..."
DNS_IP=$(dig +short iawuuw.com | tail -1)
if [ "$DNS_IP" = "80.76.43.75" ]; then
    echo "✅ DNS настроен правильно: $DNS_IP"
    echo ""
    echo "Попытка получить SSL сертификат..."
    certbot --nginx -d iawuuw.com -d www.iawuuw.com --non-interactive --agree-tos --email admin@iawuuw.com --redirect || {
        echo ""
        echo "⚠️ Не удалось получить SSL сертификат автоматически."
        echo "Возможные причины:"
        echo "1. DNS записи еще не распространились (подождите 10-15 минут)"
        echo "2. Домен не доступен из интернета"
        echo ""
        echo "Проверьте:"
        echo "  dig iawuuw.com +short"
        echo "  curl -I http://iawuuw.com"
    }
else
    echo "⚠️ DNS не настроен или указывает на другой IP: $DNS_IP"
    echo "Ожидаемый IP: 80.76.43.75"
    echo ""
    echo "Настройте DNS записи:"
    echo "  A запись: @ -> 80.76.43.75"
    echo "  A запись: www -> 80.76.43.75"
fi

echo ""
echo "✅ Проверка завершена!"
echo ""
echo "📝 Текущий статус:"
docker-compose ps

