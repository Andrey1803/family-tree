# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки отправки email.
Запуск: python test_email.py [email]
"""

import sys
import os

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_service import send_email, send_verification_code, cleanup_expired_codes

def test_send_email():
    """Тест прямой отправки email."""
    print("=" * 60)
    print("ТЕСТ ОТПРАВКИ EMAIL")
    print("=" * 60)
    
    # Проверяем настройки
    from email_service import SENDGRID_API_KEY, SMTP_LOGIN, SMTP_PASSWORD
    
    print("\n📋 Проверка настроек:")
    print(f"  SENDGRID_API_KEY задан: {bool(SENDGRID_API_KEY)}")
    print(f"  SMTP_LOGIN: {SMTP_LOGIN}")
    print(f"  SMTP_PASSWORD задан: {bool(SMTP_PASSWORD)}")
    
    if not SENDGRID_API_KEY and not SMTP_LOGIN:
        print("\n❌ Email не настроен!")
        print("Добавьте переменные окружения:")
        print("  - SENDGRID_API_KEY=ваш_ключ (SendGrid)")
        print("  - или SMTP_SERVER, SMTP_LOGIN, SMTP_PASSWORD (SMTP)")
        return False
    
    # Спрашиваем email для теста
    test_email = input("\n📧 Введите email для теста: ").strip()
    if not test_email:
        print("❌ Email не введён")
        return False
    
    print(f"\n📤 Отправка тестового письма на {test_email}...")
    
    success = send_email(
        to_email=test_email,
        subject="Тест Family Tree",
        body="Это тестовое письмо от Family Tree. Если вы его получили - настройка работает!"
    )
    
    if success:
        print(f"\n✅ Письмо успешно отправлено на {test_email}!")
    else:
        print(f"\n❌ Ошибка отправки на {test_email}")
        print("Проверьте логи выше для деталей")
    
    return success


def test_send_verification_code():
    """Тест отправки кода подтверждения."""
    print("\n" + "=" * 60)
    print("ТЕСТ ОТПРАВКИ КОДА ПОДТВЕРЖДЕНИЯ")
    print("=" * 60)
    
    test_email = input("\n📧 Введите email для отправки кода: ").strip()
    if not test_email:
        print("❌ Email не введён")
        return False
    
    print(f"\n📤 Отправка кода на {test_email}...")
    
    code = send_verification_code(test_email)
    
    if code:
        print(f"\n✅ Код сгенерирован: {code}")
        print("Проверьте email (если настроен) или введите код для проверки:")
        
        # Проверяем код
        input_code = input("Введите код из письма: ").strip()
        
        from email_service import verify_code
        if verify_code(test_email, input_code):
            print("✅ Код подтверждён!")
            return True
        else:
            print("❌ Неверный код или истёк срок действия")
            return False
    else:
        print("\n❌ Ошибка генерации/отправки кода")
        return False


def test_check_settings():
    """Проверка настроек без отправки."""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА НАСТРОЕК EMAIL")
    print("=" * 60)
    
    from email_service import (
        SENDGRID_API_KEY, SENDGRID_FROM_EMAIL,
        SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD, SMTP_USE_TLS
    )
    
    print("\n📋 SendGrid настройки:")
    print(f"  API ключ: {'✅ задан' if SENDGRID_API_KEY else '❌ не задан'}")
    print(f"  FROM_EMAIL: {SENDGRID_FROM_EMAIL or '❌ не задан'}")
    
    print("\n📋 SMTP настройки:")
    print(f"  SERVER: {SMTP_SERVER}")
    print(f"  PORT: {SMTP_PORT}")
    print(f"  LOGIN: {SMTP_LOGIN}")
    print(f"  PASSWORD: {'✅ задан' if SMTP_PASSWORD else '❌ не задан'}")
    print(f"  USE_TLS: {SMTP_USE_TLS}")
    
    # Определяем метод отправки
    if SENDGRID_API_KEY:
        print("\n✅ Метод отправки: SendGrid API")
    elif SMTP_LOGIN and SMTP_PASSWORD:
        print(f"\n✅ Метод отправки: SMTP ({SMTP_SERVER}:{SMTP_PORT})")
    else:
        print("\n❌ Email не настроен!")
        return False
    
    return True


if __name__ == "__main__":
    print("\n🌳 Family Tree - Тест Email\n")
    
    if len(sys.argv) > 1:
        # Если передан email в аргументах
        test_email_arg = sys.argv[1]
        print(f"Тест с email: {test_email_arg}")
        
        # Запускаем все тесты
        test_check_settings()
        test_send_verification_code()
    else:
        # Интерактивный режим
        print("Выберите тест:")
        print("1. Проверка настроек")
        print("2. Тест отправки email")
        print("3. Тест отправки кода подтверждения")
        print("4. Все тесты")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == "1":
            test_check_settings()
        elif choice == "2":
            test_send_email()
        elif choice == "3":
            test_send_verification_code()
        elif choice == "4":
            test_check_settings()
            test_send_email()
            test_send_verification_code()
        else:
            print("❌ Неверный выбор")
    
    # Очищаем истёкшие коды
    cleanup_expired_codes()
    
    print("\n✅ Тест завершён")
