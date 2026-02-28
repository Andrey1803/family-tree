#!/bin/bash
# Pre-start script for Railway

echo "=========================================="
echo "🔧 Railway Pre-start"
echo "=========================================="
echo "DATA_DIR: ${DATA_DIR:-/data}"
echo "PWD: $(pwd)"
echo ""

# Создаём директорию для данных если не существует
mkdir -p ${DATA_DIR:-/data}

echo "📦 Проверка базы данных..."
python -c "
import os
import sqlite3
from app import init_db

DATA_DIR = os.environ.get('DATA_DIR', '/data')
DB_FILE = os.path.join(DATA_DIR, 'family_tree.db')

print(f'📦 DB_FILE: {DB_FILE}')
print(f'📦 DATA_DIR exists: {os.path.exists(DATA_DIR)}')
print(f'📦 DB exists: {os.path.exists(DB_FILE)}')

# Проверяем есть ли таблица users
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='users'\")
    result = cursor.fetchone()
    if not result:
        print('📦 Таблица users не найдена. Создание...')
        conn.close()
        init_db()
        print('✅ База данных инициализирована!')
    else:
        # Проверяем пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        print(f'✅ База данных существует. Пользователей: {count}')
    conn.close()
except Exception as e:
    print(f'❌ Ошибка БД: {e}')
    print('📦 Попытка создания БД...')
    init_db()
    print('✅ База данных создана!')
"

echo ""
echo "✅ База данных готова!"
echo "🚀 Запуск Gunicorn..."
