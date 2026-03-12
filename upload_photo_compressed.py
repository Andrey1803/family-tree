# -*- coding: utf-8 -*-
"""
Загрузка фото со сжатием для Николая Емельянова (персона ID 2).
"""
import urllib.request
import json
import base64
import os

try:
    from PIL import Image
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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
        # Если PIL нет, читаем как есть
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    try:
        img = Image.open(filepath)
        
        # Поворот по EXIF
        try:
            from PIL import ExifTags
            exif = img._getexif()
            if exif:
                for tag_id, tag in ExifTags.TAGS.items():
                    if tag == "Orientation":
                        orientation = exif.get(tag_id)
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
        except Exception:
            pass
        
        # Ресайз
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Сохраняем в JPEG
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] Ошибка сжатия: {e}")
        return None

def main():
    print("="*60)
    print("Загрузка фото со сжатием")
    print("="*60)
    
    token = get_token()
    print("\n[1] Скачивание дерева...")
    tree = download_tree(token)
    persons = tree.get("persons", {})
    
    # Загружаем фото для персоны 2
    print("\n[2] Загрузка фото для Николая Емельянова (ID 2)...")
    photo_file = "photos/i.jpg"
    
    if os.path.exists(photo_file):
        # Сжимаем и кодируем
        photo_base64 = compress_and_encode_photo(photo_file)
        
        if photo_base64:
            print(f"   Размер после сжатия: {len(photo_base64)} символов ({len(photo_base64) // 1024} KB)")
            
            # Обновляем данные
            persons["2"]["photo"] = photo_base64
            persons["2"]["photo_path"] = photo_file
            
            # Загружаем
            print("\n[3] Загрузка на сервер...")
            result = upload_tree(token, tree)
            print(f"   Результат: {result}")
            
            # Проверяем
            print("\n[4] Проверка...")
            tree2 = download_tree(token)
            p2 = tree2.get("persons", {}).get("2", {})
            has_photo = "YES" if p2.get("photo") else "NO"
            photo_size = len(p2.get("photo", ""))
            print(f"   photo: {has_photo} ({photo_size} символов)")
            
            if photo_size > 0:
                print("\n[OK] Фото успешно загружено!")
            else:
                print("\n[ERROR] Фото не сохранилось на сервере!")
        else:
            print("   [ERROR] Не удалось сжать фото")
    else:
        print(f"   [ERROR] Файл {photo_file} не найден")

if __name__ == "__main__":
    main()
