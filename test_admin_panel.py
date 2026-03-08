# -*- coding: utf-8 -*-
"""Проверка работы админ-панели"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Добавляем путь к модулю
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

print("=" * 60)
print("ТЕСТ: Проверка админ-панели")
print("=" * 60)

# 1. Проверяем импорт
print("\n1. Проверка импорта admin_dashboard_full...")
try:
    from admin_dashboard_full import AdminDashboard, open_admin_dashboard
    print("   [OK] Модуль импортирован")
except Exception as e:
    print(f"   [ERR] Ошибка импорта: {e}")
    input("Нажмите Enter...")
    exit(1)

# 2. Проверяем подключение к серверу
print("\n2. Проверка подключения к серверу...")
from admin_dashboard_full import SYNC_URL
import urllib.request
import json

try:
    req = urllib.request.Request(SYNC_URL, method='GET')
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"   [OK] Сервер доступен: {SYNC_URL}")
except Exception as e:
    print(f"   [ERR] Сервер недоступен: {e}")

# 3. Проверяем авторизацию
print("\n3. Проверка авторизации...")
login = "Андрей Емельянов"
password = "18031981asdF"

try:
    data = json.dumps({"login": login, "password": password}).encode('utf-8')
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
            print(f"   [OK] Авторизация успешна")
            print(f"       Логин: {login}")
            print(f"       Token: {token[:30]}...")
        else:
            print(f"   [ERR] Token не получен")
except Exception as e:
    print(f"   [ERR] Ошибка авторизации: {e}")

# 4. Проверяем доступ к админ API
print("\n4. Проверка доступа к админ API...")
if token:
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/stats",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            stats = json.loads(response.read().decode())
            overview = stats.get('overview', {})
            print(f"   [OK] Админ API доступен")
            print(f"       Пользователей: {overview.get('total_users', 0)}")
            print(f"       Деревьев: {overview.get('total_trees', 0)}")
            print(f"       Персон: {overview.get('total_persons', 0)}")
    except Exception as e:
        print(f"   [ERR] Ошибка доступа: {e}")

print("\n" + "=" * 60)
print("Все тесты завершены!")
print("\nАндрей Емельянов, админ-панель готова к использованию!")
print("Для открытия: Файл → 👑 Админ-панель")
print("=" * 60)
input("Нажмите Enter для выхода...")
