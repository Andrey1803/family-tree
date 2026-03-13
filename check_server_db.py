# -*- coding: utf-8 -*-
"""
Проверка структуры БД на сервере Railway.
"""
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"

def check_db():
    print("="*60)
    print("Проверка БД на сервере")
    print("="*60)

    # 1. Вход
    print("\n[1] Вход...")
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": USERNAME, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())["token"]
    print(f"[OK] Token получен")

    # 2. Проверка дерева
    print("\n[2] Проверка дерева...")
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

    # 3. Проверка структуры БД через админ API
    print("\n[3] Проверка структуры persons...")
    req = urllib.request.Request(
        f"{SYNC_URL}/api/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req)
    stats = json.loads(resp.read())
    print(f"[INFO] Статистика: {stats}")

if __name__ == "__main__":
    try:
        check_db()
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"[ERROR] {e}")
