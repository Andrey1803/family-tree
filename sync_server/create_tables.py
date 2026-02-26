# -*- coding: utf-8 -*-
"""Прямое создание таблицы users"""

import sqlite3
import os
from app import _password_hash

DB_FILE = os.environ.get('DATA_DIR', '.') + '/family_tree.db'

print(f"📦 Создание БД: {DB_FILE}")

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

# Создаём администратора
admin_password = _password_hash("admin", "admin123")
cursor.execute('''
INSERT OR IGNORE INTO users (login, password_hash, email, is_admin)
VALUES (?, ?, ?, ?)
''', ("admin", admin_password, "admin@familytree.local", 1))

conn.commit()
conn.close()

print("✅ Таблица users создана!")
print("✅ Администратор admin/admin123 создан!")
