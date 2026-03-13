# -*- coding: utf-8 -*-
"""
Проверка фото в дереве на сервере.
"""
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"

def check_photos():
    print("="*60)
    print("Проверка фото на сервере")
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

    # 2. Скачивание дерева
    print("\n[2] Скачивание дерева...")
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    tree = data.get("tree", {})
    persons = tree.get("persons", {})
    
    print(f"[INFO] Всего персон: {len(persons)}")
    
    # 3. Проверка фото
    persons_with_photo = 0
    persons_with_photo_full = 0
    
    for pid, pdata in persons.items():
        photo = pdata.get('photo')
        photo_full = pdata.get('photo_full')
        
        if photo:
            persons_with_photo += 1
            print(f"   [PHOTO] {pdata.get('surname')} {pdata.get('name')}: photo={len(photo) if photo else 0} bytes")
        if photo_full:
            persons_with_photo_full += 1
            print(f"   [PHOTO_FULL] {pdata.get('surname')} {pdata.get('name')}: photo_full={len(photo_full) if photo_full else 0} bytes")
    
    print(f"\n[INFO] Персон с photo: {persons_with_photo}")
    print(f"[INFO] Персон с photo_full: {persons_with_photo_full}")
    
    # 4. Проверка локального файла
    print("\n[3] Проверка локального файла...")
    with open("data/family_tree_Андрей Емельянов.json", "r", encoding="utf-8") as f:
        local_data = json.load(f)
    
    local_persons = local_data.get("persons", {})
    local_with_photo = 0
    for pid, pdata in local_persons.items():
        if pdata.get('photo'):
            local_with_photo += 1
    
    print(f"[INFO] Локально персон с photo: {local_with_photo}")

if __name__ == "__main__":
    try:
        check_photos()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
