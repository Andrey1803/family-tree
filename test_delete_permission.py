# -*- coding: utf-8 -*-
"""
Проверка прав удаления пользователей.
"""

import json
import urllib.request
import sys

# Включаем поддержку UTF-8 для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"


def login(login_val, password):
    """Вход в систему."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": login_val, "password": password}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        return data.get('token'), data.get('user_id'), data.get('error')


def get_users(token):
    """Получить список пользователей."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/admin/users",
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        return data.get('users', [])


def test_delete_permission(token, user_id, test_user_id):
    """Проверка права удаления."""
    print(f"\n3. Проверка права удаления пользователя {test_user_id}...")
    
    # Пробуем DELETE (desktop-стиль)
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/user/{test_user_id}",
            headers={'Authorization': f'Bearer {token}'},
            method='DELETE'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ DELETE /api/admin/user/{test_user_id} работает")
            print(f"      Ответ: {data.get('message', 'OK')}")
            return True
    except urllib.error.HTTPError as e:
        error_msg = f'HTTP {e.code}'
        try:
            error_body = e.read().decode()
            if error_body:
                error_data = json.loads(error_body)
                error_msg = error_data.get('error', error_msg)
        except:
            pass
        print(f"   ❌ DELETE /api/admin/user/{test_user_id}: {error_msg}")
        
        if e.code == 403:
            print(f"      [!] ОШИБКА ПРАВ ДОСТУПА (403 Forbidden)")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_delete_with_full_url(token, test_user_id):
    """Проверка удаления с полным URL."""
    print(f"\n4. Проверка удаления с полным URL (/delete)...")
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/user/{test_user_id}/delete",
            headers={'Authorization': f'Bearer {token}'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ POST /api/admin/user/{test_user_id}/delete работает")
            print(f"      Ответ: {data.get('message', 'OK')}")
            return True
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode()) if e.read else {}
        error_msg = error_data.get('error', f'HTTP {e.code}')
        print(f"   ❌ POST /api/admin/user/{test_user_id}/delete: {error_msg}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def main():
    print("=" * 70)
    print("  ПРОВЕРКА ПРАВ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 70)
    
    # Вход под Андреем Емельяновым
    print("\n1. Вход под Андреем Емельяновым...")
    token, user_id, error = login("Андрей Емельянов", "18031981asdF")
    
    if error:
        print(f"   ❌ Ошибка входа: {error}")
        return
    
    if not token:
        print(f"   ❌ Не удалось получить токен")
        return
    
    print(f"   ✅ Вход успешен!")
    print(f"      User ID: {user_id}")
    print(f"      Token: {token[:30]}...")
    
    # Получение списка пользователей
    print("\n2. Получение списка пользователей...")
    users = get_users(token)
    print(f"   ✅ Найдено пользователей: {len(users)}")
    
    # Находим тестового пользователя (не admin и не Андрей)
    test_user = None
    for user in users:
        login_name = user.get('login', '')
        if login_name not in ['admin', 'Андрей Емельянов']:
            test_user = user
            break
    
    if not test_user:
        print(f"   ⚠️  Нет тестовых пользователей для удаления")
        print(f"   В системе только admin и Андрей Емельянов")
        return
    
    test_user_id = test_user.get('id')
    test_user_login = test_user.get('login')
    print(f"\n   Тестовый пользователь: {test_user_login} (ID: {test_user_id})")
    
    # Проверка права удаления
    delete_works = test_delete_permission(token, user_id, test_user_id)
    
    # Проверка с полным URL
    test_delete_with_full_url(token, test_user_id)
    
    # Итог
    print("\n" + "=" * 70)
    print("  РЕЗУЛЬТАТ ПРОВЕРКИ")
    print("=" * 70)
    
    if delete_works:
        print("\n✅ УДАЛЕНИЕ РАБОТАЕТ!")
        print("\nАндрей Емельянов может удалять пользователей через:")
        print("   • DELETE /api/admin/user/{id} (desktop-версия)")
        print("   • POST /api/admin/user/{id}/delete (web-версия)")
    else:
        print("\n❌ УДАЛЕНИЕ НЕ РАБОТАЕТ!")
        print("\nВозможные причины:")
        print("   1. Сервер на Railway ещё не обновился")
        print("   2. Проблема с декоратором @require_admin")
        print("   3. Неправильно определяется логин пользователя")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
