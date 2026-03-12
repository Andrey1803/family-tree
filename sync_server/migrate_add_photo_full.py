# -*- coding: utf-8 -*-
"""
Миграция БД: добавление поля photo_full в таблицу persons.

Запуск: python migrate_add_photo_full.py
"""

import sqlite3
import os

DB_FILE = os.environ.get('DATA_DIR', '.') + '/family_tree.db'

print(f"[MIGRATION] Database: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Проверяем, существует ли уже колонка photo_full
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]

print(f"[MIGRATION] Существующие колонки: {columns}")

if 'photo_full' in columns:
    print("[MIGRATION] ✅ Колонка photo_full уже существует!")
else:
    print("[MIGRATION] Добавляем колонку photo_full...")
    cursor.execute('ALTER TABLE persons ADD COLUMN photo_full BLOB')
    print("[MIGRATION] ✅ Колонка photo_full добавлена!")

# Проверяем результат
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print(f"[MIGRATION] Итоговые колонки: {columns}")

conn.commit()
conn.close()

print("[MIGRATION] ✅ Миграция завершена!")
