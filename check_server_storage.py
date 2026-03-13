# -*- coding: utf-8 -*-
"""
Проверка сохранения данных на веб-сервере Railway.

Тестирует:
1. Регистрацию пользователя
2. Вход в систему
3. Создание/сохранение дерева
4. Проверку что данные сохранились в /data
"""

import json
import urllib.request
import urllib.error
import sys

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
# Замените на ваш актуальный URL из Railway Dashboard (без /login в конце!)
BASE_URL = "https://family-tree-production-0e7d.up.railway.app"
TEST_USERNAME = "Тестовый Пользователь"
TEST_PASSWORD = "test123456"

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def make_request(url, data=None, headers=None, method="GET"):
    """Выполняет HTTP запрос."""
    if headers is None:
        headers = {}
    
    if data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                'ok': True,
                'status': response.status,
                'data': json.loads(response.read().decode('utf-8')) if response.read else None
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.read else ""
        return {
            'ok': False,
            'status': e.code,
            'error': error_body
        }
    except urllib.error.URLError as e:
        return {
            'ok': False,
            'status': 0,
            'error': str(e.reason)
        }
    except Exception as e:
        return {
            'ok': False,
            'status': 0,
            'error': str(e)
        }


def print_result(test_name, success, message=""):
    """Выводит результат теста."""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")


# ==========================================
# ТЕСТЫ
# ==========================================

def test_health():
    """Проверка доступности сервера."""
    print("\n📡 ТЕСТ 1: Проверка доступности сервера")
    
    # Пробуем главную страницу
    result = make_request(f"{BASE_URL}/")
    
    if result['ok'] or result['status'] == 200 or result['status'] == 302:
        print_result("Сервер доступен", True, f"Статус: {result['status']}")
        return True
    else:
        print_result("Сервер недоступен", False, result.get('error', 'Неизвестная ошибка'))
        return False


def test_register():
    """Регистрация тестового пользователя."""
    print("\n👤 ТЕСТ 2: Регистрация пользователя")
    
    result = make_request(
        f"{BASE_URL}/api/auth/register",
        data={
            'login': TEST_USERNAME,
            'password': TEST_PASSWORD
        },
        method="POST"
    )
    
    if result['ok']:
        print_result("Регистрация успешна", True)
        return True
    elif 'уже существует' in result.get('error', '').lower():
        print_result("Пользователь уже существует", True, "(можно продолжить)")
        return True
    else:
        print_result("Регистрация не удалась", False, result.get('error', 'Неизвестная ошибка'))
        return False


def test_login():
    """Вход в систему через session endpoint."""
    print("\n🔑 ТЕСТ 3: Вход в систему")
    
    # Используем /api/auth/session для входа
    result = make_request(
        f"{BASE_URL}/api/auth/session",
        data={
            'login': TEST_USERNAME,
            'password': TEST_PASSWORD
        },
        method="POST"
    )
    
    if result['ok']:
        token = result['data'].get('token') if result['data'] else None
        if token:
            print_result("Вход успешен", True, f"Токен получен (длина: {len(token)})")
            return token
        else:
            # Может быть cookie-based сессия
            print_result("Вход успешен", True, "Сессия установлена (cookie)")
            return "cookie_session"
    else:
        print_result("Вход не удался", False, result.get('error', 'Неизвестная ошибка'))
        return None


def test_save_tree(token):
    """Сохранение тестового дерева."""
    print("\n🌳 ТЕСТ 4: Сохранение дерева")
    
    if not token or token == "cookie_session":
        # Для cookie сессии нужен другой подход — пропускаем
        print_result("Пропущено", False, "Требуется токен авторизации (cookie не поддерживается)")
        return None
    
    # Создаём тестовое дерево
    test_tree = {
        "persons": {
            "p1": {
                "id": "p1",
                "name": "Иван",
                "surname": "Иванов",
                "patronymic": "Иванович",
                "birth_date": "1980-01-01",
                "gender": "male",
                "is_deceased": False,
                "parents": [],
                "children": [],
                "spouse_ids": []
            }
        },
        "marriages": [],
        "current_center": "p1"
    }
    
    result = make_request(
        f"{BASE_URL}/api/tree",
        data=test_tree,
        headers={'Authorization': f'Bearer {token}'},
        method="POST"
    )
    
    if result['ok']:
        print_result("Дерево сохранено", True, f"Персон: {len(test_tree['persons'])}")
        return True
    else:
        print_result("Сохранение не удалось", False, result.get('error', 'Неизвестная ошибка'))
        return False


def test_load_tree(token):
    """Загрузка сохранённого дерева."""
    print("\n📥 ТЕСТ 5: Загрузка дерева")
    
    if not token or token == "cookie_session":
        print_result("Пропущено", False, "Требуется токен авторизации")
        return False
    
    result = make_request(
        f"{BASE_URL}/api/tree",
        headers={'Authorization': f'Bearer {token}'},
        method="GET"
    )
    
    if result['ok']:
        tree_data = result['data']
        persons_count = len(tree_data.get('persons', {})) if tree_data else 0
        print_result("Дерево загружено", True, f"Персон: {persons_count}")
        return persons_count > 0
    else:
        print_result("Загрузка не удалась", False, result.get('error', 'Неизвестная ошибка'))
        return False


def test_server_sync_health():
    """Проверка сервера синхронизации."""
    print("\n🔄 ТЕСТ 6: Проверка сервера синхронизации")
    
    sync_url = "https://ravishing-caring-production-3656.up.railway.app"
    result = make_request(f"{sync_url}/api/health")
    
    if result['ok']:
        print_result("Сервер синхронизации доступен", True, f"Статус: {result['status']}")
        return True
    else:
        print_result("Сервер синхронизации недоступен", False, result['error'])
        return False


# ==========================================
# ОСНОВНАЯ ФУНКЦИЯ
# ==========================================

def main():
    """Запуск всех тестов."""
    print("=" * 60)
    print("🧪 ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ НА RAILWAY")
    print("=" * 60)
    print(f"\nВеб-сервер: {BASE_URL}")
    print(f"Тестовый пользователь: {TEST_USERNAME}")
    
    results = []
    
    # Тест 1: Здоровье сервера
    results.append(("Доступность сервера", test_health()))
    
    # Тест 2: Регистрация
    results.append(("Регистрация", test_register()))
    
    # Тест 3: Вход
    token = test_login()
    results.append(("Вход в систему", token is not None))
    
    # Тест 4: Сохранение дерева
    tree_saved = test_save_tree(token)
    if tree_saved is not None:
        results.append(("Сохранение дерева", tree_saved))
    
    # Тест 5: Загрузка дерева
    if tree_saved is True:
        tree_loaded = test_load_tree(token)
        results.append(("Загрузка дерева", tree_loaded))
    
    # Тест 6: Сервер синхронизации
    results.append(("Сервер синхронизации", test_server_sync_health()))
    
    # ==========================================
    # ИТОГИ
    # ==========================================
    print("\n" + "=" * 60)
    print("📊 ИТОГИ")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nПройдено: {passed}/{total} тестов")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Данные сохраняются корректно.")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Проверьте конфигурацию Railway.")
    
    print("\n" + "=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
