#!/bin/bash
# Pre-start script for Railway

# Создаём директорию для данных если не существует
mkdir -p /data

echo "📦 Инициализация базы данных..."
python -c "
import os
import sqlite3
from app import init_db

DB_FILE = os.environ.get('DATA_DIR', '/data') + '/family_tree.db'

print(f'📦 DB_FILE: {DB_FILE}')

# Проверяем есть ли таблица users
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='users'\")
    result = cursor.fetchone()
    if not result:
        print('📦 Создание таблиц БД...')
        conn.close()
        init_db()
        print('✅ База данных инициализирована!')
    else:
        print('✅ База данных уже инициализирована')
    conn.close()
except Exception as e:
    print(f'❌ Ошибка БД: {e}')
    print('📦 Попытка создания БД...')
    init_db()
    print('✅ База данных создана!')
"

echo "✅ База данных готова!"
echo "🚀 Запуск Gunicorn..."
