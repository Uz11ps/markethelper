#!/bin/bash

# Настройка Nginx и проверка DNS

set -e

cd /opt/markethelper

echo "🔧 Настройка Nginx и проверка DNS..."
echo ""

# Проверка и запуск Nginx
echo "🔍 Проверка статуса Nginx..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx уже запущен"
else
    echo "▶️  Запуск Nginx..."
    systemctl start nginx
    systemctl enable nginx
    echo "✅ Nginx запущен"
fi

# Применение временной конфигурации
echo ""
echo "📝 Применение конфигурации Nginx..."
cp nginx.conf.temp-ssl /etc/nginx/sites-available/markethelper

# Создание симлинка если его нет
if [ ! -L /etc/nginx/sites-enabled/markethelper ]; then
    ln -s /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/markethelper
fi

# Удаление дефолтной конфигурации если она есть
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Проверка конфигурации
nginx -t

# Перезагрузка Nginx
systemctl reload nginx

echo ""
echo "✅ Nginx настроен и запущен"
echo ""

# Проверка DNS
echo "🔍 Проверка DNS..."
GOOGLE_DNS=$(dig +short @8.8.8.8 iawuuw.com 2>/dev/null | tail -1)
CF_DNS=$(dig +short @1.1.1.1 iawuuw.com 2>/dev/null | tail -1)

echo "Google DNS: ${GOOGLE_DNS:-не разрешается}"
echo "Cloudflare DNS: ${CF_DNS:-не разрешается}"
echo "Ожидаемый IP: 80.76.43.75"
echo ""

if [ "$GOOGLE_DNS" = "80.76.43.75" ] || [ "$CF_DNS" = "80.76.43.75" ]; then
    echo "✅ DNS записи распространились!"
    echo ""
    echo "Теперь можно получить SSL сертификат:"
    echo "  certbot --nginx -d iawuuw.com -d www.iawuuw.com"
else
    echo "⚠️ DNS записи еще не настроены или не распространились"
    echo ""
    echo "📋 Инструкция по настройке DNS:"
    echo ""
    echo "1. Войдите в панель управления вашим доменом (регистратор домена)"
    echo "2. Найдите раздел 'DNS записи' или 'DNS Management'"
    echo "3. Добавьте следующие A записи:"
    echo ""
    echo "   Тип: A"
    echo "   Имя: @ (или оставьте пустым)"
    echo "   Значение: 80.76.43.75"
    echo "   TTL: 3600 (или Auto)"
    echo ""
    echo "   Тип: A"
    echo "   Имя: www"
    echo "   Значение: 80.76.43.75"
    echo "   TTL: 3600 (или Auto)"
    echo ""
    echo "4. Сохраните изменения"
    echo "5. Подождите 10-30 минут для распространения DNS"
    echo "6. Проверьте: dig +short @8.8.8.8 iawuuw.com"
    echo "7. После распространения DNS получите SSL: certbot --nginx -d iawuuw.com -d www.iawuuw.com"
    echo ""
    echo "🌐 Пока DNS не настроен, админ-панель доступна по IP:"
    echo "   http://80.76.43.75"
fi

echo ""
echo "🧪 Проверка работы сервисов:"
echo "Backend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/docs || echo 'недоступен')"
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080 || echo 'недоступен')"
echo "Nginx: $(curl -s -o /dev/null -w '%{http_code}' http://localhost || echo 'недоступен')"

