# Исправление проблемы с отправкой email при регистрации

## ❌ Проблема
Пользователи жалуются, что при регистрации не приходит пароль на указанную почту.

## 🔍 Диагностика

### 1. Проверьте логи на Railway

Зайдите в Railway → ваш проект → **Deploy Logs** и попробуйте зарегистрироваться. Ищите логи:

```
[VERIFY] Запрос кода для email: user@gmail.com
```

Если таких логов нет — код не генерируется.

Если видите:
```
[VERIFY] ❌ Email не настроен: нет SENDGRID_API_KEY и SMTP_LOGIN
```
— значит переменные окружения не настроены.

### 2. Проверьте настройки через API

Откройте в браузере: `https://ваш-домен.up.railway.app/api/email/check`

Пример ответа:
```json
{
  "sendgrid": {"configured": false, "from_email": null},
  "smtp": {"configured": false, "server": null, ...},
  "method": "none"
}
```

Если `"method": "none"` — email не настроен.

## ✅ Решение

### Вариант 1: Настроить SendGrid (рекомендуется)

1. Зарегистрируйтесь на https://sendgrid.com
2. Создайте API ключ: Settings → API Keys → Create API Key
3. На Railway добавьте переменные:
   ```
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
   SENDGRID_FROM_EMAIL=familyroots010326@gmail.com
   ```
4. Перезапустите сервис

### Вариант 2: Настроить Gmail SMTP

1. Включите двухэтапную аутентификацию в Google Account
2. Создайте App Password: https://myaccount.google.com/apppasswords
3. На Railway добавьте переменные:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_LOGIN=familyroots010326@gmail.com
   SMTP_PASSWORD=xxxxxxxxxxxxxxxx  (16 символов, App Password)
   SMTP_USE_TLS=true
   EMAIL_FROM=Family Tree <familyroots010326@gmail.com>
   ```
4. Перезапустите сервис

### Вариант 3: Другие SMTP сервисы

#### Yandex Почта
```
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=465
SMTP_LOGIN=your-email@yandex.ru
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=false
```

#### Mail.ru
```
SMTP_SERVER=smtp.mail.ru
SMTP_PORT=465
SMTP_LOGIN=your-email@mail.ru
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=false
```

## 🧪 Тестирование

### Локально
```bash
cd web
python test_email.py
```

### На Railway
1. Откройте `/api/email/check` — проверьте настройки
2. Попробуйте зарегистрироваться с тестовым email
3. Проверьте Deploy Logs — ищите `[EMAIL] ✅ Письмо успешно отправлено`

## 📋 Чек-лист

- [ ] Переменные окружения добавлены на Railway
- [ ] `/api/email/check` показывает `"method": "sendgrid"` или `"method": "smtp"`
- [ ] В логах есть `[EMAIL] ✅ Письмо успешно отправлено`
- [ ] Письмо доходит до получателя
- [ ] Код подтверждения работает

## 🆘 Частые ошибки

### ❌ "SMTP не настроен (пустой логин или пароль)"
**Решение:** Добавьте `SMTP_LOGIN` и `SMTP_PASSWORD` в переменные окружения

### ❌ "Ошибка аутентификации SMTP: (535, ...)"
**Решение:** Используйте App Password, а не обычный пароль Gmail

### ❌ "SendGrid HTTP ошибка: 401"
**Решение:** Проверьте API ключ SendGrid (начинается с `SG.`)

### ❌ Письма не доходят
**Решение:**
- Проверьте спам
- Для Gmail: используйте SendGrid или App Password
- Для mail.ru/yandex.ru: SendGrid надёжнее

## 📝 Примечания

- Gmail может блокировать письма на mail.ru и yandex.ru
- Используйте SendGrid для production
- Никогда не коммитьте пароли в Git!
