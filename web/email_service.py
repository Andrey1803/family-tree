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
from datetime import datetime, timedelta, timezone
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
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "")

# SMTP настройки (резервные, если SendGrid не настроен)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

# EMAIL_FROM - используем SMTP_LOGIN для Gmail чтобы избежать DMARC проблем
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
if not EMAIL_FROM:
    if SENDGRID_FROM_EMAIL:
        EMAIL_FROM = SENDGRID_FROM_EMAIL
    elif SMTP_LOGIN:
        EMAIL_FROM = SMTP_LOGIN

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
    Использует UTC время для консистентности.

    Args:
        email: Email пользователя

    Returns:
        Сгенерированный код
    """
    code = generate_code()
    now = datetime.now(timezone.utc)  # Используем UTC
    expiry = now + timedelta(seconds=CODE_EXPIRY_SECONDS)

    # Проверяем есть ли уже код для этого email
    if email in _verification_codes:
        logger.warning(f"[VERIFY] ⚠️ Для {email} уже есть код ({_verification_codes[email]['code'][:2]}***), перезаписываем")

    _verification_codes[email] = {
        'code': code,
        'expiry': expiry,
        'created_at': now
    }

    logger.info(f"[VERIFY] Код создан для {email}: {code[:2]}*** (истекает через {CODE_EXPIRY_SECONDS}с)")
    logger.info(f"[VERIFY] Время создания: {now}, истечения: {expiry}")
    return code


def verify_code(email: str, code: str) -> bool:
    """
    Проверить код подтверждения.
    Использует UTC время для консистентности.

    Args:
        email: Email пользователя
        code: Введённый код

    Returns:
        True если код верный и не истёк
    """
    logger.info(f"[VERIFY] Проверка кода для email: {email}")
    
    if email not in _verification_codes:
        logger.warning(f"[VERIFY] ❌ Email '{email}' не найден в хранилище кодов")
        logger.warning(f"[VERIFY] Доступные emails: {list(_verification_codes.keys())}")
        return False

    stored = _verification_codes[email]
    logger.info(f"[VERIFY] Найден код для {email}: {stored['code'][:2]}*** (введён: {code})")

    # Проверяем не истёк ли код (используем UTC)
    now = datetime.now(timezone.utc)
    expiry = stored['expiry']
    created = stored['created_at']
    
    logger.info(f"[VERIFY] Текущее время: {now}")
    logger.info(f"[VERIFY] Код создан: {created}, истекает: {expiry}")

    if now > expiry:
        time_diff = now - created
        logger.warning(f"[VERIFY] ❌ Код истёк! Прошло {time_diff.total_seconds():.1f}с (лимит: {CODE_EXPIRY_SECONDS}с)")
        del _verification_codes[email]
        return False

    # Проверяем код
    if stored['code'] != code:
        logger.warning(f"[VERIFY] ❌ Код не совпадает")
        return False

    # Код верный - удаляем его
    logger.info(f"[VERIFY] ✅ Код подтверждён для {email}")
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
    logger.info(f"[EMAIL] === Начало отправки письма ===")
    logger.info(f"[EMAIL] Получатель: {to_email}")
    logger.info(f"[EMAIL] Тема: {subject}")

    if not SENDGRID_API_KEY:
        logger.warning("[EMAIL] SendGrid API ключ не задан, пробуем SMTP...")
        return _send_email_smtp(to_email, subject, body)

    try:
        # SendGrid API endpoint
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # Проверяем FROM_EMAIL
        if not SENDGRID_FROM_EMAIL:
            logger.error("[EMAIL] SENDGRID_FROM_EMAIL не задан!")
            return False

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

        logger.info(f"[EMAIL] Отправка через SendGrid API...")
        logger.info(f"[EMAIL] FROM: {SENDGRID_FROM_EMAIL}")
        logger.info(f"[EMAIL] API ключ задан: {bool(SENDGRID_API_KEY)}")

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
        logger.info(f"[EMAIL] 📤 Отправка запроса к SendGrid...")
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 202:
                logger.info(f"[EMAIL] ✅ Письмо успешно отправлено на {to_email}")
                return True
            else:
                logger.error(f"[EMAIL] ❌ SendGrid вернул статус: {resp.status}")
                return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error(f"[EMAIL] ❌ SendGrid HTTP ошибка: {e.code}")
        logger.error(f"[EMAIL] Детали: {error_body}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"[EMAIL] ❌ SendGrid URL ошибка: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] ❌ SendGrid ошибка: {type(e).__name__}: {e}")
        return False


def _send_email_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    Резервный метод отправки через SMTP (если SendGrid не настроен).
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    logger.info(f"[EMAIL] === Попытка отправки через SMTP ===")
    logger.info(f"[EMAIL] Получатель: {to_email}")
    logger.info(f"[EMAIL] SMTP_SERVER: {SMTP_SERVER}")
    logger.info(f"[EMAIL] SMTP_PORT: {SMTP_PORT}")
    logger.info(f"[EMAIL] SMTP_LOGIN: {SMTP_LOGIN}")
    logger.info(f"[EMAIL] SMTP_PASSWORD задан: {bool(SMTP_PASSWORD)}")
    logger.info(f"[EMAIL] SMTP_USE_TLS: {SMTP_USE_TLS}")

    if not SMTP_LOGIN or not SMTP_PASSWORD:
        logger.error("[EMAIL] ❌ SMTP не настроен (пустой логин или пароль)")
        logger.error("[EMAIL] Для настройки добавьте переменные окружения:")
        logger.error("[EMAIL] - SMTP_SERVER=smtp.gmail.com")
        logger.error("[EMAIL] - SMTP_PORT=587")
        logger.error("[EMAIL] - SMTP_LOGIN=ваш_email@gmail.com")
        logger.error("[EMAIL] - SMTP_PASSWORD=пароль_приложения")
        return False

    try:
        msg = MIMEMultipart()
        # Используем EMAIL_FROM который настроен правильно
        msg['From'] = EMAIL_FROM or SMTP_LOGIN
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        logger.info(f"[EMAIL] 📤 From: {msg['From']}")

        logger.info(f"[EMAIL] 📤 Подключение к {SMTP_SERVER}:{SMTP_PORT} ...")

        if SMTP_USE_TLS:
            logger.info("[EMAIL] 🔐 Используем SMTP + STARTTLS")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.set_debuglevel(1)
            server.starttls()
        else:
            logger.info("[EMAIL] 🔐 Используем SMTP_SSL")
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.set_debuglevel(1)

        logger.info("[EMAIL] 🔑 Выполняем вход...")
        server.login(SMTP_LOGIN, SMTP_PASSWORD)

        logger.info("[EMAIL] 📨 Отправляем письмо...")
        server.send_message(msg)

        logger.info(f"[EMAIL] ✅ Письмо успешно отправлено на {to_email}")
        server.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[EMAIL] ❌ Ошибка аутентификации SMTP: {e}")
        logger.error("[EMAIL] Проверьте логин/пароль (для Gmail используйте App Password)")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"[EMAIL] ❌ Ошибка подключения к SMTP серверу: {e}")
        logger.error("[EMAIL] Проверьте сервер/порт или попробуйте порт 465 с SMTP_USE_TLS=false")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"[EMAIL] ❌ SMTP ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] ❌ Неизвестная ошибка SMTP: {type(e).__name__}: {e}")
        return False


def send_verification_code(email: str) -> Optional[str]:
    """
    Отправить код подтверждения на email.

    Args:
        email: Email пользователя

    Returns:
        Код если успешно, None если ошибка
    """
    logger.info(f"[VERIFY] Запрос кода для email: {email}")
    
    # Генерируем код
    code = create_verification_code(email)
    logger.info(f"[VERIFY] Код сгенерирован: {code[:2]}*** (полный: {code})")

    # Формируем письмо
    body = EMAIL_TEMPLATE.format(code=code)
    logger.info(f"[VERIFY] Тело письма: {body[:100]}...")

    # Проверяем настройки перед отправкой
    if not SENDGRID_API_KEY and not SMTP_LOGIN:
        logger.error("[VERIFY] ❌ Email не настроен: нет SENDGRID_API_KEY и SMTP_LOGIN")
        logger.error("[VERIFY] Для настройки добавьте переменные окружения:")
        logger.error("[VERIFY] - SENDGRID_API_KEY=ваш_ключ (SendGrid)")
        logger.error("[VERIFY] - или SMTP_SERVER, SMTP_LOGIN, SMTP_PASSWORD (SMTP)")
        # Возвращаем None чтобы показать ошибку пользователю
        return None

    # Отправляем
    logger.info(f"[VERIFY] Вызов send_email...")
    success = send_email(email, EMAIL_SUBJECT, body)
    logger.info(f"[VERIFY] Результат отправки: {'✅ Успешно' if success else '❌ Ошибка'}")

    if success:
        logger.info(f"[VERIFY] Код успешно отправлен на {email}")
        return code
    else:
        logger.error(f"[VERIFY] Не удалось отправить код на {email}")
        return None


def cleanup_expired_codes():
    """Очистить истёкшие коды."""
    now = datetime.now()
    expired = [email for email, data in _verification_codes.items() 
               if now > data['expiry']]
    
    for email in expired:
        del _verification_codes[email]
    
    if expired:
        print(f"[EMAIL] Очищено {len(expired)} истёкших кодов")
