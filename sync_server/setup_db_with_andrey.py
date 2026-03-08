# -*- coding: utf-8 -*-
"""Создание таблицы users с супер-админом Андреем Емельяновым"""

import sqlite3
import hashlib
import os

def _password_hash(login: str, password: str) -> str:
    """Создать хеш пароля (SHA256)."""
    raw = f"FamilyTreeApp_v1{login}{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

# Определяем путь к БД
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, 'family_tree.db')

print(f"[DB] Creating database: {DB_FILE}")

# Удаляем старую БД если существует
if os.path.exists(DB_FILE):
    try:
        os.remove(DB_FILE)
        print(f"[DB] Old database removed")
    except Exception as e:
        print(f"[DB] Could not remove old DB: {e}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Создаём таблицу users
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0
)
''')

# Создаём администратора по умолчанию
admin_password = _password_hash("admin", "admin123")
cursor.execute('''
INSERT INTO users (login, password_hash, email, is_admin)
VALUES (?, ?, ?, ?)
''', ("admin", admin_password, "admin@familytree.local", 1))

# Создаём Андрея Емельянова как супер-админа
andrey_password = _password_hash("Андрей Емельянов", "andrey123")
cursor.execute('''
INSERT INTO users (login, password_hash, email, is_admin)
VALUES (?, ?, ?, ?)
''', ("Андрей Емельянов", andrey_password, "andrey@familytree.local", 1))

conn.commit()

# Проверяем результат
cursor.execute("SELECT id, login, email, is_admin FROM users")
users = cursor.fetchall()

print("\n[DB] Users created:")
for user in users:
    admin_status = "SUPER-ADMIN" if user[3] else "user"
    print(f"   ID: {user[0]}, Login: {user[1]}, Email: {user[2]}, Rights: {admin_status}")

conn.close()

print("\n" + "=" * 60)
print("  DATABASE CREATED SUCCESSFULLY!")
print("=" * 60)
print("\nSuper-admin credentials:")
print("  Login: Андрей Емельянов")
print("  Password: andrey123")
print("\nDefault admin credentials:")
print("  Login: admin")
print("  Password: admin123")
