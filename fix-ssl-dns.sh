#!/bin/bash

# Исправление проблем с SSL и DNS

set -e

cd /opt/markethelper

echo "🔧 Исправление проблем с SSL и DNS..."
echo ""

# Проверка DNS из разных источников
echo "🔍 Проверка DNS из разных источников..."
echo "Локально:"
LOCAL_DNS=$(dig +short @8.8.8.8 iawuuw.com | tail -1)
echo "  iawuuw.com -> $LOCAL_DNS"

echo ""
echo "Из Google DNS:"
GOOGLE_DNS=$(dig +short @8.8.8.8 iawuuw.com | tail -1)
echo "  iawuuw.com -> $GOOGLE_DNS"

echo ""
echo "Из Cloudflare DNS:"
CF_DNS=$(dig +short @1.1.1.1 iawuuw.com | tail -1)
echo "  iawuuw.com -> $CF_DNS"

if [ "$GOOGLE_DNS" != "80.76.43.75" ] && [ "$CF_DNS" != "80.76.43.75" ]; then
    echo ""
    echo "⚠️ DNS записи еще не распространились глобально!"
    echo "Ожидаемый IP: 80.76.43.75"
    echo "Google DNS: $GOOGLE_DNS"
    echo "Cloudflare DNS: $CF_DNS"
    echo ""
    echo "Подождите 10-30 минут и попробуйте снова."
    echo "Или проверьте настройки DNS в панели управления доменом:"
    echo "  - A запись: @ -> 80.76.43.75"
    echo "  - A запись: www -> 80.76.43.75"
    exit 1
fi

echo ""
echo "✅ DNS записи распространились"
echo ""

# Проверка доступности домена из интернета
echo "🔍 Проверка доступности домена из интернета..."
if curl -s -I http://iawuuw.com | head -1 | grep -q "200\|301\|302"; then
    echo "✅ Домен доступен"
else
    echo "⚠️ Домен не доступен из интернета"
    echo "Проверьте firewall:"
    echo "  sudo ufw status"
    echo "  sudo ufw allow 80/tcp"
    echo "  sudo ufw allow 443/tcp"
    exit 1
fi

# Проверка портов
echo ""
echo "🔍 Проверка открытых портов..."
if netstat -tuln | grep -q ":80 "; then
    echo "✅ Порт 80 открыт"
else
    echo "⚠️ Порт 80 не открыт"
    echo "Откройте порт: sudo ufw allow 80/tcp"
    exit 1
fi

# Временная конфигурация Nginx без SSL
echo ""
echo "📝 Применение временной конфигурации Nginx..."
cp nginx.conf.temp-ssl /etc/nginx/sites-available/markethelper
mkdir -p /var/www/certbot
nginx -t
systemctl reload nginx

echo ""
echo "✅ Временная конфигурация применена"
echo ""
echo "Теперь попробуйте получить SSL сертификат:"
echo "  certbot --nginx -d iawuuw.com -d www.iawuuw.com"
echo ""
echo "Или используйте standalone режим:"
echo "  ./setup-ssl-standalone.sh"

