#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест SMTP подключения на Railway.
Запустить через Railway Console: python test_smtp.py
"""

import os
import sys

print("=" * 60)
print("ТЕСТ SMTP ПОДКЛЮЧЕНИЯ")
print("=" * 60)

# Добавляем web в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

from email_config import SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD, SMTP_USE_TLS

print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_LOGIN: {SMTP_LOGIN}")
print(f"SMTP_PASSWORD задан: {bool(SMTP_PASSWORD)}")
print(f"SMTP_USE_TLS: {SMTP_USE_TLS}")
print()

# Тест подключения
import smtplib

try:
    print(f"Подключение к {SMTP_SERVER}:{SMTP_PORT}...")
    
    if SMTP_USE_TLS:
        print("Режим: STARTTLS")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)
        server.starttls()
    else:
        print("Режим: SSL")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)
    
    print("Подключение успешно!")
    
    print(f"Логин: {SMTP_LOGIN}")
    server.login(SMTP_LOGIN, SMTP_PASSWORD)
    print("Вход успешен!")
    
    server.quit()
    print("Тест пройден!")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"ОШИБКА: Неверный логин/пароль: {e}")
    print("Проверьте App Password в Google Account")
except smtplib.SMTPConnectError as e:
    print(f"ОШИБКА: Не удалось подключиться: {e}")
    print("Возможно, порт блокируется фаерволом Railway")
except Exception as e:
    print(f"ОШИБКА: {type(e).__name__}: {e}")

print()
print("=" * 60)
