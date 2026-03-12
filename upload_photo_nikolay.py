# -*- coding: utf-8 -*-
"""
Загрузка фото для Николая Емельянова (персона ID 2).
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

def image_to_base64(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("="*60)
    print("Загрузка фото для Николая Емельянова")
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
    
    # 3. Проверка персоны ID 2
    print("\n[3] Проверка персоны ID 2...")
    if "2" in persons:
        person = persons["2"]
        print(f"   {person.get('surname')} {person.get('name')} {person.get('patronymic')}")
        print(f"   Дата рождения: {person.get('birth_date')}")
    else:
        print("   [ERROR] Персона ID 2 не найдена!")
        return
    
    # 4. Загрузка фото i.jpg
    print("\n[4] Загрузка фото i.jpg...")
    photo_file = "photos/i.jpg"
    
    if not os.path.exists(photo_file):
        print(f"   [ERROR] Файл {photo_file} не найден!")
        return
    
    photo_base64 = image_to_base64(photo_file)
    file_size = os.path.getsize(photo_file)
    print(f"   Размер: {file_size // 1024} KB ({len(photo_base64)} символов)")
    
    # Обновляем данные персоны
    persons["2"]["photo"] = photo_base64
    persons["2"]["photo_path"] = photo_file
    print(f"   [OK] Фото добавлено персоне ID 2")
    
    # 5. Загрузка обновлённого дерева
    print("\n[5] Загрузка обновлённого дерева...")
    result = upload_tree(token, tree)
    print(f"[OK] {result.get('message', 'Успешно')}")
    print(f"[INFO] Персон: {result.get('persons_count', 'N/A')}")
    
    print(f"\n{'='*60}")
    print("Готово! Фото Николая Емельянова загружено")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
