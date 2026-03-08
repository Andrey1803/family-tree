# -*- coding: utf-8 -*-
"""
Проверка состояния сервера синхронизации и пользователей.
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


def check_server():
    """Проверка доступности сервера."""
    print("=" * 60)
    print("  ПРОВЕРКА СЕРВЕРА СИНХРОНИЗАЦИИ")
    print("=" * 60)
    print(f"\nURL: {SYNC_URL}\n")
    
    # Проверка корня
    print("1. Проверка корня сервера (/):")
    try:
        req = urllib.request.Request(f"{SYNC_URL}/", method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"   ✅ Сервер отвечает (HTTP {response.status})")
    except urllib.error.HTTPError as e:
        print(f"   ⚠️  HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Проверка API health
    print("\n2. Проверка API (/api/health):")
    try:
        req = urllib.request.Request(f"{SYNC_URL}/api/health", method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ Health OK: {data}")
    except Exception as e:
        print(f"   ⚠️  Health недоступен: {e}")
    
    # Проверка регистрации
    print("\n3. Проверка API регистрации (/api/auth/register):")
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/register",
            data=json.dumps({"login": "test_user_check", "password": "test123456", "email": "test@test.com"}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ Регистрация работает: {data.get('message', 'OK')}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"   ℹ️  Тестовый пользователь уже существует (сервер работает)")
        else:
            print(f"   ⚠️  HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Проверка входа под admin
    print("\n4. Проверка входа под admin:")
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": "admin", "password": "admin123"}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')
            if token:
                print(f"   ✅ Вход под admin успешен (token: {token[:20]}...)")
                return token
            else:
                print(f"   ❌ Ошибка: {data.get('error', 'Неизвестная ошибка')}")
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    return None


def check_users(token):
    """Проверка списка пользователей."""
    if not token:
        print("\n⚠️  Нет токена для проверки пользователей")
        return
    
    print("\n5. Проверка списка пользователей (/api/admin/users):")
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])
            print(f"   ✅ Найдено пользователей: {len(users)}")
            
            print("\n   Список пользователей:")
            for user in users:
                login = user.get('login', 'unknown')
                email = user.get('email', '-')
                is_admin = user.get('is_admin', False)
                created = user.get('created_at', '-')
                admin_mark = "👑" if is_admin else ""
                print(f"      {admin_mark} {login} ({email}) [создан: {created}]")
            
            # Проверка Андрея Емельянова
            andrey_user = next((u for u in users if u.get('login') == 'Андрей Емельянов'), None)
            if andrey_user:
                print(f"\n   ✅ Андрей Емельянов найден!")
                print(f"      ID: {andrey_user.get('id')}")
                print(f"      Email: {andrey_user.get('email')}")
                print(f"      Admin: {andrey_user.get('is_admin')}")
            else:
                print(f"\n   ⚠️  Андрей Емельянов НЕ найден в списке пользователей")
                
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


def test_andrey_login():
    """Проверка входа под Андреем Емельяновым."""
    print("\n6. Проверка входа под 'Андрей Емельянов':")
    
    passwords_to_try = ["andrey123", "18031981asdF", "andrey"]
    
    for password in passwords_to_try:
        try:
            req = urllib.request.Request(
                f"{SYNC_URL}/api/auth/login",
                data=json.dumps({"login": "Андрей Емельянов", "password": password}).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                token = data.get('token')
                if token:
                    print(f"   ✅ Вход успешен с паролем '{password}' (token: {token[:20]}...)")
                    return True
        except urllib.error.HTTPError:
            print(f"   ❌ Пароль '{password}': неверный")
        except Exception as e:
            print(f"   ❌ Пароль '{password}': ошибка {e}")
    
    return False


if __name__ == "__main__":
    try:
        token = check_server()
        
        if token:
            check_users(token)
        
        test_andrey_login()
        
        print("\n" + "=" * 60)
        print("  ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
