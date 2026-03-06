# -*- coding: utf-8 -*-
"""
Скрипт для удаления пользователя 'admin' из базы данных Railway.
Использует psycopg2 для подключения к PostgreSQL.

Запуск на Railway:
1. Railway → project → Deployments → New → Empty Service
2. Command: python remove_admin_user.py
"""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 не установлен. Добавьте в requirements.txt: psycopg2-binary")
    sys.exit(1)

# Railway автоматически предоставляет DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL не найден!")
    print("   Убедитесь, что к проекту подключена база данных PostgreSQL")
    sys.exit(1)

print("=" * 60)
print("Удаление пользователя 'admin' из базы данных")
print("=" * 60)

try:
    # Подключение к базе данных
    print("\nПодключение к базе данных...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    print("✅ Подключение успешно")
    
    # Проверяем таблицу
    print("\nПроверка таблицы users...")
    cur.execute("SELECT id, login, email, is_admin FROM users ORDER BY id;")
    users = cur.fetchall()
    
    print(f"Найдено пользователей: {len(users)}")
    for user in users:
        print(f"   {user[0]}: {user[1]} ({user[2]}) - admin: {user[3]}")
    
    # Ищем admin
    admin_id = None
    for user in users:
        if user[1] == 'admin':
            admin_id = user[0]
            break
    
    if admin_id:
        print(f"\nУдаление пользователя 'admin' (id={admin_id})...")
        cur.execute("DELETE FROM users WHERE login = 'admin';")
        print(f"✅ Пользователь 'admin' удалён")
        
        # Проверяем результат
        cur.execute("SELECT COUNT(*) FROM users;")
        count = cur.fetchone()[0]
        print(f"Осталось пользователей: {count}")
    else:
        print("\n⚠️ Пользователь 'admin' не найден")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
    
except psycopg2.Error as e:
    print(f"❌ Ошибка базы данных: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)
