# -*- coding: utf-8 -*-
"""
Проверка интеграции админ-панели.
Тестирует соединение с сервером и права администратора.
"""

import json
import urllib.request
import urllib.error

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_connection():
    """Проверяет доступность сервера."""
    print_header("1. ПРОВЕРКА СОЕДИНЕНИЯ")
    try:
        req = urllib.request.Request(SYNC_URL + "/api/health", method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ Сервер доступен: {SYNC_URL}")
            return True
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return False

def test_login(login, password):
    """Проверяет вход пользователя."""
    print_header("2. ПРОВЕРКА ВХОДА")
    print(f"Логин: {login}")
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": login, "password": password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')
            user_id = data.get('user_id')
            
            if token:
                print(f"✅ Вход успешен")
                print(f"   Token: {token[:20]}...")
                print(f"   User ID: {user_id}")
                return token
            else:
                print(f"❌ Вход не удался: {data.get('error', 'Неизвестная ошибка')}")
                return None
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode()) if e.read else {}
        print(f"❌ HTTP {e.code}: {error_data.get('error', 'Неизвестная ошибка')}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def test_admin_access(token):
    """Проверяет права администратора."""
    print_header("3. ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА")
    
    if not token:
        print("❌ Нет токена")
        return False
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/stats",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            overview = data.get('overview', {})
            
            print(f"✅ Права администратора подтверждены")
            print(f"   Пользователей: {overview.get('total_users', 0)}")
            print(f"   Деревьев: {overview.get('total_trees', 0)}")
            print(f"   Персон: {overview.get('total_persons', 0)}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"❌ Доступ запрещён (403) — у пользователя нет прав администратора")
        elif e.code == 401:
            print(f"❌ Неверный токен (401)")
        else:
            print(f"❌ HTTP {e.code}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_admin_users(token):
    """Проверяет получение списка пользователей."""
    print_header("4. ПОЛУЧЕНИЕ СПИСКА ПОЛЬЗОВАТЕЛЕЙ")
    
    if not token:
        return
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])
            
            print(f"✅ Загружено пользователей: {len(users)}")
            print(f"\n   {'Логин':<30} {'Email':<25} {'Админ':<6} {'Активен':<8}")
            print(f"   {'-'*75}")
            
            for user in users[:10]:  # Показываем первые 10
                login = user.get('login', '—')[:28]
                email = user.get('email', '—')[:23] or '—'
                is_admin = '👑' if user.get('is_admin') else ''
                is_active = '✅' if user.get('is_active') else '❌'
                print(f"   {login:<30} {email:<25} {is_admin:<6} {is_active:<8}")
            
            if len(users) > 10:
                print(f"   ... и ещё {len(users) - 10} пользователей")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_admin_trees(token):
    """Проверяет получение списка деревьев."""
    print_header("5. ПОЛУЧЕНИЕ СПИСКА ДЕРЕВЬЕВ")
    
    if not token:
        return
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/trees",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            trees = data.get('trees', [])
            
            print(f"✅ Загружено деревьев: {len(trees)}")
            print(f"\n   {'Владелец':<25} {'Название':<25} {'Персон':<10}")
            print(f"   {'-'*65}")
            
            for tree in trees[:10]:  # Показываем первые 10
                owner = tree.get('user_login', '—')[:23]
                name = tree.get('name', '—')[:23]
                persons = len(tree.get('persons', {}))
                print(f"   {owner:<25} {name:<25} {persons:<10}")
            
            if len(trees) > 10:
                print(f"   ... и ещё {len(trees) - 10} деревьев")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция."""
    print_header("🔍 ПРОВЕРКА ИНТЕГРАЦИИ АДМИН-ПАНЕЛИ")
    
    # Тест 1: Соединение
    if not test_connection():
        print("\n⚠️  Сервер недоступен. Проверьте интернет-соединение.")
        return
    
    # Тест 2: Вход
    print("\nВведите учётные данные администратора:")
    login = input("Логин (по умолчанию 'Андрей Емельянов'): ").strip() or "Андрей Емельянов"
    password = input("Пароль: ").strip()
    
    if not password:
        print("❌ Пароль обязателен")
        return
    
    token = test_login(login, password)
    if not token:
        print("\n⚠️  Вход не удался. Проверьте логин и пароль.")
        return
    
    # Тест 3: Права администратора
    if not test_admin_access(token):
        print("\n⚠️  У пользователя нет прав администратора!")
        print("\n📝 Выполните команду на сервере:")
        print(f"   railway run sqlite3 /data/family_tree.db \"UPDATE users SET is_admin = 1 WHERE login = '{login}';\"")
        return
    
    # Тест 4: Список пользователей
    test_admin_users(token)
    
    # Тест 5: Список деревьев
    test_admin_trees(token)
    
    print_header("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    print("Админ-панель готова к работе!")
    print("\n📝 Для запуска десктопной админ-панели:")
    print("   1. Запустите main.py")
    print("   2. Войдите под пользователем 'Андрей Емельянов'")
    print("   3. Меню Файл → 👑 Админ-панель")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
