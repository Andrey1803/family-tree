# -*- coding: utf-8 -*-
"""
Импорт CSV в дерево пользователя на Railway сервере.
"""
import csv
import json
import urllib.request
from getpass import getpass

# === НАСТРОЙКИ ===
CSV_FILE = 'сохр дерево2.csv'
SYNC_SERVER_URL = 'https://ravishing-caring-production-3656.up.railway.app'
WEB_SERVER_URL = 'https://family-tree-production-0e7d.up.railway.app'

print("=== ИМПОРТ CSV В СЕМЕЙНОЕ ДЕРЕВО ===\n")

# Логин и пароль от сервера
login = input("Ваш логин (Андрей Емельянов): ").strip() or "Андрей Емельянов"
password = getpass("Ваш пароль: ")

# Шаг 1: Вход на сервер синхронизации
print(f"\n[1/4] Вход на сервер синхронизации...")
try:
    req = urllib.request.Request(
        f"{SYNC_SERVER_URL}/api/auth/login",
        data=json.dumps({"login": login, "password": password}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        if not data.get('token'):
            print(f"❌ Ошибка входа: {data.get('error', 'Неизвестная ошибка')}")
            exit(1)
        token = data['token']
        user_id = data.get('user_id')
        print(f"✅ Успешный вход! Token: {token[:20]}...")
except Exception as e:
    print(f"❌ Ошибка входа: {e}")
    exit(1)

# Шаг 2: Чтение CSV
print(f"\n[2/4] Чтение CSV файла: {CSV_FILE}")
persons = {}
marriages_set = set()

try:
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            pid = str(row['id']).strip()
            if not pid:
                continue
            
            persons[pid] = {
                'name': row.get('name', ''),
                'surname': row.get('surname', ''),
                'patronymic': row.get('patronymic', ''),
                'birth_date': row.get('birth_date', ''),
                'birth_place': row.get('birth_place', ''),
                'gender': row.get('gender', ''),
                'is_deceased': row.get('is_deceased', '') == 'True',
                'death_date': row.get('death_date', ''),
                'maiden_name': row.get('maiden_name', ''),
                'photo_path': row.get('photo_path', ''),
                'biography': row.get('biography', ''),
                'burial_place': row.get('burial_place', ''),
                'burial_date': row.get('burial_date', ''),
                'occupation': row.get('occupation', ''),
                'education': row.get('education', ''),
                'address': row.get('address', ''),
                'notes': row.get('notes', ''),
                'parents': row.get('parents', '').split('|') if row.get('parents') else [],
                'children': row.get('children', '').split('|') if row.get('children') else [],
                'spouse_ids': row.get('spouse_ids', '').split('|') if row.get('spouse_ids') else []
            }
            
            # Добавляем браки из spouse_ids
            if row.get('spouse_ids'):
                for sid in row['spouse_ids'].split('|'):
                    if sid.strip():
                        pair = tuple(sorted([pid, sid.strip()]))
                        marriages_set.add(pair)
    
    marriages = [list(pair) for pair in sorted(marriages_set)]
    print(f"✅ Загружено персон: {len(persons)}")
    print(f"✅ Браков: {len(marriages)}")
    
except Exception as e:
    print(f"❌ Ошибка чтения CSV: {e}")
    exit(1)

# Шаг 3: Загрузка дерева на сервер синхронизации
print(f"\n[3/4] Загрузка дерева на сервер синхронизации...")
tree_data = {
    'persons': persons,
    'marriages': marriages,
    'current_center': '1'  # Андрей Николаевич Емельянов
}

try:
    req = urllib.request.Request(
        f"{SYNC_SERVER_URL}/api/sync/upload",
        data=json.dumps({
            'tree': tree_data,
            'tree_name': f"Дерево {login}"
        }).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        print(f"✅ Сервер синхронизации: {result}")
except Exception as e:
    print(f"❌ Ошибка загрузки на сервер синхронизации: {e}")
    print("⚠️ Продолжаем с загрузкой на веб-сервер...")

# Шаг 4: Загрузка на веб-сервер
print(f"\n[4/4] Загрузка дерева на веб-сервер...")
try:
    # Сначала получаем сессию
    session_req = urllib.request.Request(
        f"{WEB_SERVER_URL}/api/auth/session",
        data=json.dumps({
            'token': token,
            'user_id': user_id,
            'login': login
        }).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    # Создаем куки-опener
    import http.cookiejar
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [('Content-Type', 'application/json')]
    
    # Устанавливаем сессию
    with opener.open(session_req, timeout=10) as resp:
        print(f"✅ Сессия установлена")
    
    # Загружаем дерево
    tree_req = urllib.request.Request(
        f"{WEB_SERVER_URL}/api/tree",
        data=json.dumps(tree_data).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with opener.open(tree_req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        if result.get('ok'):
            print(f"✅✅✅ ИМПОРТ ЗАВЕРШЁН УСПЕШНО! ✅✅✅")
            print(f"\n📊 Итого:")
            print(f"   - Персон: {len(persons)}")
            print(f"   - Браков: {len(marriages)}")
            print(f"   - Центральная персона: Андрей Николаевич Емельянов (ID 1)")
            print(f"\n🌳 Откройте сайт: {WEB_SERVER_URL}")
            print(f"   и войдите под логином '{login}'")
        else:
            print(f"⚠️ Веб-сервер вернул: {result}")
            
except Exception as e:
    print(f"❌ Ошибка загрузки на веб-сервер: {e}")
    print(f"\n⚠️ Но данные уже загружены на сервер синхронизации!")
    print(f"   Откройте {WEB_SERVER_URL} и войдите под вашим логином")

print("\n=== ГОТОВО ===")
