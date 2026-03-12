# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(persons)')
columns = [row[1] for row in cursor.fetchall()]

with open('migration_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"Колонки в таблице persons: {columns}\n")
    f.write(f"photo_full существует: {'photo_full' in columns}\n")

conn.close()
print("Результат записан в migration_result.txt")
