# -*- coding: utf-8 -*-
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'family_tree.db')

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(persons)')
columns = [row[1] for row in cursor.fetchall()]

result = f"Колонки в таблице persons: {columns}\nphoto_full существует: {'photo_full' in columns}\n"

with open(os.path.join(os.path.dirname(__file__), 'migration_result.txt'), 'w', encoding='utf-8') as f:
    f.write(result)

print(result)
conn.close()
