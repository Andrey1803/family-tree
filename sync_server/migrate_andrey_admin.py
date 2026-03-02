# -*- coding: utf-8 -*-
"""
Миграция: Предоставление прав администратора пользователю "Андрей Емельянов"

Выполнить на сервере Railway через Railway CLI:
railway run python sync_server/migrate_andrey_admin.py

ИЛИ через панель Railway -> Settings -> Commands
"""

import sqlite3
import os

# Путь к базе данных на Railway
DB_FILE = os.environ.get('DATA_DIR', '/app/data') + '/family_tree.db'

print(f"📦 Подключение к БД: {DB_FILE}")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute('SELECT id, login, is_admin FROM users WHERE login = ?', ('Андрей Емельянов',))
    user = cursor.fetchone()
    
    if user:
        print(f"   Найден пользователь: id={user[0]}, login={user[1]}, is_admin={user[2]}")
        
        if user[2]:
            print("✅ Пользователь уже является администратором.")
        else:
            # Предоставляем права администратора
            cursor.execute('UPDATE users SET is_admin = 1 WHERE login = ?', ('Андрей Емельянов',))
            conn.commit()
            print("✅ Права администратора предоставлены!")
            
            # Проверяем результат
            cursor.execute('SELECT id, login, is_admin FROM users WHERE login = ?', ('Андрей Емельянов',))
            user = cursor.fetchone()
            print(f"   Результат: id={user[0]}, login={user[1]}, is_admin={user[2]}")
    else:
        print("⚠️ Пользователь 'Андрей Емельянов' не найден в базе данных сервера.")
        print("   Вам нужно зарегистрироваться на сервере под этим логином.")
        
        # Показываем всех пользователей
        cursor.execute('SELECT id, login, is_admin FROM users')
        users = cursor.fetchall()
        print("\n   Все пользователи:")
        for u in users:
            print(f"   - id={u[0]}, login={u[1]}, is_admin={u[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    raise
