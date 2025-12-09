# Решение проблем с SSL сертификатом

## Проблема: Let's Encrypt не может проверить домен

Ошибка: `DNS problem: NXDOMAIN looking up A for iawuuw.com`

## Возможные причины и решения

### 1. DNS записи еще не распространились глобально

**Решение:**
```bash
cd /opt/markethelper
git pull origin master
chmod +x fix-ssl-dns.sh
./fix-ssl-dns.sh
```

Этот скрипт проверит DNS из разных источников и покажет, распространились ли записи.

**Если DNS еще не распространился:**
- Подождите 10-30 минут (иногда до 24 часов)
- Проверьте настройки DNS в панели управления доменом:
  - A запись: `@` -> `80.76.43.75`
  - A запись: `www` -> `80.76.43.75`

### 2. Домен не доступен из интернета (Firewall)

**Проверка:**
```bash
sudo ufw status
```

**Открытие портов:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

### 3. Использование standalone режима

Если nginx плагин не работает, используйте standalone режим:

```bash
cd /opt/markethelper
git pull origin master
chmod +x setup-ssl-standalone.sh
./setup-ssl-standalone.sh
```

Этот скрипт:
1. Остановит Nginx временно
2. Получит сертификат через standalone режим
3. Запустит Nginx обратно
4. Применит SSL конфигурацию

### 4. Ручная проверка DNS

Проверьте DNS из разных источников:

```bash
# Google DNS
dig +short @8.8.8.8 iawuuw.com

# Cloudflare DNS
dig +short @1.1.1.1 iawuuw.com

# Должно вернуть: 80.76.43.75
```

### 5. Проверка доступности домена

```bash
# Локально
curl -I http://iawuuw.com

# Из интернета (используйте другой сервер или онлайн сервис)
# Должен вернуть HTTP 200 или 301/302
```

## Пошаговая инструкция

1. **Проверьте DNS:**
   ```bash
   cd /opt/markethelper
   git pull origin master
   chmod +x fix-ssl-dns.sh
   ./fix-ssl-dns.sh
   ```

2. **Если DNS распространился, попробуйте получить сертификат:**
   ```bash
   certbot --nginx -d iawuuw.com -d www.iawuuw.com
   ```

3. **Если не работает, используйте standalone:**
   ```bash
   chmod +x setup-ssl-standalone.sh
   ./setup-ssl-standalone.sh
   ```

4. **После получения сертификата примените полную конфигурацию:**
   ```bash
   cp nginx.conf /etc/nginx/sites-available/markethelper
   nginx -t
   systemctl reload nginx
   ```

## Альтернативное решение: Временная работа без SSL

Если SSL критически важен, но DNS еще не распространился, можно временно работать без HTTPS:

1. Используйте временную конфигурацию:
   ```bash
   cp nginx.conf.temp-ssl /etc/nginx/sites-available/markethelper
   nginx -t
   systemctl reload nginx
   ```

2. Админ-панель будет доступна по HTTP: `http://iawuuw.com`

3. После распространения DNS получите SSL сертификат.

## Проверка после получения SSL

```bash
# Проверка HTTPS
curl -I https://iawuuw.com/api/docs

# Должен вернуть HTTP 200
```

## Полезные команды

```bash
# Просмотр логов Certbot
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Проверка конфигурации Nginx
nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx

# Проверка статуса сертификатов
sudo certbot certificates
```

## Контакты для помощи

Если проблема не решается:
1. Проверьте логи: `/var/log/letsencrypt/letsencrypt.log`
2. Убедитесь, что DNS записи настроены правильно
3. Проверьте, что порты 80 и 443 открыты в firewall
4. Убедитесь, что домен доступен из интернета

