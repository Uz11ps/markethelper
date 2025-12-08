# Быстрый старт развертывания на сервере

## Шаг 1: Подключение к серверу

```bash
ssh root@80.76.43.152
# Пароль: dKoqRxy9CwNQ
```

## Шаг 2: Первоначальная настройка

Выполните на сервере:

```bash
# Обновление системы
apt-get update && apt-get upgrade -y

# Установка необходимых пакетов
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

## Шаг 3: Загрузка проекта

### С локальной машины (Windows PowerShell):

```powershell
# Установите rsync для Windows или используйте SCP
scp -r . root@80.76.43.152:/opt/markethelper/
```

Или используйте WinSCP или другой SFTP клиент для загрузки файлов.

## Шаг 4: Настройка .env файла

На сервере создайте файл `/opt/markethelper/.env`:

```bash
cd /opt/markethelper
nano .env
```

Вставьте содержимое из `.env.production.example` и заполните реальными значениями.

## Шаг 5: Настройка Nginx

```bash
cd /opt/markethelper
cp nginx.conf /etc/nginx/sites-available/markethelper
ln -s /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t
```

## Шаг 6: Получение SSL сертификата

```bash
systemctl start nginx
certbot --nginx -d 374504.vm.spacecore.network
# Следуйте инструкциям, выберите опцию 2 (Redirect)
```

## Шаг 7: Запуск приложения

```bash
cd /opt/markethelper
cp docker-compose.prod.yml docker-compose.yml
chmod +x deploy.sh
./deploy.sh
```

## Шаг 8: Проверка

```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f

# Проверка доступности
curl https://374504.vm.spacecore.network/api/docs
```

## Доступ к админ-панели

После развертывания:
- **Админ-панель**: https://374504.vm.spacecore.network
- **API документация**: https://374504.vm.spacecore.network/docs

## Создание первого администратора

После запуска backend создайте первого админа через Python:

```bash
cd /opt/markethelper
docker-compose exec backend python backend/create_admin.py
```

Или через API:

```bash
curl -X POST https://374504.vm.spacecore.network/api/admin/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -d '{
    "username": "admin",
    "password": "secure_password",
    "full_name": "Admin User",
    "email": "admin@example.com",
    "is_super_admin": true
  }'
```

## Полезные команды

```bash
# Перезапуск всех сервисов
docker-compose restart

# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f bot

# Обновление проекта
cd /opt/markethelper
git pull  # если используете git
docker-compose build --no-cache
docker-compose up -d
```

