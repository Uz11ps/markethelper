# Исправление проблем развертывания

## Проблемы которые были исправлены:

1. **Nginx требует SSL сертификат до его получения** - создана временная конфигурация без SSL
2. **База данных SQLite не может быть создана** - исправлен путь к базе данных и права доступа

## Инструкция по исправлению на сервере:

### Шаг 1: Обновите код с GitHub

```bash
cd /opt/markethelper
git pull origin master
```

### Шаг 2: Выполните скрипт исправления

```bash
chmod +x fix-deployment.sh
./fix-deployment.sh
```

Или выполните команды вручную:

```bash
cd /opt/markethelper

# Создание директорий с правильными правами
mkdir -p chroma_db cookie logs
chmod -R 777 chroma_db cookie logs

# Создание файла базы данных
touch db.sqlite3
chmod 666 db.sqlite3

# Использование временной конфигурации Nginx (без SSL)
cp nginx.conf.temp /etc/nginx/sites-available/markethelper
ln -sf /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Перезапуск контейнеров
docker-compose down
docker-compose up -d

# Проверка статуса
docker-compose ps
docker-compose logs --tail=50 backend
```

### Шаг 3: Проверка работы

```bash
# Проверка backend
curl http://localhost:8000/api/docs

# Проверка frontend
curl http://localhost:8080

# Проверка через домен (если DNS настроен)
curl http://iawuuw.com/api/docs
```

### Шаг 4: Получение SSL сертификата

После того как все работает:

```bash
certbot --nginx -d iawuuw.com -d www.iawuuw.com
```

Certbot автоматически обновит конфигурацию Nginx для использования SSL.

### Шаг 5: Применение финальной конфигурации с SSL

Если certbot не обновил конфигурацию автоматически:

```bash
cp nginx.conf /etc/nginx/sites-available/markethelper
nginx -t
systemctl reload nginx
```

### Шаг 6: Создание первого администратора

```bash
docker-compose exec backend python backend/create_admin.py
```

## Проверка логов при проблемах

```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs backend
docker-compose logs bot
docker-compose logs frontend

# Логи Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

## Устранение проблем

### Проблема: Backend не запускается

```bash
# Проверьте права на файл базы данных
ls -la db.sqlite3
chmod 666 db.sqlite3

# Проверьте логи
docker-compose logs backend

# Пересоздайте контейнер
docker-compose up -d --force-recreate backend
```

### Проблема: База данных не создается

```bash
# Создайте файл вручную
touch db.sqlite3
chmod 666 db.sqlite3

# Проверьте что директория существует
ls -la /opt/markethelper/

# Перезапустите backend
docker-compose restart backend
```

### Проблема: Nginx ошибки

```bash
# Проверьте конфигурацию
nginx -t

# Проверьте что порты не заняты
netstat -tulpn | grep -E '80|443|8000|8080'

# Перезапустите Nginx
systemctl restart nginx
```

