# -*- coding: utf-8 -*-
"""Полная проверка входа и сохранения дерева"""

import json
import urllib.request
import http.cookiejar

BASE_URL = "https://family-tree-production-0e7d.up.railway.app"

# Создаем хранилище кук
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def request(url, data=None, method='GET'):
    """Выполняет запрос с сохранением кук"""
    if data:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, timeout=10) as resp:
            return {
                'status': resp.status,
                'data': json.loads(resp.read().decode('utf-8')) if resp.read else None,
                'cookies': list(cookie_jar)
            }
    except urllib.error.HTTPError as e:
        return {
            'status': e.code,
            'data': json.loads(e.read().decode('utf-8')) if e.read else str(e),
            'error': True
        }
    except Exception as e:
        return {'status': 0, 'data': str(e), 'error': True}

print("=" * 60)
print("ПРОВЕРКА ВХОДА И СОХРАНЕНИЯ ДЕРЕВА")
print("=" * 60)

# Шаг 1: Локальный вход
print("\n1️⃣  Локальный вход:")
result = request(f"{BASE_URL}/api/auth/login-local", 
                 {"login": "Тестовый Пользователь", "password": "test123456"}, 
                 'POST')
print(f"   Статус: {result['status']}")
print(f"   Ответ: {result['data']}")
print(f"   Куки: {len(result['cookies'])} шт.")

# Шаг 2: Проверка сессии
print("\n2️⃣  Проверка сессии:")
result = request(f"{BASE_URL}/api/check-session")
print(f"   Статус: {result['status']}")
print(f"   Ответ: {result['data']}")

# Шаг 3: Сохранение дерева
print("\n3️⃣  Сохранение дерева:")
test_tree = {
    "persons": {"p1": {"id": "p1", "name": "Тест", "surname": "Тестов"}},
    "marriages": [],
    "current_center": "p1"
}
result = request(f"{BASE_URL}/api/tree", test_tree, 'POST')
print(f"   Статус: {result['status']}")
print(f"   Ответ: {result['data']}")

# Шаг 4: Загрузка дерева
print("\n4️⃣  Загрузка дерева:")
result = request(f"{BASE_URL}/api/tree")
print(f"   Статус: {result['status']}")
print(f"   Ответ: {result['data']}")

print("\n" + "=" * 60)
print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)
