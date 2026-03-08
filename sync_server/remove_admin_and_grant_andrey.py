# -*- coding: utf-8 -*-
"""
Скрипт для удаления пользователя 'admin' и предоставления прав супер-админа Андрею Емельянову.
Запускать локально или на Railway.
"""

import json
import urllib.request
import urllib.error
import os

SERVER_URL = "https://ravishing-caring-production-3656.up.railway.app"

def login(login, password):
    """Вход на сервер, получение токена."""
    req = urllib.request.Request(
        f"{SERVER_URL}/api/auth/login",
        data=json.dumps({"login": login, "password": password}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('token'), data.get('user_id')
    except urllib.error.HTTPError as e:
        print(f"Ошибка входа: {e.code}")
        return None, None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None


def get_users(token):
    """Получить список всех пользователей."""
    req = urllib.request.Request(
        f"{SERVER_URL}/api/admin/users",
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return None


def delete_user(token, user_id):
    """Удалить пользователя."""
    req = urllib.request.Request(
        f"{SERVER_URL}/api/admin/user/{user_id}",
        headers={'Authorization': f'Bearer {token}'},
        method='DELETE'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Ошибка удаления: {e.code}")
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


def grant_admin(token, user_id):
    """Предоставить права администратора."""
    req = urllib.request.Request(
        f"{SERVER_URL}/api/admin/user/{user_id}/grant-admin",
        headers={'Authorization': f'Bearer {token}'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Ошибка предоставления прав: {e.code}")
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Удаление 'admin' и предоставление прав Андрею Емельянову")
    print("=" * 60)
    
    # Вход под admin
    print("\nВход под admin...")
    token, admin_id = login("admin", "admin123")
    
    if not token:
        print("Не удалось войти под admin")
        print("Попробуйте: admin / admin123")
        exit(1)
    
    print(f"Успешный вход. Token: {token[:30]}...")
    
    # Получаем список пользователей
    print("\nПолучение списка пользователей...")
    users_data = get_users(token)
    
    if not users_data:
        print("Не удалось получить список пользователей")
        exit(1)
    
    # API возвращает {'users': [...]}
    if isinstance(users_data, dict) and 'users' in users_data:
        users = users_data['users']
    else:
        users = users_data
    
    print(f"Найдено пользователей: {len(users)}")
    
    # Ищем admin и Андрей Емельянов
    admin_user = None
    andrey_user = None
    
    # API может возвращать dict или list
    if isinstance(users, dict):
        users_list = list(users.values())
    elif isinstance(users, list):
        users_list = users
    else:
        print(f"Неизвестный формат пользователей: {type(users)}")
        exit(1)
    
    for user in users_list:
        if isinstance(user, dict):
            login_name = user.get('login', '')
            is_admin = user.get('is_admin', False)
            print(f"   - {login_name} (admin: {is_admin})")
            
            if login_name == "admin":
                admin_user = user
            elif login_name == "Андрей Емельянов":
                andrey_user = user
        elif isinstance(user, str):
            # Если возвращается просто логин
            print(f"   - {user}")
            if user == "admin":
                admin_user = {'login': user, 'id': user}
            elif user == "Андрей Емельянов":
                andrey_user = {'login': user, 'id': user}
    
    # Удаляем admin
    if admin_user:
        print(f"\nУдаление пользователя 'admin'...")
        result = delete_user(token, admin_user['id'])
        if result:
            print(f"User 'admin' удалён: {result}")
        else:
            print("Не удалось удалить 'admin'")
    else:
        print("\nПользователь 'admin' не найден")
    
    # Предоставляем права Андрею
    if andrey_user:
        if andrey_user.get('is_admin'):
            print(f"\nАндрей Емельянов уже администратор")
        else:
            print(f"\nПредоставление прав администратора Андрей Емельянов...")
            result = grant_admin(token, andrey_user['id'])
            if result:
                print(f"Права предоставлены: {result}")
            else:
                print("Не удалось предоставить права")
    else:
        print("\nПользователь Андрей Емельянов не найден")
        print("Сначала зарегистрируйтесь под этим логином")
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
