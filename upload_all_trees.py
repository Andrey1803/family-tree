# -*- coding: utf-8 -*-
"""
Загрузка всех локальных деревьев на сервер синхронизации.
"""
import urllib.request
import json
import os
from pathlib import Path

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"
DATA_DIR = Path("data")

# Пользователи и их пароли
USERS = {
    "Андрей Емельянов": "18031981asdF",
    # Добавьте других пользователей при необходимости
}

def upload_tree(username, password):
    """Загружает дерево пользователя на сервер."""
    print(f"\n{'='*60}")
    print(f"Загрузка дерева: {username}")
    print(f"{'='*60}")
    
    # 1. Вход
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": username, "password": password}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        token = json.loads(resp.read())["token"]
        print(f"[OK] Token получен")
    except Exception as e:
        print(f"[ERROR] Ошибка входа: {e}")
        return False
    
    # 2. Загрузка локального дерева
    tree_file = DATA_DIR / f"family_tree_{username}.json"
    if not tree_file.exists():
        print(f"[ERROR] Файл не найден: {tree_file}")
        return False
    
    with open(tree_file, "r", encoding="utf-8") as f:
        local_data = json.load(f)
    
    persons_count = len(local_data.get("persons", {}))
    marriages_count = len(local_data.get("marriages", []))
    print(f"[OK] Локально: {persons_count} персон, {marriages_count} браков")
    
    # 3. Загрузка на сервер
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/upload",
            data=json.dumps({"tree": local_data, "tree_name": f"Дерево {username}"}).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"[OK] Загрузка на сервер: {result.get('message', 'OK')}")
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки: {e}")
        return False
    
    # 4. Проверка скачивания
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/sync/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        tree = data.get("tree", {})
        server_persons = len(tree.get("persons", {}))
        server_marriages = len(tree.get("marriages", []))
        print(f"[OK] Сервер вернул: {server_persons} персон, {server_marriages} браков")
        
        if server_marriages == marriages_count:
            print(f"[DONE] Браки загружены успешно!")
        else:
            print(f"[WARN] Браки: локально {marriages_count}, на сервере {server_marriages}")
    except Exception as e:
        print(f"[ERROR] Ошибка скачивания: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("Загрузка деревьев на сервер синхронизации")
    print("="*60)
    
    success_count = 0
    for username, password in USERS.items():
        if upload_tree(username, password):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Завершено: {success_count}/{len(USERS)} деревьев")
    print(f"{'='*60}")
