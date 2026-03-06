# -*- coding: utf-8 -*-
"""
Скрипт для удаления пользователя 'admin' из SQLite базы данных на Railway.
"""

import sqlite3
import os

DB_FILE = "/data/family_tree.db"

print("=" * 60)
print("Удаление пользователя 'admin' из SQLite")
print("=" * 60)

if not os.path.exists(DB_FILE):
    print(f"❌ База данных не найдена: {DB_FILE}")
    exit(1)

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем пользователей
    print("\nПользователи в базе:")
    cursor.execute("SELECT id, login, email, is_admin FROM users ORDER BY id;")
    users = cursor.fetchall()
    
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
        cursor.execute("DELETE FROM users WHERE id = ?", (admin_id,))
        conn.commit()
        print(f"✅ Пользователь 'admin' удалён")
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
        print(f"Осталось пользователей: {count}")
    else:
        print("\n⚠️ Пользователь 'admin' не найден")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)
