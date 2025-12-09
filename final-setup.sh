#!/bin/bash

# Финальная настройка проекта

set -e

cd /opt/markethelper

echo "🚀 Финальная настройка проекта..."
echo ""

# Обновление кода
echo "📥 Обновление кода..."
git pull origin master

# Обновление docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml

# Пересборка backend с новым кодом
echo "🔨 Пересборка backend..."
docker-compose build --no-cache backend

# Перезапуск контейнеров
echo "▶️  Запуск контейнеров..."
docker-compose down
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска (20 секунд)..."
sleep 20

# Проверка backend
echo ""
echo "📋 Проверка backend..."
if curl -s http://localhost:8000/api/docs > /dev/null; then
    echo "✅ Backend работает!"
else
    echo "⚠️ Backend еще запускается..."
    docker-compose logs --tail=20 backend
fi

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка Nginx
echo ""
echo "🌐 Проверка Nginx..."
if [ -f "/etc/nginx/sites-available/markethelper" ]; then
    nginx -t && echo "✅ Nginx конфигурация корректна"
else
    echo "⚠️ Конфигурация Nginx не найдена"
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
    echo "✅ DNS настроен: $DNS_IP"
    echo ""
    echo "Проверка доступности домена..."
    if curl -s -I http://iawuuw.com | head -1 | grep -q "200\|301\|302"; then
        echo "✅ Домен доступен!"
        echo ""
        echo "Попытка получить SSL сертификат..."
        certbot --nginx -d iawuuw.com -d www.iawuuw.com --non-interactive --agree-tos --email admin@iawuuw.com --redirect 2>&1 | tail -10
    else
        echo "⚠️ Домен не отвечает. Проверьте настройки Nginx."
    fi
else
    echo "⚠️ DNS не настроен или указывает на другой IP: $DNS_IP"
    echo "Ожидаемый IP: 80.76.43.75"
fi

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📝 Доступ к проекту:"
echo "  - Backend API: http://localhost:8000/api/docs"
echo "  - Frontend: http://localhost:8080"
if [ "$DNS_IP" = "80.76.43.75" ]; then
    echo "  - Через домен: http://iawuuw.com"
fi

