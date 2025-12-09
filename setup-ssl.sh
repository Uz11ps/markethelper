#!/bin/bash

# Настройка SSL сертификата

set -e

cd /opt/markethelper

echo "🔒 Настройка SSL сертификата..."
echo ""

# Проверка DNS
echo "🔍 Проверка DNS..."
DNS_IP=$(dig +short iawuuw.com | tail -1)
echo "DNS для iawuuw.com: $DNS_IP"

if [ "$DNS_IP" != "80.76.43.75" ]; then
    echo "⚠️ DNS не настроен правильно!"
    echo "Ожидаемый IP: 80.76.43.75"
    echo "Текущий IP: $DNS_IP"
    echo ""
    echo "Настройте DNS записи:"
    echo "  A запись: @ -> 80.76.43.75"
    echo "  A запись: www -> 80.76.43.75"
    exit 1
fi

echo "✅ DNS настроен правильно"
echo ""

# Проверка доступности домена
echo "🔍 Проверка доступности домена..."
if curl -s -I http://iawuuw.com | head -1 | grep -q "200\|301\|302"; then
    echo "✅ Домен доступен"
else
    echo "⚠️ Домен не отвечает"
    exit 1
fi

# Получение SSL сертификата
echo ""
echo "🔒 Получение SSL сертификата..."
certbot --nginx -d iawuuw.com -d www.iawuuw.com --non-interactive --agree-tos --email admin@iawuuw.com --redirect

# Проверка результата
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL сертификат получен успешно!"
    echo ""
    echo "🌐 Проверка HTTPS:"
    curl -s -o /dev/null -w "HTTP %{http_code}\n" https://iawuuw.com/api/docs
    echo ""
    echo "✅ Админ-панель доступна по адресу: https://iawuuw.com"
else
    echo ""
    echo "⚠️ Не удалось получить SSL сертификат"
    echo "Проверьте логи: /var/log/letsencrypt/letsencrypt.log"
fi

