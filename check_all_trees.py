# -*- coding: utf-8 -*-
"""
Проверка деревьев всех пользователей на сервере.
"""
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

# Проверяем обоих пользователей
USERS = [
    ("Андрей Емельянов", "18031981asdF"),
    ("Наталья Емельянова", "130196"),
]

def check_user_tree(username, password):
    print(f"\n{'='*60}")
    print(f"Проверка: {username}")
    print(f"{'='*60}")
    
    try:
        # 1. Вход
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": username, "password": password}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        token = json.loads(resp.read())["token"]
        print(f"[OK] Вход выполнен")
        
        # 2. Проверка дерева
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        tree = data.get("tree", {})
        persons = len(tree.get("persons", {}))
        marriages = len(tree.get("marriages", []))
        
        print(f"[INFO] Дерево: {persons} персон, {marriages} браков")
        
        if persons > 0:
            # Выводим имена первых 5 персон
            persons_list = list(tree.get("persons", {}).values())[:5]
            print(f"[INFO] Первые персоны:")
            for p in persons_list:
                print(f"   - {p.get('surname')} {p.get('name')}")
        
        return persons
        
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"[ERROR] HTTP {e.code}: {error}")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("Проверка деревьев всех пользователей")
    print("="*60)
    
    for username, password in USERS:
        check_user_tree(username, password)
    
    print(f"\n{'='*60}")
    print("Готово")
    print(f"{'='*60}")
