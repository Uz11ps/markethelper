#!/bin/bash

# Проверка всех сервисов

cd /opt/markethelper

echo "🔍 Проверка всех сервисов..."
echo ""

echo "📊 Статус контейнеров:"
docker-compose ps
echo ""

echo "🔍 Проверка backend на порту 8000:"
netstat -tulpn | grep 8000 || echo "Порт 8000 не слушается"
echo ""

echo "🧪 Тестирование backend:"
echo "1. Изнутри контейнера:"
docker-compose exec -T backend curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs || echo "Недоступен"
echo ""

echo "2. С хоста (localhost):"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/docs || echo "Недоступен"
echo ""

echo "3. Через IP сервера:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://80.76.43.75:8000/api/docs || echo "Недоступен"
echo ""

echo "🌐 Проверка Nginx:"
echo "Конфигурация:"
cat /etc/nginx/sites-available/markethelper | grep -A 5 "proxy_pass" | head -10
echo ""

echo "Статус Nginx:"
systemctl status nginx --no-pager | head -5
echo ""

echo "🔍 Проверка DNS:"
DNS_IP=$(dig +short iawuuw.com | tail -1)
echo "DNS для iawuuw.com: $DNS_IP"
if [ "$DNS_IP" = "80.76.43.75" ]; then
    echo "✅ DNS настроен правильно"
else
    echo "⚠️ DNS не настроен или указывает на другой IP"
fi
echo ""

echo "📋 Логи backend (последние 10 строк):"
docker-compose logs --tail=10 backend

