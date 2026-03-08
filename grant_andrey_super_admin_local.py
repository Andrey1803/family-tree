# -*- coding: utf-8 -*-
"""
Прямое предоставление прав СУПЕР-АДМИНА Андрею Емельянову через SQL.
Скрипт для выполнения на сервере Railway.
"""

import sqlite3
import os
import sys

# Включаем поддержку UTF-8 для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def hash_password(login: str, password: str) -> str:
    """Создать хеш пароля (SHA256 fallback)."""
    import hashlib
    raw = f"FamilyTreeApp_v1{login}{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def main():
    print("=" * 60)
    print("  Прямое предоставление прав СУПЕР-АДМИНА")
    print("  Пользователь: Андрей Емельянов")
    print("=" * 60)
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), "sync_server", "family_tree.db")
    
    if not os.path.exists(db_path):
        print(f"\n[INFO] База данных не найдена по пути: {db_path}")
        print("Этот скрипт предназначен для запуска на сервере Railway.")
        print("\nДля локального тестирования создайте БД:")
        print("  python sync_server/create_tables.py")
        return
    
    print(f"\n[INFO] Путь к БД: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT id, login, email, is_admin FROM users WHERE login = ?", ("Андрей Емельянов",))
        user = cursor.fetchone()
        
        if user:
            print(f"\n[INFO] Пользователь найден:")
            print(f"   ID: {user[0]}")
            print(f"   Логин: {user[1]}")
            print(f"   Email: {user[2]}")
            print(f"   Текущие права: {'👑 АДМИНИСТРАТОР' if user[3] else '❌ НЕТ ПРАВ'}")
            
            if user[3]:
                print("\n✅ У пользователя УЖЕ есть права АДМИНИСТРАТОРА!")
            else:
                # Предоставляем права
                cursor.execute("UPDATE users SET is_admin = 1 WHERE login = ?", ("Андрей Емельянов",))
                conn.commit()
                print("\n✅ Права СУПЕР-АДМИНА предоставлены!")
        else:
            print("\n[INFO] Пользователь 'Андрей Емельянов' не найден.")
            print("Создаю нового пользователя с правами супер-админа...")
            
            password_hash = hash_password("Андрей Емельянов", "andrey123")
            cursor.execute("""
                INSERT INTO users (login, password_hash, email, is_admin, is_active)
                VALUES (?, ?, ?, 1, 1)
            """, ("Андрей Емельянов", password_hash, "andrey@familytree.local"))
            conn.commit()
            
            user_id = cursor.lastrowid
            print(f"\n✅ Пользователь создан:")
            print(f"   ID: {user_id}")
            print(f"   Логин: Андрей Емельянов")
            print(f"   Пароль: andrey123")
            print(f"   Права: 👑 СУПЕР-АДМИНИСТРАТОР")
        
        # Показываем всех администраторов
        print("\n" + "=" * 60)
        print("  Все администраторы системы:")
        print("=" * 60)
        
        cursor.execute("SELECT id, login, email, is_admin FROM users WHERE is_admin = 1")
        admins = cursor.fetchall()
        
        for admin in admins:
            print(f"   • {admin[1]} (ID: {admin[0]}, email: {admin[2]})")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("  ✅ ГОТОВО!")
        print("=" * 60)
        print("\nТеперь Андрей Емельянов имеет ПОЛНЫЕ права:")
        print("  • Просмотр всех пользователей")
        print("  • Управление правами доступа")
        print("  • Удаление пользователей")
        print("  • Сброс паролей")
        print("  • Просмотр статистики")
        print("  • Управление деревьями")
        print("\nДанные для входа:")
        print("  Логин: Андрей Емельянов")
        print("  Пароль: andrey123 (если пользователь создавался заново)")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
