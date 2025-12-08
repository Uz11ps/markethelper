# Инструкция по развертыванию MarketHelper на сервере

## Информация о сервере

- **IP**: 80.76.43.152
- **Домен**: 374504.vm.spacecore.network
- **Пользователь**: root
- **Пароль**: dKoqRxy9CwNQ

## Шаг 1: Подключение к серверу

```bash
ssh root@80.76.43.152
# Пароль: dKoqRxy9CwNQ
```

## Шаг 2: Первоначальная настройка сервера

Выполните на сервере:

```bash
# Загрузите скрипт настройки
wget https://raw.githubusercontent.com/your-repo/markethelper/main/setup-server.sh
chmod +x setup-server.sh
./setup-server.sh
```

Или выполните команды вручную:

```bash
# Обновление системы
apt-get update && apt-get upgrade -y

# Установка необходимых пакетов
apt-get install -y curl wget git nginx certbot python3-certbot-nginx ufw

# Настройка firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создание директорий
mkdir -p /opt/markethelper
mkdir -p /var/www/certbot
```

## Шаг 3: Загрузка проекта на сервер

### Вариант 1: Через Git (рекомендуется)

```bash
cd /opt
git clone <your-repo-url> markethelper
cd markethelper
```

### Вариант 2: Через SCP (с локальной машины)

```bash
# С локальной машины
scp -r . root@80.76.43.152:/opt/markethelper/
```

### Вариант 3: Через rsync (с локальной машины)

```bash
# С локальной машины
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
  ./ root@80.76.43.152:/opt/markethelper/
```

## Шаг 4: Настройка переменных окружения

Создайте файл `.env` в `/opt/markethelper/`:

```bash
cd /opt/markethelper
nano .env
```

Содержимое `.env`:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# Backend
BACKEND_URL=http://backend:8000
PORT=8000
APP_DEBUG=False

# Database
DATABASE_URL=sqlite:///./db.sqlite3

# Admin
ADMIN_TG_ID=your_telegram_id
JWT_SECRET_KEY=your-very-secure-secret-key-change-this

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# FAL AI
FAL_API_KEY=your_fal_api_key_here
FAL_API_BASE_URL=https://fal.run
FAL_IMAGE_MODEL=fal-ai/flux-pro/v1.1
FAL_UPSCALE_MODEL=fal-ai/advanced-upscale

# Bot API URL (для уведомлений)
BOT_API_URL=http://bot:8001

# Telemetry
CHROMA_TELEMETRY_ENABLED=false
```

**ВАЖНО**: Замените все значения на реальные!

## Шаг 5: Настройка Nginx

Скопируйте конфигурацию Nginx:

```bash
cp nginx.conf /etc/nginx/sites-available/markethelper
ln -s /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Удалите дефолтный сайт если есть
```

Проверьте конфигурацию:

```bash
nginx -t
```

## Шаг 6: Получение SSL сертификата

```bash
# Запустите временный Nginx для получения сертификата
systemctl start nginx

# Получите сертификат
certbot --nginx -d 374504.vm.spacecore.network

# Следуйте инструкциям certbot
# Выберите опцию 2 (Redirect HTTP to HTTPS)
```

## Шаг 7: Развертывание приложения

```bash
cd /opt/markethelper

# Используйте продакшн конфигурацию
cp docker-compose.prod.yml docker-compose.yml

# Запустите развертывание
chmod +x deploy.sh
./deploy.sh
```

Или вручную:

```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Шаг 8: Проверка работы

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f bot

# Проверка доступности
curl http://localhost:8000/api/docs
curl http://localhost:8080
```

## Шаг 9: Настройка автообновления SSL

Добавьте в crontab:

```bash
crontab -e
```

Добавьте строку:

```
0 0 * * * certbot renew --quiet && systemctl reload nginx
```

## Полезные команды

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f bot
docker-compose logs -f frontend
```

### Перезапуск сервисов

```bash
docker-compose restart backend
docker-compose restart bot
docker-compose restart frontend
```

### Обновление проекта

```bash
cd /opt/markethelper
git pull  # Если используете git
docker-compose build --no-cache
docker-compose up -d
```

### Резервное копирование базы данных

```bash
# Создание бэкапа
cp /opt/markethelper/db.sqlite3 /opt/markethelper/backups/db-$(date +%Y%m%d-%H%M%S).sqlite3

# Восстановление из бэкапа
cp /opt/markethelper/backups/db-YYYYMMDD-HHMMSS.sqlite3 /opt/markethelper/db.sqlite3
docker-compose restart backend
```

## Доступ к админ-панели

После развертывания админ-панель будет доступна по адресу:

**https://374504.vm.spacecore.network**

API документация: **https://374504.vm.spacecore.network/docs**

## Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose logs

# Проверьте .env файл
cat .env

# Проверьте порты
netstat -tulpn | grep -E '8000|8001|8080'
```

### Проблема: Nginx не работает

```bash
# Проверьте конфигурацию
nginx -t

# Проверьте логи
tail -f /var/log/nginx/error.log

# Перезапустите Nginx
systemctl restart nginx
```

### Проблема: SSL сертификат не работает

```bash
# Проверьте сертификат
certbot certificates

# Обновите сертификат вручную
certbot renew --force-renewal
systemctl reload nginx
```

## Безопасность

1. **Измените пароль root** после первого входа:
   ```bash
   passwd
   ```

2. **Создайте отдельного пользователя** для работы:
   ```bash
   adduser deploy
   usermod -aG docker deploy
   ```

3. **Настройте SSH ключи** вместо пароля:
   ```bash
   # На локальной машине
   ssh-copy-id root@80.76.43.152
   ```

4. **Ограничьте доступ к портам** через firewall:
   ```bash
   ufw status
   ```

## Мониторинг

Для мониторинга используйте:

```bash
# Использование ресурсов
htop

# Статус Docker
docker stats

# Логи системы
journalctl -u docker -f
```

