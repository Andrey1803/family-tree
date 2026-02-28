#!/bin/bash
# Pre-start script for Railway

echo "=========================================="
echo "🔧 Railway Pre-start"
echo "=========================================="
echo "DATA_DIR: ${DATA_DIR:-/data}"
echo "PWD: $(pwd)"
echo "Files in /data: $(ls -la /data 2>/dev/null || echo 'NOT FOUND')"
echo "Files in .: $(ls -la .)"
echo ""

# Создаём директорию для данных если не существует
mkdir -p ${DATA_DIR:-/data}

echo "📦 Проверка базы данных..."
python << 'PYTHON_SCRIPT'
import os
import sqlite3

DATA_DIR = os.environ.get('DATA_DIR', '/data')
DB_FILE = os.path.join(DATA_DIR, 'family_tree.db')

print(f'📦 DATA_DIR env: {os.environ.get("DATA_DIR", "NOT SET")}')
print(f'📦 DB_FILE: {DB_FILE}')
print(f'📦 /data exists: {os.path.exists("/data")}')
print(f'📦 /data writable: {os.access("/data", os.W_OK)}')
print(f'📦 DB exists before: {os.path.exists(DB_FILE)}')

if os.path.exists(DB_FILE):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        if result:
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            print(f'✅ БД существует. Пользователей: {count}')
            # Выводим логинов
            cursor.execute('SELECT login FROM users')
            for row in cursor.fetchall():
                print(f'   - {row[0]}')
        else:
            print('⚠️  Таблица users НЕ найдена в БД!')
        conn.close()
    except Exception as e:
        print(f'❌ Ошибка чтения БД: {e}')
else:
    print('⚠️  БД НЕ существует! Будет создана.')

print(f'📦 Files in {DATA_DIR}: {os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else "DIR NOT FOUND"}')
PYTHON_SCRIPT

echo ""
echo "✅ Pre-start завершён!"
echo "🚀 Запуск Gunicorn..."
