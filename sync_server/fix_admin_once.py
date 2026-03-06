# -*- coding: utf-8 -*-
"""
Разовый скрипт для удаления 'admin' и предоставления прав Андрею Емельянову.
Запускается автоматически при старте сервиса на Railway.
"""

import sqlite3
import os

DB_FILE = os.environ.get('DATA_DIR', '/data') + '/family_tree.db'
MARKER_FILE = os.environ.get('DATA_DIR', '/data') + '/.admin_fixed'

# Проверяем выполнялось ли уже
if os.path.exists(MARKER_FILE):
    print("✅ Скрипт уже выполнялся ранее")
    exit(0)

print("=" * 60)
print("Удаление 'admin' и предоставление прав Андрею Емельянову")
print("=" * 60)

if not os.path.exists(DB_FILE):
    print(f"❌ БД не найдена: {DB_FILE}")
    exit(1)

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем пользователей
    print("\nПользователи до изменений:")
    cursor.execute("SELECT id, login, email, is_admin FROM users ORDER BY id;")
    users = cursor.fetchall()
    for user in users:
        print(f"   {user[0]}: {user[1]} (admin: {user[3]})")
    
    # Удаляем admin
    print("\n🗑️ Удаление пользователя 'admin'...")
    cursor.execute('DELETE FROM users WHERE login = "admin"')
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"✅ 'admin' удалён ({deleted} запись)")
    else:
        print("⚠️ 'admin' не найден")
    
    # Делаем Андрея админом
    print("\n⚙️ Предоставление прав Андрею Емельянову...")
    cursor.execute('UPDATE users SET is_admin = 1 WHERE login = "Андрей Емельянов"')
    updated = cursor.rowcount
    if updated > 0:
        print(f"✅ Андрей Емельянов теперь админ ({updated} запись)")
    else:
        print("⚠️ Андрей Емельянов не найден")
    
    conn.commit()
    
    # Проверяем результат
    print("\nПользователи после изменений:")
    cursor.execute("SELECT id, login, email, is_admin FROM users ORDER BY id;")
    users = cursor.fetchall()
    for user in users:
        print(f"   {user[0]}: {user[1]} (admin: {user[3]})")
    
    # Ставим маркер что скрипт выполнен
    with open(MARKER_FILE, 'w') as f:
        f.write("done")
    print(f"\n✅ Скрипт выполнен. Маркер: {MARKER_FILE}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)
