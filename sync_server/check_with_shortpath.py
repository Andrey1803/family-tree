import os
import ctypes
import sqlite3

# Получаем текущую директорию скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))

# Получаем короткий путь через Windows API
kernel32 = ctypes.windll.kernel32
GetShortPathNameW = kernel32.GetShortPathNameW

short_dir_buffer = ctypes.create_unicode_buffer(500)
GetShortPathNameW(script_dir, short_dir_buffer, 500)
short_dir = short_dir_buffer.value

print(f"Script dir (long): {script_dir}")
print(f"Script dir (short): {short_dir}")

# Меняем рабочую директорию на короткую
os.chdir(short_dir)
print(f"Current dir: {os.getcwd()}")

db_path = 'family_tree.db'
print(f"DB exists: {os.path.exists(db_path)}")

# Подключаемся к БД
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Columns:", columns)
print("photo_full exists:", 'photo_full' in columns)
conn.close()
