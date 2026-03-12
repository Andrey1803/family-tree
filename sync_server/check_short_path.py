import sqlite3
import os
import ctypes

# Используем ctypes для получения короткого пути
kernel32 = ctypes.windll.kernel32
GetShortPathNameW = kernel32.GetShortPathNameW

# Получаем текущую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'family_tree.db')

# Получаем короткий путь
short_path = ctypes.create_unicode_buffer(500)
GetShortPathNameW(db_path, short_path, 500)
short_db_path = short_path.value

print(f"Long path: {db_path}")
print(f"Short path: {short_db_path}")
print(f"DB exists (long): {os.path.exists(db_path)}")
print(f"DB exists (short): {os.path.exists(short_db_path)}")

# Пробуем подключиться используя короткий путь
try:
    conn = sqlite3.connect(short_db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Columns:", columns)
    print("photo_full exists:", 'photo_full' in columns)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
