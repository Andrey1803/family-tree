# -*- coding: utf-8 -*-
"""
Загрузка фото из папки photos/ на сервер синхронизации.
"""
import urllib.request
import json
import base64
import os
from pathlib import Path

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
USERNAME = "Андрей Емельянов"
PASSWORD = "18031981asdF"
PHOTOS_DIR = Path("photos")

def get_token():
    """Получить токен авторизации."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": USERNAME, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["token"]

def download_tree(token):
    """Скачать дерево с сервера."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["tree"]

def upload_tree(token, tree_data):
    """Загрузить дерево на сервер."""
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

def image_to_base64(filepath):
    """Конвертировать изображение в base64."""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("="*60)
    print("Загрузка фото на сервер")
    print("="*60)
    
    # 1. Вход
    print("\n[1] Авторизация...")
    token = get_token()
    print(f"[OK] Token получен")
    
    # 2. Скачивание дерева
    print("\n[2] Скачивание дерева...")
    tree = download_tree(token)
    persons = tree.get("persons", {})
    print(f"[INFO] Загружено {len(persons)} персон")
    
    # 3. Проверка фото в папке
    print("\n[3] Проверка папки photos/...")
    if not PHOTOS_DIR.exists():
        print(f"[ERROR] Папка {PHOTOS_DIR} не найдена")
        return
    
    photo_files = list(PHOTOS_DIR.glob("*.jpg")) + list(PHOTOS_DIR.glob("*.png"))
    print(f"[INFO] Найдено {len(photo_files)} файлов")
    
    if not photo_files:
        print("[WARN] Нет файлов для загрузки")
        return
    
    # 4. Загрузка фото
    print("\n[4] Загрузка фото...")
    updated = 0
    
    # Сопоставление файлов с персонами (по имени файла)
    # Например: 1.jpg -> person id "1"
    for photo_file in photo_files:
        # Пробуем найти персону по имени файла (без расширения)
        person_id = photo_file.stem  # "1" из "1.jpg"
        
        if person_id in persons:
            person = persons[person_id]
            print(f"\n   [{person_id}] {person.get('surname')} {person.get('name')}")
            
            # Кодируем фото в base64
            photo_base64 = image_to_base64(photo_file)
            print(f"   Размер: {len(photo_base64)} символов ({os.path.getsize(photo_file) // 1024} KB)")
            
            # Обновляем данные персоны
            persons[person_id]["photo"] = photo_base64
            persons[person_id]["photo_path"] = str(photo_file)
            updated += 1
            print(f"   [OK] Фото добавлено")
        else:
            print(f"\n   [WARN] {photo_file.name} - персона {person_id} не найдена")
    
    # 5. Загрузка обновлённого дерева
    if updated > 0:
        print(f"\n[5] Загрузка обновлённого дерева ({updated} фото)...")
        result = upload_tree(token, tree)
        print(f"[OK] {result.get('message', 'Успешно')}")
        print(f"[INFO] Персон: {result.get('persons_count', 'N/A')}")
    else:
        print("\n[WARN] Нет обновлений для загрузки")
    
    print(f"\n{'='*60}")
    print(f"Готово! Загружено {updated} фото")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
