# Чеклист развертывания MarketHelper

## ✅ Подготовка

- [ ] Проект готов к развертыванию
- [ ] Все зависимости указаны в requirements.txt
- [ ] Docker файлы настроены
- [ ] Фронтенд использует динамические URL (window.location.origin)

## 📋 Шаги развертывания

### 1. Подключение к серверу
```bash
ssh root@80.76.43.152
# Пароль: dKoqRxy9CwNQ
```

### 2. Первоначальная настройка
```bash
# Выполнить setup-server.sh или команды вручную
./setup-server.sh
```

### 3. Загрузка проекта
```bash
# Вариант 1: Через SCP (с локальной машины)
scp -r . root@80.76.43.152:/opt/markethelper/

# Вариант 2: Через Git
cd /opt
git clone <your-repo> markethelper
```

### 4. Настройка переменных окружения
```bash
cd /opt/markethelper
cp .env.production.example .env
nano .env
# Заполните все переменные реальными значениями!
```

**Критически важно заполнить:**
- `BOT_TOKEN` - токен Telegram бота
- `OPENAI_API_KEY` - ключ OpenAI
- `FAL_API_KEY` - ключ FAL AI
- `JWT_SECRET_KEY` - случайная строка минимум 32 символа
- `ADMIN_TG_ID` - ваш Telegram ID

### 5. Настройка Nginx
```bash
cp nginx.conf /etc/nginx/sites-available/markethelper
ln -s /etc/nginx/sites-available/markethelper /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
```

### 6. Получение SSL сертификата
```bash
systemctl start nginx
certbot --nginx -d 374504.vm.spacecore.network
# Выберите опцию 2 (Redirect HTTP to HTTPS)
```

### 7. Запуск приложения
```bash
cd /opt/markethelper
cp docker-compose.prod.yml docker-compose.yml
chmod +x deploy.sh
./deploy.sh
```

### 8. Создание первого администратора
```bash
cd /opt/markethelper
docker-compose exec backend python backend/create_admin.py
```

Или через интерактивный скрипт:
```bash
chmod +x create_admin_script.sh
./create_admin_script.sh
```

### 9. Проверка работы
```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f

# Проверка доступности
curl https://374504.vm.spacecore.network/api/docs
```

## 🌐 Доступ

После успешного развертывания:

- **Админ-панель**: https://374504.vm.spacecore.network
- **API документация**: https://374504.vm.spacecore.network/docs
- **Вход**: Используйте созданные учетные данные администратора

## 🔧 Устранение проблем

### Контейнеры не запускаются
```bash
docker-compose logs
docker-compose ps
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
```

### Проблемы с базой данных
```bash
docker-compose exec backend python backend/create_admin.py
```

## 📝 После развертывания

1. Измените пароль root на сервере
2. Настройте SSH ключи вместо пароля
3. Настройте автоматическое обновление SSL (crontab)
4. Настройте резервное копирование базы данных
5. Проверьте работу всех функций админ-панели

## 🔄 Обновление проекта

```bash
cd /opt/markethelper
git pull  # если используете git
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

