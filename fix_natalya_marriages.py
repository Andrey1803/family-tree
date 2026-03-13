# -*- coding: utf-8 -*-
"""Исправление дубликатов браков в дереве Натальи"""

import json
import urllib.request

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

print("=" * 60)
print("ИСПРАВЛЕНИЕ ДУБЛИКАТОВ БРАКОВ - НАТАЛЬЯ")
print("=" * 60)

# 1. Вход
print("\n1. Вход под пользователем 'Наталья Емельянова':")
data = json.dumps({
    "login": "Наталья Емельянова",
    "password": "130196"
}).encode('utf-8')

req = urllib.request.Request(
    f"{SYNC_URL}/api/auth/login",
    data=data,
    method='POST'
)
req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read().decode('utf-8'))
    token = result.get('token')
    print(f"   Токен получен: {token[:20]}...")

# 2. Загрузка дерева
print("\n2. Загрузка дерева:")
req = urllib.request.Request(
    f"{SYNC_URL}/api/sync/download",
    headers={'Authorization': f'Bearer {token}'},
    method='GET'
)

with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read().decode('utf-8'))
    tree = result.get('tree', {})
    persons = tree.get('persons', {})
    marriages_raw = tree.get('marriages', [])
    
    print(f"   Персон: {len(persons)}")
    print(f"   Браков (до очистки): {len(marriages_raw)}")
    
    # 3. Очистка дубликатов
    print("\n3. Очистка дубликатов браков:")
    marriages_unique = []
    seen = set()
    
    for m in marriages_raw:
        # Сортируем IDs для правильного сравнения
        p1, p2 = sorted([m['persons'][0], m['persons'][1]])
        key = (p1, p2, m.get('date', ''))
        
        if key not in seen:
            seen.add(key)
            marriages_unique.append(m)
    
    print(f"   Браков (после очистки): {len(marriages_unique)}")
    print(f"   Удалено дубликатов: {len(marriages_raw) - len(marriages_unique)}")
    
    # 4. Сохранение исправленного дерева
    print("\n4. Сохранение исправленного дерева:")
    tree['marriages'] = marriages_unique
    
    upload_data = {
        'tree': tree,
        'tree_name': 'Дерево Натальи'
    }
    
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/upload",
        data=json.dumps(upload_data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"   Статус: {resp.status}")
        print(f"   Ответ: {result}")

# 5. Проверка
print("\n5. Проверка после исправления:")
req = urllib.request.Request(
    f"{SYNC_URL}/api/sync/download",
    headers={'Authorization': f'Bearer {token}'},
    method='GET'
)

with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read().decode('utf-8'))
    tree = result.get('tree', {})
    print(f"   Персон: {len(tree.get('persons', {}))}")
    print(f"   Браков: {len(tree.get('marriages', []))}")

print("\n" + "=" * 60)
print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
print("=" * 60)
