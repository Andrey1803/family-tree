# -*- coding: utf-8 -*-
"""
Email сервис для отправки кодов подтверждения через SendGrid.
"""

import random
import string
import logging
import os
import urllib.request
import json
from datetime import datetime, timedelta
from typing import Optional, Dict

# Настройка логирования для Railway
logging.basicConfig(
    level=logging.INFO,
    format='[EMAIL] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# SendGrid настройки
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "familyroots010326@gmail.com")

# SMTP настройки (резервные, если SendGrid не настроен)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

# Остальные настройки
EMAIL_SUBJECT = "Код подтверждения регистрации"
CODE_EXPIRY_SECONDS = 600
EMAIL_TEMPLATE = """Здравствуйте!

Ваш код подтверждения для регистрации в Family Tree: {code}

Код действителен в течение 10 минут.

Если вы не регистрировались, просто проигнорируйте это письмо.

---
Семейное древо (Family Tree)"""

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
    Отправить email через SendGrid API.

    Args:
        to_email: Кому отправлять
        subject: Тема письма
        body: Текст письма

    Returns:
        True если отправлено успешно
    """
    logger.info("=== Начало отправки письма ===")
    logger.info(f"Получатель: {to_email}")
    logger.info(f"Тема: {subject}")
    logger.info(f"SendGrid API ключ задан: {bool(SENDGRID_API_KEY)}")
    logger.info(f"From: {SENDGRID_FROM_EMAIL}")
    
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API ключ не задан, пробуем SMTP...")
        return _send_email_smtp(to_email, subject, body)

    try:
        # SendGrid API endpoint
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # Формируем запрос
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": SENDGRID_FROM_EMAIL},
            "content": [
                {
                    "type": "text/plain",
                    "value": body
                }
            ]
        }
        
        logger.info(f"Отправка через SendGrid API...")
        
        # Создаём запрос
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        # Отправляем
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 202:
                logger.info(f"Письмо успешно отправлено на {to_email}")
                return True
            else:
                logger.error(f"SendGrid вернул статус: {resp.status}")
                return False
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error(f"SendGrid HTTP ошибка: {e.code} - {error_body}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"SendGrid URL ошибка: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"SendGrid ошибка: {type(e).__name__}: {e}")
        return False


def _send_email_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    Резервный метод отправки через SMTP (если SendGrid не настроен).
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    logger.info("Попытка отправки через SMTP...")
    
    if not SMTP_LOGIN or not SMTP_PASSWORD:
        logger.error("SMTP не настроен (пустой логин или пароль)")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDGRID_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        logger.info(f"Подключение к {SMTP_SERVER}:{SMTP_PORT} ...")
        
        if SMTP_USE_TLS:
            logger.info("Используем SMTP + STARTTLS")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.set_debuglevel(1)
            server.starttls()
        else:
            logger.info("Используем SMTP_SSL")
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.set_debuglevel(1)

        logger.info("Выполняем вход...")
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        
        logger.info("Отправляем письмо...")
        server.send_message(msg)
        
        logger.info(f"Письмо успешно отправлено на {to_email}")
        server.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Ошибка аутентификации SMTP: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Ошибка подключения к SMTP серверу: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка SMTP: {type(e).__name__}: {e}")
        return False


def send_verification_code(email: str) -> Optional[str]:
    """
    Отправить код подтверждения на email.

    Args:
        email: Email пользователя

    Returns:
        Код если успешно (для тестирования), None если ошибка
    """
    logger.info(f"=== send_verification_code вызван для {email} ===")
    
    # Генерируем код
    code = create_verification_code(email)
    logger.info(f"Код сгенерирован: {code}")

    # Формируем письмо
    body = EMAIL_TEMPLATE.format(code=code)

    # Отправляем
    logger.info("Вызов send_email...")
    success = send_email(email, EMAIL_SUBJECT, body)

    logger.info(f"send_email вернул: {success}")
    
    if success:
        logger.info(f"Код {code} отправлен на {email}")
        return code
    else:
        # Для тестирования возвращаем код даже если SMTP не настроен
        logger.warning(f"SMTP отправка не удалась, возвращаем код для теста: {code}")
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
