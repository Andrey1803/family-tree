# -*- coding: utf-8 -*-
import sqlite3
import os

# Получаем текущую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

print(f"Working directory: {os.getcwd()}")
print(f"DB exists: {os.path.exists('family_tree.db')}")

conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Columns:", columns)
print("photo_full present:", 'photo_full' in columns)
conn.close()
