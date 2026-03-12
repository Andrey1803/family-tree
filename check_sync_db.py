import sqlite3
import os

# Путь к БД
db_path = r"d:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server\family_tree.db"

print(f"DB path: {db_path}")
print(f"DB exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Columns:", columns)
print("photo_full exists:", 'photo_full' in columns)
conn.close()
