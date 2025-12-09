# Развертывание MarketHelper на iawuuw.com

## Информация о сервере

- **IP**: 80.76.43.75
- **Домен**: iawuuw.com
- **Пользователь**: root
- **Пароль**: 0s0549pdg6ML

## Быстрое развертывание

### Автоматический способ (рекомендуется)

С локальной машины выполните:

```bash
chmod +x deploy-to-server.sh
./deploy-to-server.sh
```

Скрипт автоматически:
1. Подключится к серверу
2. Установит все необходимые пакеты
3. Клонирует репозиторий с GitHub
4. Настроит Nginx
5. Получит SSL сертификат
6. Запустит приложение

### Ручной способ

#### Шаг 1: Подключение к серверу

```bash
ssh root@80.76.43.75
# Пароль: 0s0549pdg6ML
```

#### Шаг 2: Первоначальная настройка

```bash
# Обновление системы
apt-get update && apt-get upgrade -y

# Установка пакетов
apt-get install -y curl wget git nginx certbot python3-certbot-nginx ufw

# Настройка firewall
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm get-docker.sh

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создание директорий
mkdir -p /opt/markethelper /var/www/certbot
```

#### Шаг 3: Клонирование проекта

```bash
cd /opt
git clone https://github.com/Uz11ps/markethelper.git
cd markethelper
```

#### Шаг 4: Настройка переменных окружения

```bash
# Создайте файл .env
nano .env
```

Вставьте и заполните:

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
JWT_SECRET_KEY=generate-very-secure-random-string-min-32-chars

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# FAL AI
FAL_API_KEY=your_fal_api_key_here
FAL_API_BASE_URL=https://fal.run
FAL_IMAGE_MODEL=fal-ai/flux-pro/v1.1
FAL_UPSCALE_MODEL=fal-ai/advanced-upscale

# Bot API
BOT_API_URL=http://bot:8001

# Telemetry
CHROMA_TELEMETRY_ENABLED=false
```

**ВАЖНО**: Замените все значения на реальные!

#### Шаг 5: Настройка Nginx

```bash
cd /opt/markethelper
cp nginx.conf /etc/nginx/sites-available/markethelper
ln -s /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
```

#### Шаг 6: Получение SSL сертификата

```bash
systemctl start nginx
certbot --nginx -d iawuuw.com -d www.iawuuw.com
# Следуйте инструкциям, выберите опцию 2 (Redirect HTTP to HTTPS)
```

#### Шаг 7: Запуск приложения

```bash
cd /opt/markethelper
cp docker-compose.prod.yml docker-compose.yml
chmod +x deploy.sh
./deploy.sh
```

Или вручную:

```bash
docker-compose build --no-cache
docker-compose up -d
```

#### Шаг 8: Создание первого администратора

```bash
docker-compose exec backend python backend/create_admin.py
```

Следуйте инструкциям для создания учетной записи администратора.

#### Шаг 9: Проверка работы

```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f

# Проверка доступности
curl https://iawuuw.com/api/docs
```

## Доступ к админ-панели

После успешного развертывания:

- **Админ-панель**: https://iawuuw.com
- **API документация**: https://iawuuw.com/docs
- **Вход**: Используйте созданные учетные данные администратора

## Полезные команды

### Просмотр логов

```bash
cd /opt/markethelper
docker-compose logs -f backend
docker-compose logs -f bot
docker-compose logs -f frontend
```

### Перезапуск сервисов

```bash
docker-compose restart
# Или конкретный сервис
docker-compose restart backend
```

### Обновление проекта

```bash
cd /opt/markethelper
git pull origin master
docker-compose build --no-cache
docker-compose up -d
```

### Резервное копирование базы данных

```bash
# Создание бэкапа
cp /opt/markethelper/db.sqlite3 /opt/markethelper/backups/db-$(date +%Y%m%d-%H%M%S).sqlite3

# Восстановление
cp /opt/markethelper/backups/db-YYYYMMDD-HHMMSS.sqlite3 /opt/markethelper/db.sqlite3
docker-compose restart backend
```

## Устранение неполадок

### Контейнеры не запускаются

```bash
docker-compose logs
docker-compose ps
docker-compose down
docker-compose up -d
```

### Nginx ошибки

```bash
nginx -t
tail -f /var/log/nginx/error.log
systemctl restart nginx
```

### SSL проблемы

```bash
certbot certificates
certbot renew --force-renewal
systemctl reload nginx
```

### Проблемы с базой данных

```bash
docker-compose exec backend python backend/create_admin.py
```

## Безопасность

1. **Измените пароль root** после первого входа:
   ```bash
   passwd
   ```

2. **Настройте SSH ключи** вместо пароля:
   ```bash
   # На локальной машине
   ssh-copy-id root@80.76.43.75
   ```

3. **Ограничьте доступ** через firewall:
   ```bash
   ufw status
   ufw deny 22/tcp  # После настройки SSH ключей
   ```

4. **Регулярно обновляйте систему**:
   ```bash
   apt-get update && apt-get upgrade -y
   ```

## Мониторинг

```bash
# Использование ресурсов
htop
docker stats

# Логи системы
journalctl -u docker -f
journalctl -u nginx -f
```

