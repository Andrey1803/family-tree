#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки переменных окружения SMTP на Railway.
Запустите через Railway Console или локально.
"""

import os
import sys

print("=" * 60)
print("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ SMTP")
print("=" * 60)

# Проверяем SMTP переменные
smtp_vars = {
    'SMTP_SERVER': os.environ.get('SMTP_SERVER', 'НЕ ЗАДАНА'),
    'SMTP_PORT': os.environ.get('SMTP_PORT', 'НЕ ЗАДАНА'),
    'SMTP_LOGIN': os.environ.get('SMTP_LOGIN', 'НЕ ЗАДАНА'),
    'SMTP_PASSWORD': '***' if os.environ.get('SMTP_PASSWORD') else 'НЕ ЗАДАНА',
    'SMTP_USE_TLS': os.environ.get('SMTP_USE_TLS', 'НЕ ЗАДАНА'),
    'EMAIL_FROM': os.environ.get('EMAIL_FROM', 'НЕ ЗАДАНА'),
}

for var, value in smtp_vars.items():
    print(f"{var}: {value}")

print()
print("=" * 60)
print("ПРОВЕРКА ДОСТУПНОСТИ EMAIL МОДУЛЕЙ")
print("=" * 60)

# Проверяем импорт email_service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))
    from email_config import SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD, SMTP_USE_TLS
    print(f"✓ email_config импортирован успешно")
    print(f"  SMTP_SERVER: {SMTP_SERVER}")
    print(f"  SMTP_PORT: {SMTP_PORT}")
    print(f"  SMTP_LOGIN: {SMTP_LOGIN}")
    print(f"  SMTP_PASSWORD задан: {bool(SMTP_PASSWORD)}")
    print(f"  SMTP_USE_TLS: {SMTP_USE_TLS}")
except Exception as e:
    print(f"✗ Ошибка импорта email_config: {e}")

print()
print("=" * 60)
print("ТЕСТОВАЯ ОТПРАВКА EMAIL (если настроен)")
print("=" * 60)

test_email = os.environ.get('TEST_EMAIL', '')
if test_email:
    try:
        from email_service import send_email
        result = send_email(test_email, "Тест SMTP", "Это тестовое письмо от Family Tree")
        print(f"Результат: {'✓ Успешно' if result else '✗ Ошибка'}")
    except Exception as e:
        print(f"✗ Ошибка отправки: {e}")
else:
    print("TEST_EMAIL не задан. Для теста добавьте переменную TEST_EMAIL")

print()
print("=" * 60)
