# -*- coding: utf-8 -*-
"""
Email сервис для отправки кодов подтверждения.
"""

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict

try:
    from .email_config import (
        SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD,
        SMTP_USE_TLS, EMAIL_FROM, EMAIL_SUBJECT, CODE_EXPIRY_SECONDS,
        EMAIL_TEMPLATE
    )
except ImportError:
    # Значения по умолчанию (для тестирования без SMTP)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_LOGIN = ""
    SMTP_PASSWORD = ""
    SMTP_USE_TLS = True
    EMAIL_FROM = "Family Tree <noreply@familytree.local>"
    EMAIL_SUBJECT = "Код подтверждения регистрации"
    CODE_EXPIRY_SECONDS = 600
    EMAIL_TEMPLATE = "Ваш код: {code}"

# Хранилище кодов (в памяти, для production нужна БД)
_verification_codes: Dict[str, dict] = {}


def generate_code(length: int = 6) -> str:
    """Генерация случайного кода подтверждения."""
    return ''.join(random.choices(string.digits, k=length))


def create_verification_code(email: str) -> str:
    """
    Создать код подтверждения для email.
    
    Args:
        email: Email пользователя
        
    Returns:
        Сгенерированный код
    """
    code = generate_code()
    expiry = datetime.now() + timedelta(seconds=CODE_EXPIRY_SECONDS)
    
    _verification_codes[email] = {
        'code': code,
        'expiry': expiry,
        'created_at': datetime.now()
    }
    
    return code


def verify_code(email: str, code: str) -> bool:
    """
    Проверить код подтверждения.
    
    Args:
        email: Email пользователя
        code: Введённый код
        
    Returns:
        True если код верный и не истёк
    """
    if email not in _verification_codes:
        return False
    
    stored = _verification_codes[email]
    
    # Проверяем не истёк ли код
    if datetime.now() > stored['expiry']:
        del _verification_codes[email]
        return False
    
    # Проверяем код
    if stored['code'] != code:
        return False
    
    # Код верный - удаляем его
    del _verification_codes[email]
    return True


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Отправить email.
    
    Args:
        to_email: Кому отправлять
        subject: Тема письма
        body: Текст письма
        
    Returns:
        True если отправлено успешно
    """
    if not SMTP_LOGIN or not SMTP_PASSWORD:
        print(f"[EMAIL] SMTP не настроен. Письмо для {to_email} не отправлено.")
        print(f"[EMAIL] Тема: {subject}")
        print(f"[EMAIL] Тело: {body[:100]}...")
        return False
    
    try:
        # Создаём письмо
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Подключаемся к SMTP серверу
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] Письмо отправлено на {to_email}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Ошибка отправки: {e}")
        return False


def send_verification_code(email: str) -> Optional[str]:
    """
    Отправить код подтверждения на email.
    
    Args:
        email: Email пользователя
        
    Returns:
        Код если успешно (для тестирования), None если ошибка
    """
    # Генерируем код
    code = create_verification_code(email)
    
    # Формируем письмо
    body = EMAIL_TEMPLATE.format(code=code)
    
    # Отправляем
    success = send_email(email, EMAIL_SUBJECT, body)
    
    if success:
        return code
    else:
        # Для тестирования возвращаем код даже если SMTP не настроен
        return code


def cleanup_expired_codes():
    """Очистить истёкшие коды."""
    now = datetime.now()
    expired = [email for email, data in _verification_codes.items() 
               if now > data['expiry']]
    
    for email in expired:
        del _verification_codes[email]
    
    if expired:
        print(f"[EMAIL] Очищено {len(expired)} истёкших кодов")
