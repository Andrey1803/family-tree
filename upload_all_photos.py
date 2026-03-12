# -*- coding: utf-8 -*-
"""
Загрузка всех фото из папки photos/ со сжатием.
"""
import urllib.request
import json
import base64
import os
from pathlib import Path

try:
    from PIL import Image
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"
PHOTOS_DIR = Path("photos")

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

def upload_tree(token, tree_data):
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/upload",
        data=json.dumps({"tree": tree_data, "tree_name": "Дерево " + USERNAME}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def compress_and_encode_photo(filepath, max_size=(400, 400), quality=75):
    """Сжимает и кодирует фото в base64."""
    if not PIL_AVAILABLE:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    try:
        img = Image.open(filepath)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"   [ERROR] {e}")
        return None

def main():
    print("="*60)
    print("Загрузка всех фото со сжатием")
    print("="*60)
    
    token = get_token()
    print("\n[1] Скачивание дерева...")
    tree = download_tree(token)
    persons = tree.get("persons", {})
    print(f"    Загружено {len(persons)} персон")
    
    # Список фото для загрузки
    photo_mapping = {
        "1.jpg": "1",        # Андрей Емельянов
        "i.jpg": "2",        # Николай Емельянов
        # Добавьте другие фото по необходимости
    }
    
    print("\n[2] Загрузка фото...")
    updated = 0
    
    for filename, person_id in photo_mapping.items():
        photo_file = PHOTOS_DIR / filename
        
        if not photo_file.exists():
            print(f"   [WARN] {filename} не найден")
            continue
        
        if person_id not in persons:
            print(f"   [WARN] Персона {person_id} не найдена")
            continue
        
        person = persons[person_id]
        print(f"\n   [{person_id}] {person.get('surname')} {person.get('name')}")
        
        # Сжимаем и кодируем
        photo_base64 = compress_and_encode_photo(photo_file)
        
        if photo_base64:
            print(f"   Размер: {len(photo_base64) // 1024} KB")
            
            persons[person_id]["photo"] = photo_base64
            persons[person_id]["photo_path"] = str(photo_file)
            updated += 1
            print(f"   [OK] Фото добавлено")
        else:
            print(f"   [ERROR] Не удалось обработать фото")
    
    # Загружаем обновлённое дерево
    if updated > 0:
        print(f"\n[3] Загрузка обновлённого дерева ({updated} фото)...")
        result = upload_tree(token, tree)
        print(f"    {result}")
        
        # Проверяем
        print("\n[4] Проверка...")
        tree2 = download_tree(token)
        persons2 = tree2.get("persons", {})
        
        count = 0
        for pid in photo_mapping.values():
            if persons2.get(pid, {}).get("photo"):
                count += 1
        
        print(f"    Фото на сервере: {count} из {updated}")
    
    print(f"\n{'='*60}")
    print(f"Готово! Загружено {updated} фото")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
