# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(persons)')
columns = [row[1] for row in cursor.fetchall()]

print("Columns in persons table:")
for col in columns:
    print(f"  - {col}")

print(f"\nphoto_full exists: {'photo_full' in columns}")

conn.close()
