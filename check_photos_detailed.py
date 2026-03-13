# -*- coding: utf-8 -*-
"""
Проверка фото на сервере с подробным выводом.
"""
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"

def check_photos():
    print("="*60)
    print("Проверка фото на сервере (подробно)")
    print("="*60)

    # 1. Вход
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": USERNAME, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())["token"]
    print(f"\n[OK] Token получен")

    # 2. Скачивание дерева
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    tree = data.get("tree", {})
    persons = tree.get("persons", {})
    
    print(f"[INFO] Всего персон: {len(persons)}")
    
    # 3. Проверка всех персон с фото
    print("\nПерсоны с фото:")
    count = 0
    for pid, pdata in persons.items():
        photo = pdata.get('photo')
        photo_path = pdata.get('photo_path', '')
        
        if photo:
            count += 1
            photo_size = len(photo) if isinstance(photo, str) else 0
            print(f"   [{pid}] {pdata.get('surname')} {pdata.get('name')}: {photo_size} символов, path={photo_path}")
        elif photo_path:
            print(f"   [{pid}] {pdata.get('surname')} {pdata.get('name')}: только path={photo_path}")
    
    print(f"\n[INFO] Персон с photo: {count}")
    
    # 4. Проверка персон 1 и 2
    print("\nПроверка персон 1 и 2:")
    for pid in ["1", "2"]:
        if pid in persons:
            p = persons[pid]
            has_photo = "YES" if p.get('photo') else "NO"
            photo_path = p.get('photo_path', 'N/A')
            print(f"   [{pid}] {p.get('surname')} {p.get('name')}: photo={has_photo}, path={photo_path}")

if __name__ == "__main__":
    try:
        check_photos()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
