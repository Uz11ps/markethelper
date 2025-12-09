# Настройка API SalesFinder

Если внешний API `salesfinder.ru` недоступен или изменился URL, вы можете настроить его через переменные окружения.

## Переменные окружения

Добавьте в файл `.env`:

```bash
# URL для авторизации на SalesFinder
SALESFINDER_LOGIN_URL=https://salesfinder.ru/api/user/signIn

# URL для проверки пользователя на SalesFinder
SALESFINDER_CHECK_URL=https://salesfinder.ru/api/user/getUser
```

## Проверка текущего URL

Текущий URL можно проверить в логах backend при попытке добавить файл:

```bash
docker-compose -f docker-compose.prod.yml logs backend | grep "SALESFINDER"
```

## Решение проблем

### Ошибка 404

Если вы получаете ошибку `404 Not Found`:

1. **Проверьте доступность API:**
   ```bash
   curl -X POST https://salesfinder.ru/api/user/signIn \
     -H "Content-Type: application/json" \
     -d '{"user_email_address":"test@example.com","user_password":"test"}'
   ```

2. **Проверьте правильность URL** - возможно, API изменился

3. **Свяжитесь с поддержкой SalesFinder** для получения актуального URL API

### Ошибка подключения

Если вы получаете ошибку подключения:

1. Проверьте доступность сервера `salesfinder.ru`
2. Проверьте настройки сети/firewall
3. Проверьте DNS разрешение

## Логирование

Все попытки подключения к SalesFinder API логируются. Для просмотра логов:

```bash
docker-compose -f docker-compose.prod.yml logs backend | grep -i salesfinder
```

