import sqlite3
conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Колонки:", columns)
print("photo_full есть:", 'photo_full' in columns)
conn.close()
