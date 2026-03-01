# -*- coding: utf-8 -*-
"""
Конфигурация email для подтверждения регистрации.
Заполните данными вашего SMTP сервера.
"""

import os

# SMTP настройки
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))  # 587 для TLS (рекомендуется), 465 для SSL
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "familyroots010326@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "xryylsrdahhkjvvm")  # Пароль приложения
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"  # True для порта 587

# От кого
EMAIL_FROM = os.environ.get("EMAIL_FROM", "Family Tree <familyroots010326@gmail.com>")
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
