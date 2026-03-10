# -*- coding: utf-8 -*-
"""
Конфигурация email для подтверждения регистрации.
Заполните данными вашего SMTP сервера.

ВАЖНО: Для Gmail используйте App Password, а не обычный пароль.
Для production рекомендуется SendGrid.
"""

import os

# SendGrid (рекомендуется для production)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "")

# SMTP настройки (резервные, если SendGrid не настроен)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))  # 587 для TLS (рекомендуется), 465 для SSL
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # Пароль приложения Gmail
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"  # True для порта 587

# От кого - используем SMTP_LOGIN если SENDGRID_FROM_EMAIL не задан
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
if not EMAIL_FROM:
    if SENDGRID_FROM_EMAIL:
        EMAIL_FROM = SENDGRID_FROM_EMAIL
    elif SMTP_LOGIN:
        EMAIL_FROM = SMTP_LOGIN

EMAIL_SUBJECT = "Код подтверждения регистрации"

# Время жизни кода (секунды)
CODE_EXPIRY_SECONDS = 600  # 10 минут

# Пример письма
EMAIL_TEMPLATE = """Здравствуйте!

Ваш код подтверждения для регистрации в Family Tree: {code}

Код действителен в течение 10 минут.

Если вы не регистрировались, просто проигнорируйте это письмо.

---
Семейное древо (Family Tree)"""


def is_email_configured() -> bool:
    """Проверяет, настроен ли email сервис."""
    # Проверяем SendGrid
    if SENDGRID_API_KEY and SENDGRID_FROM_EMAIL:
        return True
    # Проверяем SMTP
    if SMTP_LOGIN and SMTP_PASSWORD and SMTP_SERVER:
        return True
    return False


def get_email_config_status() -> dict:
    """Возвращает статус конфигурации email."""
    sendgrid_configured = bool(SENDGRID_API_KEY and SENDGRID_FROM_EMAIL)
    smtp_configured = bool(SMTP_LOGIN and SMTP_PASSWORD and SMTP_SERVER)
    
    return {
        "configured": sendgrid_configured or smtp_configured,
        "sendgrid": {
            "available": sendgrid_configured,
            "api_key_set": bool(SENDGRID_API_KEY),
            "from_email_set": bool(SENDGRID_FROM_EMAIL)
        },
        "smtp": {
            "available": smtp_configured,
            "server": SMTP_SERVER if smtp_configured else "not configured",
            "port": SMTP_PORT if smtp_configured else 0,
            "login_set": bool(SMTP_LOGIN),
            "password_set": bool(SMTP_PASSWORD),
            "use_tls": SMTP_USE_TLS
        },
        "email_from": EMAIL_FROM
    }
