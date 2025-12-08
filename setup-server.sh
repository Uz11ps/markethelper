#!/bin/bash

# Скрипт первоначальной настройки сервера
# Запускать на сервере от root

set -e

echo "🔧 Настройка сервера для MarketHelper..."

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "📥 Установка пакетов..."
apt-get install -y \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    nano

# Настройка firewall
echo "🔥 Настройка firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Установка Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Установка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p /opt/markethelper
mkdir -p /var/www/certbot
chmod -R 755 /opt/markethelper

# Клонирование проекта (если используется git)
# echo "📥 Клонирование проекта..."
# cd /opt
# git clone <your-repo-url> markethelper || echo "Репозиторий не указан, пропускаю..."

echo "✅ Настройка сервера завершена!"
echo "📝 Следующие шаги:"
echo "1. Скопируйте файлы проекта в /opt/markethelper"
echo "2. Создайте файл .env с настройками"
echo "3. Запустите ./deploy.sh"

