import sqlite3

# Используем raw string для пути
db_path = r'\\?\d:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server\family_tree.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Колонки:", columns)
print("photo_full есть:", 'photo_full' in columns)
conn.close()
