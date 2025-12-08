#!/bin/bash

# Скрипт развертывания MarketHelper на сервере
# Использование: ./deploy.sh

set -e

echo "🚀 Начало развертывания MarketHelper..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаю..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаю..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p /opt/markethelper/{chroma_db,cookie,static,logs}
chmod -R 755 /opt/markethelper

# Копирование файлов проекта
echo "📦 Копирование файлов..."
if [ ! -f "/opt/markethelper/.env" ]; then
    echo "⚠️  Файл .env не найден. Создайте его вручную!"
    echo "Скопируйте .env.example в .env и заполните все переменные."
    exit 1
fi

# Остановка старых контейнеров
echo "🛑 Остановка старых контейнеров..."
cd /opt/markethelper
docker-compose down 2>/dev/null || true

# Сборка и запуск контейнеров
echo "🔨 Сборка образов..."
docker-compose build --no-cache

echo "▶️  Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo "✅ Проверка статуса..."
docker-compose ps

echo "🎉 Развертывание завершено!"
echo "📝 Проверьте логи: docker-compose logs -f"

