# -*- coding: utf-8 -*-
"""
Тест синхронизации между веб-версией и оконной версией.
Проверяет:
1. Вход под пользователем
2. Загрузка дерева с сервера
3. Выгрузка дерева на сервер
4. Проверка целостности данных
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

# Включаем поддержку UTF-8 для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

# Тестовые пользователи
TEST_USERS = [
    {"login": "admin", "password": "admin123", "name": "Админ"},
    {"login": "Андрей Емельянов", "password": "andrey123", "name": "Андрей Емельянов"},
]


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, text):
    print(f"\n[ШАГ {step_num}] {text}")


def login(login_val, password):
    """Вход в систему."""
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": login_val, "password": password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')
            user_id = data.get('user_id')
            
            if token:
                print(f"   ✅ Вход успешен (user_id: {user_id})")
                return token, user_id
            else:
                print(f"   ❌ Ошибка: {data.get('error', 'Неизвестная ошибка')}")
                return None, None
                
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP {e.code}: {e.reason}")
        return None, None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None, None


def download_tree(token):
    """Скачать дерево с сервера."""
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/download",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            tree = data.get('tree', {})
            persons = tree.get('persons', {})
            marriages = tree.get('marriages', [])
            
            print(f"   ✅ Дерево загружено: {len(persons)} персон, {len(marriages)} браков")
            return tree
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"   ⚠️  Дерево не найдено (пустое)")
            return {'persons': {}, 'marriages': []}
        print(f"   ❌ HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def upload_tree(token, tree_data, tree_name="Тестовое дерево"):
    """Загрузить дерево на сервер."""
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/upload",
            data=json.dumps({
                'tree': tree_data,
                'tree_name': tree_name
            }).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   ✅ Дерево загружено на сервер")
            return data
            
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def create_test_tree():
    """Создать тестовое дерево."""
    tree = {
        'persons': {
            '1': {
                'id': '1',
                'name': 'Иван',
                'surname': 'Иванов',
                'patronymic': 'Иванович',
                'birth_date': '1950-01-01',
                'gender': 'male',
                'is_deceased': False,
                'parents': [],
                'children': ['2'],
                'spouse_ids': ['3']
            },
            '2': {
                'id': '2',
                'name': 'Петр',
                'surname': 'Иванов',
                'patronymic': 'Иванович',
                'birth_date': '1975-05-15',
                'gender': 'male',
                'is_deceased': False,
                'parents': ['1'],
                'children': [],
                'spouse_ids': []
            },
            '3': {
                'id': '3',
                'name': 'Мария',
                'surname': 'Иванова',
                'patronymic': 'Петровна',
                'birth_date': '1955-03-20',
                'gender': 'female',
                'is_deceased': False,
                'parents': [],
                'children': ['2'],
                'spouse_ids': ['1']
            }
        },
        'marriages': [
            {'persons': ['1', '3'], 'date': '1974-06-01'}
        ]
    }
    return tree


def verify_tree(tree1, tree2, name1="Локальное", name2="Сервер"):
    """Сравнить два дерева."""
    if not tree1 or not tree2:
        print(f"   ❌ Одно из деревьев пустое")
        return False
    
    persons1 = tree1.get('persons', {})
    persons2 = tree2.get('persons', {})
    marriages1 = tree1.get('marriages', [])
    marriages2 = tree2.get('marriages', [])
    
    # Сравниваем количество персон
    if len(persons1) != len(persons2):
        print(f"   ❌ Разное количество персон: {name1}={len(persons1)}, {name2}={len(persons2)}")
        return False
    
    # Сравниваем количество браков
    if len(marriages1) != len(marriages2):
        print(f"   ❌ Разное количество браков: {name1}={len(marriages1)}, {name2}={len(marriages2)}")
        return False
    
    # Сравниваем данные персон
    for pid, p1 in persons1.items():
        if pid not in persons2:
            print(f"   ❌ Персона {pid} не найдена в {name2}")
            return False
        
        p2 = persons2[pid]
        for key in ['name', 'surname', 'birth_date', 'gender']:
            if p1.get(key) != p2.get(key):
                print(f"   ❌ Персона {pid}: различие в {key}: {name1}={p1.get(key)}, {name2}={p2.get(key)}")
                return False
    
    print(f"   ✅ Деревья идентичны ({len(persons1)} персон, {len(marriages1)} браков)")
    return True


def test_user_sync(user):
    """Протестировать синхронизацию для пользователя."""
    print_header(f"Тест синхронизации: {user['name']}")
    
    # Шаг 1: Вход
    print_step(1, "Вход в систему")
    token, user_id = login(user['login'], user['password'])
    
    if not token:
        print("   ❌ Не удалось войти. Пропускаем тест.")
        return False
    
    # Шаг 2: Проверка существующего дерева
    print_step(2, "Загрузка текущего дерева с сервера")
    existing_tree = download_tree(token)
    
    if existing_tree:
        persons_count = len(existing_tree.get('persons', {}))
        if persons_count > 0:
            print(f"   ℹ️  Найдено существующее дерево ({persons_count} персон)")
        else:
            print(f"   ℹ️  Дерево пустое")
    
    # Шаг 3: Создание тестового дерева
    print_step(3, "Создание тестового дерева")
    test_tree = create_test_tree()
    print(f"   ✅ Создано дерево: {len(test_tree['persons'])} персон, {len(test_tree['marriages'])} браков")
    
    # Шаг 4: Загрузка на сервер
    print_step(4, "Загрузка тестового дерева на сервер")
    upload_result = upload_tree(token, test_tree, "Тестовое дерево синхронизации")
    
    if not upload_result:
        print("   ❌ Не удалось загрузить дерево")
        return False
    
    # Шаг 5: Скачивание и проверка
    print_step(5, "Скачивание дерева для проверки")
    downloaded_tree = download_tree(token)
    
    if not downloaded_tree:
        print("   ❌ Не удалось скачать дерево")
        return False
    
    # Шаг 6: Сравнение
    print_step(6, "Сравнение загруженного и скачанного дерева")
    if not verify_tree(test_tree, downloaded_tree, "Исходное", "Скачанное"):
        return False
    
    # Шаг 7: Восстановление оригинального дерева (если было)
    if existing_tree and len(existing_tree.get('persons', {})) > 0:
        print_step(7, "Восстановление оригинального дерева")
        upload_tree(token, existing_tree, "Восстановленное дерево")
        restored_tree = download_tree(token)
        verify_tree(existing_tree, restored_tree, "Оригинал", "Восстановленное")
    
    print_header("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    return True


def test_web_to_desktop_sync():
    """Тест синхронизации между веб и desktop."""
    print_header("Тест синхронизации: ВЕБ ↔ ОКОННАЯ ВЕРСИЯ")
    
    print("\n📋 Проверка конфигурации:")
    print(f"   URL сервера: {SYNC_URL}")
    print(f"   Тестовых пользователей: {len(TEST_USERS)}")
    
    # Проверяем доступность сервера
    print("\n📋 Проверка доступности сервера:")
    try:
        req = urllib.request.Request(f"{SYNC_URL}/api/health", method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            print("   ✅ Сервер доступен")
    except:
        # Пробуем корень
        try:
            req = urllib.request.Request(f"{SYNC_URL}/", method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                print("   ✅ Сервер доступен (корень)")
        except Exception as e:
            print(f"   ⚠️  Сервер может быть недоступен: {e}")
    
    # Тестируем каждого пользователя
    results = []
    for user in TEST_USERS:
        result = test_user_sync(user)
        results.append((user['name'], result))
    
    # Итоговый отчёт
    print_header("ИТОГОВЫЙ ОТЧЁТ")
    for name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {name}: {status}")
    
    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
    
    return all_passed


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("  ТЕСТ СИНХРОНИЗАЦИИ")
        print("  Веб-версия ↔ Оконная версия ↔ Сервер")
        print("=" * 60)
        print(f"\nДата теста: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"Сервер: {SYNC_URL}")
        
        success = test_web_to_desktop_sync()
        
        print("\n" + "=" * 60)
        if success:
            print("  ✅ СИНХРОНИЗАЦИЯ РАБОТАЕТ КОРРЕКТНО")
        else:
            print("  ⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ С СИНХРОНИЗАЦИЕЙ")
        print("=" * 60)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
