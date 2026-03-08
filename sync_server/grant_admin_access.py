# -*- coding: utf-8 -*-
"""
Скрипт для проверки и предоставления прав администратора пользователю "Андрей Емельянов"
на сервере синхронизации Railway.

Использование:
1. Войдите под admin/admin123 на сервере
2. Получите токен
3. Выполните этот скрипт
"""

import json
import urllib.request
import urllib.error

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
        print(f"Ошибка входа: {e.code} - {e.read().decode()}")
        return None, None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None


def get_users(token):
    """Получить список всех пользователей (только для админа)."""
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


def grant_admin(token, user_id):
    """Предоставить права администратора пользователю."""
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
        try:
            print(e.read().decode())
        except:
            pass
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


if __name__ == "__main__":
    print("🔐 Вход под admin...")
    token, user_id = login("admin", "admin123")
    
    if not token:
        print("❌ Не удалось войти под admin. Проверьте учётные данные.")
        print("   По умолчанию: admin / admin123")
        exit(1)
    
    print(f"✅ Успешный вход. Token: {token[:20]}...")
    
    print("\n📋 Получение списка пользователей...")
    users = get_users(token)
    
    if users:
        print(f"   Найдено пользователей: {len(users)}")
        
        # Ищем "Андрей Емельянов"
        andrey_user = None
        for user in users:
            login_name = user.get('login', '')
            print(f"   - {login_name} (admin: {user.get('is_admin', False)})")
            if login_name == "Андрей Емельянов":
                andrey_user = user
        
        if andrey_user:
            if andrey_user.get('is_admin'):
                print(f"\n✅ Пользователь '{andrey_user['login']}' уже является администратором.")
            else:
                print(f"\n⚙️ Предоставление прав администратора пользователю '{andrey_user['login']}'...")
                result = grant_admin(token, andrey_user['id'])
                if result:
                    print(f"✅ Права предоставлены: {result}")
                else:
                    print("❌ Не удалось предоставить права.")
                    print("   Возможно, на сервере нет эндпоинта /api/admin/user/{id}/grant-admin")
        else:
            print("\n⚠️ Пользователь 'Андрей Емельянов' не найден на сервере.")
            print("   Вам нужно зарегистрироваться на сервере под этим логином.")
    else:
        print("❌ Не удалось получить список пользователей.")
