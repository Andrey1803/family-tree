# Настройка SMTP для отправки email на Railway

## 📋 Проблема
Если письма не отправляются и логи `[EMAIL]` не появляются в Railway Deploy Logs, это означает что:
1. Переменные окружения не настроены
2. Или SMTP сервис не может подключиться

## 🔧 Решение

### Шаг 1: Настройте переменные окружения на Railway

1. Зайдите в проект на Railway: https://railway.app/project/family-tree
2. Выберите сервис `family-tree-production`
3. Перейдите во вкладку **Variables**
4. Добавьте следующие переменные:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_LOGIN=familyroots010326@gmail.com
SMTP_PASSWORD=xryylsrdahhkjvvm
SMTP_USE_TLS=true
EMAIL_FROM=Family Tree <familyroots010326@gmail.com>
```

### Шаг 2: Проверка пароля приложения Gmail

Для Gmail **обязательно** используйте **App Password** (пароль приложения), а не обычный пароль:

1. Зайдите в Google Account: https://myaccount.google.com/
2. Перейдите в **Безопасность** → **Двухэтапная аутентификация**
3. Включите двухэтапную аутентификацию (если не включена)
4. Перейдите в **Пароли приложений** (App Passwords)
5. Создайте новый пароль для "Mail" и "Other"
6. Скопируйте 16-символьный пароль
7. Вставьте его в `SMTP_PASSWORD` на Railway

### Шаг 3: Проверка после деплоя

После обновления переменных окружения:

1. Railway автоматически перезапустит сервис
2. Зайдите в **Deploy Logs**
3. Попробуйте зарегистрироваться через форму
4. В логах должны появиться сообщения:

```
[AUTH] Запрос кода подтверждения для email: user@example.com
[AUTH] Вызов send_verification_code для user@example.com
[EMAIL] === Начало отправки письма ===
[EMAIL] Получатель: user@example.com
[EMAIL] SMTP_SERVER: smtp.gmail.com
[EMAIL] SMTP_PORT: 587
[EMAIL] SMTP_USE_TLS: true
[EMAIL] 📤 Подключение к smtp.gmail.com:587 ...
[EMAIL] 🔐 Используем SMTP + STARTTLS
[EMAIL] 🔑 Выполняем вход...
[EMAIL] 📨 Отправляем письмо...
[EMAIL] ✅ Письмо успешно отправлено на user@example.com
```

### Шаг 4: Диагностика проблем

#### ❌ Логи `[EMAIL]` не появляются
**Причина:** Модуль `email_service` не импортируется или код не вызывается

**Решение:**
- Проверьте, что файл `email_service.py` загружен на GitHub
- Проверьте логи импорта в начале запуска

#### ❌ Ошибка аутентификации SMTP
```
[EMAIL] ❌ Ошибка аутентификации SMTP: (535, ...)
```
**Причина:** Неверный логин/пароль

**Решение:**
- Используйте App Password, а не обычный пароль Gmail
- Проверьте, что двухэтапная аутентификация включена

#### ❌ Ошибка подключения
```
[EMAIL] ❌ Ошибка подключения к SMTP серверу: ...
```
**Причина:** Неправильный порт или сервер блокируется

**Решение:**
- Попробуйте порт 465 с `SMTP_USE_TLS=false`
- Проверьте, что брандмауэр не блокирует SMTP

### Шаг 5: Альтернативные настройки SMTP

Если Gmail не работает, попробуйте другие сервисы:

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

#### Outlook/Hotmail
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_LOGIN=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
```

## 🧪 Тестирование локально

Для проверки работы SMTP локально:

```bash
cd web
python -c "from email_service import send_email; send_email('test@example.com', 'Test', 'Hello')"
```

## 📝 Примечания

- **Никогда не коммитьте реальные пароли в Git!** Используйте переменные окружения
- Для production уберите `test_code` из API ответа
- Рассмотрите использование специализированных сервисов: SendGrid, Mailgun, Amazon SES
