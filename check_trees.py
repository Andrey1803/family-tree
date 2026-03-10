# -*- coding: utf-8 -*-
"""
Проверка деревьев пользователей на сервере синхронизации.
1. Логин на сервере синхронизации как администратор (admin/admin123)
2. Получение всех пользователей
3. Проверка наличия дерева у каждого пользователя
4. Вывод результатов
"""

import json
import urllib.request
import urllib.error
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
ADMIN_LOGIN = "Андрей Емельянов"
ADMIN_PASSWORD = "18031981asdF"


def login_admin():
    print(f"Попытка входа на сервер {SYNC_URL}...")
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get("token")
            if token:
                print(f"Успешный вход как {ADMIN_LOGIN}")
                return token
            else:
                print(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Ошибка при входе: {e}")
        return None


def get_all_users(token):
    if not token:
        return []
    print("\nПолучение списка всех пользователей...")
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get("users", [])
            print(f"Найдено пользователей: {len(users)}")
            return users
    except Exception as e:
        print(f"Ошибка: {e}")
        return []


def check_user_tree(token, user_id, username):
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/tree/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return True, data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, None
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def main():
    print("=" * 60)
    print("ПРОВЕРКА ДЕРЕВЬЕВ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)
    
    token = login_admin()
    if not token:
        print("\nНе удалось войти. Завершение.")
        return
    
    users = get_all_users(token)
    if not users:
        print("\nНе удалось получить пользователей. Завершение.")
        return
    
    print("\n" + "=" * 60)
    print("ПРОВЕРКА НАЛИЧИЯ ДЕРЕВЬЕВ")
    print("=" * 60)
    
    users_with_trees = 0
    users_without_trees = 0
    
    for user in users:
        user_id = user.get("id") or user.get("user_id") or user.get("login")
        username = user.get("login") or user.get("email") or str(user_id)
        
        has_tree, tree_data = check_user_tree(token, user_id, username)
        
        if has_tree:
            status = "ЕСТЬ дерево"
            users_with_trees += 1
        elif has_tree is False:
            status = "НЕТ дерева"
            users_without_trees += 1
        else:
            status = f"Ошибка: {tree_data}"
        
        print(f"Пользователь: {username} (ID: {user_id}) - {status}")
    
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    print(f"Всего пользователей: {len(users)}")
    print(f"С деревьями: {users_with_trees}")
    print(f"Без деревьев: {users_without_trees}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
