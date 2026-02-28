# -*- coding: utf-8 -*-
"""
Скрипт назначения пользователя admin администратором на сервере Railway.
"""

import urllib.request
import json

# URL сервера синхронизации
SYNC_SERVER_URL = "https://ravishing-caring-production-3656.up.railway.app"

# Данные администратора (измените на ваши)
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin123"

print("=== НАЗНАЧЕНИЕ ADMIN АДМИНИСТРАТОРОМ ===\n")

# Шаг 1: Вход на сервер
print(f"[1] Вход на сервер как {ADMIN_LOGIN}...")
try:
    req = urllib.request.Request(
        f"{SYNC_SERVER_URL}/api/auth/login",
        data=json.dumps({"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        token = data.get('token')
        user_id = data.get('user_id')
        
        if token:
            print(f"    ✓ Token получен: {token[:30]}...")
            print(f"    ✓ User ID: {user_id}")
        else:
            print(f"    ✗ Ошибка: {data}")
            exit(1)
            
except Exception as e:
    print(f"    ✗ Ошибка входа: {e}")
    exit(1)

# Шаг 2: Проверка текущего статуса
print(f"\n[2] Проверка текущего статуса...")
try:
    req = urllib.request.Request(
        f"{SYNC_SERVER_URL}/api/admin/stats",
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        print(f"    ✓ У вас УЖЕ есть права администратора!")
        print(f"    Пользователей: {data.get('overview', {}).get('total_users', 0)}")
        print(f"    Деревьев: {data.get('overview', {}).get('total_trees', 0)}")
        exit(0)
        
except urllib.error.HTTPError as e:
    if e.code == 403:
        print(f"    ✗ Нет прав администратора (HTTP 403)")
    else:
        print(f"    ✗ Ошибка: HTTP {e.code}")
except Exception as e:
    print(f"    ✗ Ошибка: {e}")

# Шаг 3: Попытка получения прав через API
print(f"\n[3] Попытка получения прав администратора...")
print("    Примечание: Это можно сделать только через БД сервера")
print("    Обратитесь к документации или используйте SQL запрос:")
print()
print(f"    UPDATE users SET is_admin = 1 WHERE login = 'admin';")
print()

# Шаг 4: Проверка через users.json локально
print(f"\n[4] Проверка локального файла users.json...")
import os
import json as json_module

users_file = "users.json"
if os.path.exists(users_file):
    with open(users_file, 'r', encoding='utf-8') as f:
        users_data = json_module.load(f)
    
    admin_data = users_data.get('users', {}).get('admin', {})
    
    if isinstance(admin_data, dict) and admin_data.get('is_admin'):
        print(f"    ✓ В users.json у admin есть флаг is_admin")
    else:
        print(f"    ✗ В users.json у admin НЕТ флага is_admin")
        print(f"    Хотите добавить? (y/n): ", end='')
        
        # Не используем input, так как это может не работать в некоторых средах
        # Просто покажем инструкцию
        print()
        print()
        print("    Для добавления выполните вручную:")
        print()
        print("    import json")
        print("    with open('users.json', 'r+', encoding='utf-8') as f:")
        print("        data = json.load(f)")
        print("        if 'users' not in data: data['users'] = {}")
        print("        if isinstance(data['users'].get('admin'), str):")
        print("            data['users']['admin'] = {'password': data['users']['admin'], 'is_admin': True}")
        print("        else:")
        print("            data['users']['admin']['is_admin'] = True")
        print("        json.dump(data, f, ensure_ascii=False, indent=2)")
        print()
else:
    print(f"    ✗ Файл users.json не найден")

print("\n=== ГОТОВО ===")
print("\nРекомендации:")
print("1. Для Railway: обратитесь к базе данных через панель Railway")
print("2. Выполните: UPDATE users SET is_admin = 1 WHERE login = 'admin';")
print("3. Перезайдите на сайте под admin")
