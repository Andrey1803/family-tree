# -*- coding: utf-8 -*-
"""
Проверка размера фото перед загрузкой.
"""
import urllib.request
import json
import base64
import os

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"

def get_token():
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": USERNAME, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["token"]

def download_tree(token):
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["tree"]

def main():
    print("="*60)
    print("Проверка фото в дереве на сервере")
    print("="*60)
    
    token = get_token()
    tree = download_tree(token)
    persons = tree.get("persons", {})
    
    print(f"\nВсего персон: {len(persons)}")
    
    # Проверяем персон 1 и 2
    for pid in ["1", "2"]:
        if pid in persons:
            p = persons[pid]
            photo = p.get('photo')
            photo_full = p.get('photo_full')
            photo_path = p.get('photo_path', '')
            
            print(f"\n[{pid}] {p.get('surname')} {p.get('name')}:")
            print(f"   photo: {'YES' if photo else 'NO'} ({len(photo) if photo else 0} символов)")
            print(f"   photo_full: {'YES' if photo_full else 'NO'} ({len(photo_full) if photo_full else 0} символов)")
            print(f"   photo_path: {photo_path}")
            
            # Проверяем тип данных
            if photo:
                print(f"   photo type: {type(photo).__name__}")
                if isinstance(photo, str):
                    print(f"   photo starts with: {photo[:20]}...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
