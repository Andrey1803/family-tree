# -*- coding: utf-8 -*-
"""Проверка API веб-приложения"""

import json
import urllib.request

BASE_URL = "https://family-tree-production-0e7d.up.railway.app"

# Тест 1: Главная страница
print("1. Главная страница:")
try:
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"   Статус: {resp.status}")
except Exception as e:
    print(f"   Ошибка: {e}")

# Тест 2: Локальный вход
print("\n2. Локальный вход (/api/auth/login-local):")
try:
    data = json.dumps({"login": "Тестовый Пользователь", "password": "test123456"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login-local", data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"   Статус: {resp.status}")
        print(f"   Ответ: {result}")
except Exception as e:
    print(f"   Ошибка: {e}")

# Тест 3: Проверка сессии
print("\n3. Проверка сессии (/api/check-session):")
try:
    req = urllib.request.Request(f"{BASE_URL}/api/check-session")
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"   Статус: {resp.status}")
        print(f"   Ответ: {result}")
except Exception as e:
    print(f"   Ошибка: {e}")

# Тест 4: Сервер синхронизации
print("\n4. Сервер синхронизации (/api/health):")
try:
    req = urllib.request.Request("https://ravishing-caring-production-3656.up.railway.app/api/health")
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"   Статус: {resp.status}")
        print(f"   Ответ: {result}")
except Exception as e:
    print(f"   Ошибка: {e}")

print("\n✅ Проверка завершена!")
