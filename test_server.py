# -*- coding: utf-8 -*-
"""Проверка подключения к серверу и данных"""

import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

# 1. Получаем токен
print("1. Получение токена...")
req = urllib.request.Request(
    f"{SYNC_URL}/api/auth/login",
    data=json.dumps({"login": "Андрей Емельянов", "password": "admin123"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        token = result.get('token')
        if token:
            print(f"   ✅ Токен получен: {token[:30]}...")
        else:
            print(f"   ❌ Токен не получен: {result}")
            input("Нажмите Enter для выхода...")
            exit()
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    input("Нажмите Enter для выхода...")
    exit()

# 2. Получаем статистику
print("\n2. Получение статистики...")
req = urllib.request.Request(
    f"{SYNC_URL}/api/admin/stats",
    headers={'Authorization': f'Bearer {token}'},
    method='GET'
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        stats = json.loads(response.read().decode())
        print(f"   ✅ Статистика:")
        print(f"      Пользователей: {stats.get('overview', {}).get('total_users', 0)}")
        print(f"      Деревьев: {stats.get('overview', {}).get('total_trees', 0)}")
        print(f"      Персон: {stats.get('overview', {}).get('total_persons', 0)}")
        
        # Пользователи
        recent_users = stats.get('recent_users', [])
        print(f"\n   Пользователи ({len(recent_users)}):")
        for u in recent_users:
            print(f"      - {u['login']} (создан: {u['created_at']})")
            
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n✅ Тест завершён!")
input("Нажмите Enter для выхода...")
