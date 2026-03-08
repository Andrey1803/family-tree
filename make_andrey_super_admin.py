# -*- coding: utf-8 -*-
"""
Скрипт для предоставления прав СУПЕР-АДМИНА Андрею Емельянову.
Отправляет запрос на сервер Railway и предоставляет полные права.
"""

import json
import urllib.request
import urllib.error
import sys

# Включаем поддержку UTF-8 для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

def main():
    print("=" * 60)
    print("  Предоставление прав СУПЕР-АДМИНА")
    print("  Пользователь: Андрей Емельянов")
    print("=" * 60)

    # Шаг 1: Вход под супер-админом
    print("\n1. Вход под супер-админом (admin)...")

    admin_login = "admin"
    admin_password = "admin123"

    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": admin_login, "password": admin_password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')

            if not token:
                print(f"   [ERROR] {data.get('error', 'Неизвестная ошибка')}")
                return

            print(f"   [OK] Токен получен")

    except urllib.error.HTTPError as e:
        print(f"   [ERROR] HTTP {e.code}: Неверный логин или пароль")
        return
    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    # Шаг 2: Получение списка пользователей
    print("\n2. Получение списка пользователей...")

    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])

            # Ищем Андрея Емельянова
            andrey_user = None
            for user in users:
                if user.get('login') == 'Андрей Емельянов':
                    andrey_user = user
                    break

            if not andrey_user:
                print(f"   [ERROR] Пользователь 'Андрей Емельянов' не найден")
                print(f"   Доступные пользователи:")
                for u in users:
                    print(f"      - {u.get('login')} (admin: {u.get('is_admin', False)})")
                return

            user_id = andrey_user.get('id')
            is_admin = andrey_user.get('is_admin', False)

            print(f"   [OK] Найден пользователь:")
            print(f"      ID: {user_id}")
            print(f"      Логин: {andrey_user.get('login')}")
            print(f"      Email: {andrey_user.get('email', 'не указан')}")
            print(f"      Текущие права: {'👑 АДМИНИСТРАТОР' if is_admin else '❌ НЕТ ПРАВ'}")

            if is_admin:
                print(f"\n   ✅ У пользователя УЖЕ есть права АДМИНИСТРАТОРА!")
                print(f"   Перезапустите приложение и войдите в админ-панель.")
                return

    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    # Шаг 3: Предоставление прав администратора
    print("\n3. Предоставление прав СУПЕР-АДМИНА...")

    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/user/{user_id}/grant-admin",
            headers={'Authorization': f'Bearer {token}'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ {data.get('message', 'Права предоставлены')}")

    except urllib.error.HTTPError as e:
        print(f"   [ERROR] HTTP {e.code}")
        error_data = json.loads(e.read().decode()) if e.read else {}
        print(f"      {error_data.get('error', 'Неизвестная ошибка')}")
        return
    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    # Шаг 4: Проверка результата
    print("\n4. Проверка результата...")

    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])

            for user in users:
                if user.get('login') == 'Андрей Емельянов':
                    is_admin = user.get('is_admin', False)
                    status = '👑 АДМИНИСТРАТОР' if is_admin else '❌ НЕТ ПРАВ (ОШИБКА!)'
                    print(f"   [RESULT] Права администратора: {status}")
                    break

    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    print("\n" + "=" * 60)
    print("  ✅ ГОТОВО! Андрей Емельянов теперь СУПЕР-АДМИН")
    print("=" * 60)
    print("\nПерезапустите приложение и откройте:")
    print("  Меню Файл -> Админ-панель")
    print("\nТеперь доступны все права:")
    print("  • Просмотр всех пользователей")
    print("  • Управление правами доступа")
    print("  • Удаление пользователей")
    print("  • Сброс паролей")
    print("  • Просмотр статистики")
    print("  • Управление деревьями")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Прервано пользователем")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
