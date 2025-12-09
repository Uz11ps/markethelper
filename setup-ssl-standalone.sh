#!/bin/bash

# Настройка SSL сертификата через standalone режим

set -e

cd /opt/markethelper

echo "🔒 Настройка SSL сертификата (standalone режим)..."
echo ""

# Проверка DNS
echo "🔍 Проверка DNS..."
DNS_IP=$(dig +short iawuuw.com | tail -1)
echo "DNS для iawuuw.com: $DNS_IP"

if [ "$DNS_IP" != "80.76.43.75" ]; then
    echo "⚠️ DNS не настроен правильно!"
    echo "Ожидаемый IP: 80.76.43.75"
    echo "Текущий IP: $DNS_IP"
    exit 1
fi

echo "✅ DNS настроен правильно"
echo ""

# Проверка доступности домена из интернета
echo "🔍 Проверка доступности домена из интернета..."
if curl -s -I http://iawuuw.com | head -1 | grep -q "200\|301\|302"; then
    echo "✅ Домен доступен локально"
else
    echo "⚠️ Домен не отвечает локально"
    exit 1
fi

# Остановка Nginx временно для standalone режима
echo ""
echo "🛑 Временная остановка Nginx для standalone режима..."
systemctl stop nginx

# Получение SSL сертификата через standalone
echo ""
echo "🔒 Получение SSL сертификата (standalone режим)..."
certbot certonly --standalone -d iawuuw.com -d www.iawuuw.com --non-interactive --agree-tos --email admin@iawuuw.com

# Запуск Nginx обратно
echo ""
echo "▶️  Запуск Nginx..."
systemctl start nginx

# Проверка результата
if [ -f "/etc/letsencrypt/live/iawuuw.com/fullchain.pem" ]; then
    echo ""
    echo "✅ SSL сертификат получен успешно!"
    echo ""
    echo "🌐 Настройка Nginx для использования SSL..."
    
    # Применение конфигурации с SSL
    cp nginx.conf /etc/nginx/sites-available/markethelper
    nginx -t
    systemctl reload nginx
    
    echo ""
    echo "✅ Nginx настроен для HTTPS"
    echo ""
    echo "🧪 Проверка HTTPS:"
    sleep 2
    curl -s -o /dev/null -w "HTTP %{http_code}\n" https://iawuuw.com/api/docs || echo "HTTPS еще настраивается..."
    echo ""
    echo "✅ Админ-панель доступна по адресу: https://iawuuw.com"
else
    echo ""
    echo "⚠️ Не удалось получить SSL сертификат"
    echo "Возможные причины:"
    echo "1. DNS записи еще не распространились глобально (подождите 10-30 минут)"
    echo "2. Домен не доступен из интернета (проверьте firewall)"
    echo "3. Порт 80 заблокирован"
    echo ""
    echo "Проверьте логи: /var/log/letsencrypt/letsencrypt.log"
fi

