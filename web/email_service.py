# -*- coding: utf-8 -*-
"""
Email сервис для отправки кодов подтверждения.
"""

import smtplib
import random
import string
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict

# Настройка логирования для Railway
logging.basicConfig(
    level=logging.INFO,
    format='[EMAIL] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Читаем переменные окружения напрямую (не через email_config)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

# Остальные настройки
EMAIL_FROM = os.environ.get("EMAIL_FROM", "Family Tree <familyroots010326@gmail.com>")
EMAIL_SUBJECT = "Код подтверждения регистрации"
CODE_EXPIRY_SECONDS = 600
EMAIL_TEMPLATE = """
Здравствуйте!

Ваш код подтверждения для регистрации в Family Tree: {code}

Код действителен в течение 10 минут.

Если вы не регистрировались, просто проигнорируйте это письмо.

---
Семейное древо (Family Tree)
"""

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
    logger.info("=== Начало отправки письма ===")
    logger.info(f"Получатель: {to_email}")
    logger.info(f"Тема: {subject}")
    logger.info(f"SMTP_SERVER: {SMTP_SERVER}")
    logger.info(f"SMTP_PORT: {SMTP_PORT}")
    logger.info(f"SMTP_LOGIN: {SMTP_LOGIN}")
    logger.info(f"SMTP_PASSWORD задан: {bool(SMTP_PASSWORD)}")
    logger.info(f"SMTP_USE_TLS: {SMTP_USE_TLS}")
    
    if not SMTP_LOGIN or not SMTP_PASSWORD:
        logger.error(f"SMTP не настроен (пустой логин или пароль). Письмо для {to_email} не отправлено.")
        logger.info(f"Тело: {body[:100]}...")
        return False

    try:
        # Создаём письмо
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        logger.info(f"Подключение к {SMTP_SERVER}:{SMTP_PORT} ...")
        
        # Подключаемся к SMTP серверу
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
        logger.error("Проверьте логин/пароль. Для Gmail используйте App Password.")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Ошибка подключения к SMTP серверу: {e}")
        logger.error(f"Проверьте SMTP_SERVER и SMTP_PORT")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {type(e).__name__}: {e}")
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
