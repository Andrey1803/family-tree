#!/bin/bash
# Pre-start script for Railway

echo "📦 Инициализация базы данных..."
python -c "
import os
import sqlite3
from app import init_db

DB_FILE = os.environ.get('DATA_DIR', '.') + '/family_tree.db'

# Проверяем есть ли таблица users
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='users'\")
if not cursor.fetchone():
    print('📦 Создание таблиц БД...')
    conn.close()
    init_db()
    print('✅ База данных инициализирована!')
else:
    print('✅ База данных уже инициализирована')
    conn.close()
"

echo "✅ База данных готова!"
echo "🚀 Запуск Gunicorn..."
