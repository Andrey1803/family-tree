# -*- coding: utf-8 -*-
"""Тест авторизации на сервере"""

import urllib.request
import json
import sys
import io

# Исправляем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

print("=" * 60)
print("ТЕСТ: Авторизация на сервере")
print("=" * 60)

# Тест 1: admin
print("\n1. Тест: admin / admin123")
try:
    data = json.dumps({"login": "admin", "password": "admin123"}).encode('utf-8')
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        token = result.get('token')
        if token:
            print(f"   [OK] УСПЕХ! Token: {token[:30]}...")
        else:
            print(f"   [ERR] Token не получен: {result}")
except Exception as e:
    print(f"   [ERR] Ошибка: {e}")

# Тест 2: Андрей Емельянов (проверка написания)
print("\n2. Тест: Андрей Емельянов / 18031981asdF")
try:
    data = json.dumps({"login": "Андрей Емельянов", "password": "18031981asdF"}).encode('utf-8')
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        token = result.get('token')
        if token:
            print(f"   [OK] УСПЕХ! Token: {token[:30]}...")
        else:
            print(f"   [ERR] Token не получен: {result}")
except urllib.error.HTTPError as e:
    print(f"   [ERR] HTTP {e.code}: {e.reason}")
except Exception as e:
    print(f"   [ERR] Ошибка: {e}")

# Тест 3: Получение статистики (с токеном admin)
print("\n3. Тест: Получение статистики")
try:
    # Сначала получаем токен admin
    data = json.dumps({"login": "admin", "password": "admin123"}).encode('utf-8')
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        admin_token = result.get('token')
        
        if admin_token:
            # Получаем статистику
            req = urllib.request.Request(
                f"{SYNC_URL}/api/admin/stats",
                headers={'Authorization': f'Bearer {admin_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                stats = json.loads(resp.read().decode())
                print(f"   [OK] Статистика получена!")
                overview = stats.get('overview', {})
                print(f"      Пользователей: {overview.get('total_users', 0)}")
                print(f"      Деревьев: {overview.get('total_trees', 0)}")
                print(f"      Персон: {overview.get('total_persons', 0)}")
                
                # Проверяем пользователей
                recent = stats.get('recent_users', [])
                print(f"\n   Пользователи ({len(recent)}):")
                for u in recent:
                    print(f"      - {u['login']}")
                    
except Exception as e:
    print(f"   [ERR] Ошибка: {e}")

print("\n" + "=" * 60)
print("Тест завершён!")
input("Нажмите Enter для выхода...")
