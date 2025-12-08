#!/bin/bash

# Быстрый деплой для пользователя
# Использование: ./quick-deploy.sh

echo "🚀 Быстрый деплой MarketHelper на сервер..."

SERVER_IP="80.76.43.152"
SERVER_USER="root"
SERVER_PATH="/opt/markethelper"

# Проверка подключения
echo "📡 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 ${SERVER_USER}@${SERVER_IP} "echo 'Connected'" 2>/dev/null; then
    echo "❌ Не удалось подключиться к серверу. Проверьте доступность."
    exit 1
fi

# Создание директории на сервере
echo "📁 Создание директорий на сервере..."
ssh ${SERVER_USER}@${SERVER_IP} "mkdir -p ${SERVER_PATH}"

# Копирование файлов
echo "📦 Копирование файлов на сервер..."
rsync -avz --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'db.sqlite3' \
    --exclude 'chroma_db' \
    --exclude 'cookie' \
    ./ ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

# Копирование скриптов развертывания
echo "📝 Копирование скриптов..."
scp deploy.sh ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/
scp docker-compose.prod.yml ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/
scp nginx.conf ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

# Выполнение развертывания на сервере
echo "▶️  Запуск развертывания на сервере..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/markethelper
chmod +x deploy.sh
./deploy.sh
ENDSSH

echo "✅ Развертывание завершено!"
echo "🌐 Админ-панель будет доступна по адресу: https://374504.vm.spacecore.network"

