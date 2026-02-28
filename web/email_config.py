# -*- coding: utf-8 -*-
"""
Конфигурация email для подтверждения регистрации.
Заполните данными вашего SMTP сервера.
"""

# SMTP настройки
SMTP_SERVER = "smtp.gmail.com"  # или smtp.yandex.ru
SMTP_PORT = 587  # 587 для TLS, 465 для SSL
SMTP_LOGIN = "your-email@gmail.com"  # Ваш email
SMTP_PASSWORD = "your-app-password"  # Пароль приложения (не обычный пароль!)
SMTP_USE_TLS = True

# От кого
EMAIL_FROM = "Family Tree <your-email@gmail.com>"
EMAIL_SUBJECT = "Код подтверждения регистрации"

# Время жизни кода (секунды)
CODE_EXPIRY_SECONDS = 600  # 10 минут

# Пример письма
EMAIL_TEMPLATE = """
Здравствуйте!

Ваш код подтверждения для регистрации в Family Tree: {code}

Код действителен в течение 10 минут.

Если вы не регистрировались, просто проигнорируйте это письмо.

---
Семейное древо (Family Tree)
"""
