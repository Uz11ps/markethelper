#!/bin/bash

# Скрипт автоматического развертывания на сервере iawuuw.com
# Использование: ./deploy-to-server.sh

set -e

SERVER_IP="80.76.43.75"
SERVER_USER="root"
SERVER_PATH="/opt/markethelper"
DOMAIN="iawuuw.com"

echo "🚀 Развертывание MarketHelper на сервере $DOMAIN"
echo "=========================================="

# Проверка подключения
echo "📡 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "echo 'Connected'" 2>/dev/null; then
    echo "❌ Не удалось подключиться к серверу."
    echo "Проверьте доступность сервера и правильность учетных данных."
    exit 1
fi

echo "✅ Подключение установлено"

# Выполнение команд на сервере
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
set -e

echo "🔧 Шаг 1: Обновление системы и установка пакетов..."
apt-get update -qq
apt-get upgrade -y -qq

# Установка необходимых пакетов
if ! command -v git &> /dev/null; then
    echo "📦 Установка Git..."
    apt-get install -y git -qq
fi

if ! command -v nginx &> /dev/null; then
    echo "📦 Установка Nginx..."
    apt-get install -y nginx certbot python3-certbot-nginx ufw -qq
fi

if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh -qq
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Настройка firewall
echo "🔥 Настройка firewall..."
ufw allow 22/tcp 2>/dev/null || true
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p /opt/markethelper
mkdir -p /var/www/certbot
chmod -R 755 /opt/markethelper

echo "✅ Настройка сервера завершена"
ENDSSH

# Клонирование репозитория
echo ""
echo "📥 Шаг 2: Клонирование репозитория..."
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
cd /opt
if [ -d "markethelper" ]; then
    echo "📂 Репозиторий уже существует, обновляю..."
    cd markethelper
    git pull origin master || git fetch origin master && git reset --hard origin/master
else
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/Uz11ps/markethelper.git
    cd markethelper
fi
ENDSSH

# Копирование конфигурационных файлов
echo ""
echo "📝 Шаг 3: Настройка конфигурации..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/markethelper

# Копирование продакшн конфигурации
cp docker-compose.prod.yml docker-compose.yml 2>/dev/null || true

# Создание .env если не существует
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте файл .env с настройками перед запуском."
    echo "Используйте .env.production.example как шаблон."
    exit 1
fi

echo "✅ Конфигурация готова"
ENDSSH

# Настройка Nginx
echo ""
echo "🌐 Шаг 4: Настройка Nginx..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/markethelper

# Копирование конфигурации Nginx
cp nginx.conf /etc/nginx/sites-available/markethelper
ln -sf /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
nginx -t

echo "✅ Nginx настроен"
ENDSSH

# Получение SSL сертификата
echo ""
echo "🔒 Шаг 5: Получение SSL сертификата..."
echo "⚠️  Внимание: Для получения сертификата нужно выполнить вручную:"
echo "   certbot --nginx -d iawuuw.com -d www.iawuuw.com"
echo ""
read -p "Получить SSL сертификат сейчас? (y/n): " get_ssl

if [ "$get_ssl" = "y" ] || [ "$get_ssl" = "Y" ]; then
    ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
    systemctl start nginx
    certbot --nginx -d iawuuw.com -d www.iawuuw.com --non-interactive --agree-tos --email admin@iawuuw.com --redirect
    systemctl reload nginx
ENDSSH
else
    echo "⏭️  Пропущено. Выполните позже: certbot --nginx -d iawuuw.com"
fi

# Запуск приложения
echo ""
echo "▶️  Шаг 6: Запуск приложения..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/markethelper

# Остановка старых контейнеров
docker-compose down 2>/dev/null || true

# Сборка и запуск
echo "🔨 Сборка образов..."
docker-compose build --no-cache

echo "▶️  Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo "✅ Статус контейнеров:"
docker-compose ps
ENDSSH

echo ""
echo "🎉 Развертывание завершено!"
echo "=========================================="
echo "🌐 Админ-панель: https://iawuuw.com"
echo "📚 API документация: https://iawuuw.com/docs"
echo ""
echo "📝 Следующие шаги:"
echo "1. Создайте первого администратора:"
echo "   ssh root@80.76.43.75"
echo "   cd /opt/markethelper"
echo "   docker-compose exec backend python backend/create_admin.py"
echo ""
echo "2. Проверьте логи:"
echo "   docker-compose logs -f"

