# -*- coding: utf-8 -*-
"""
Создание дерева для Натальи Емельяновой (Юркевич).
"""
import urllib.request
import json
import base64
from datetime import datetime

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

# Данные для входа
NATALYA_LOGIN = "Наталья Емельянова"
NATALYA_PASSWORD = "130196"
ANDREY_LOGIN = "Андрей Емельянов"
ANDREY_PASSWORD = "18031981asdF"

def get_token(login, password):
    """Получить токен авторизации."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": login, "password": password}).encode(),
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

def upload_tree(token, tree_data, tree_name):
    """Загрузить дерево на сервер."""
    req = urllib.request.Request(
        f"{SYNC_URL}/api/sync/upload",
        data=json.dumps({"tree": tree_data, "tree_name": tree_name}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def create_natalya_tree():
    """Создать дерево для Натальи Емельяновой."""
    
    # Создаём структуру дерева
    # Используем ID с префиксом "n_" для уникальности
    tree = {
        "persons": {},
        "marriages": []
    }
    
    # === Персоны ===
    
    # n1. Наталья Емельянова (Юркевич) - главная персона
    tree["persons"]["n1"] = {
        "name": "Наталья",
        "surname": "Емельянова",
        "patronymic": "",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Девичья фамилия: Юркевич",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": ["2", "3"],  # Мама и папа
        "children": [],
        "spouse_ids": [],
        "collapsed_branches": False
    }
    
    # 2. Юркевич Светлана Владимировна (Новик) - мама
    tree["persons"]["2"] = {
        "name": "Светлана",
        "surname": "Юркевич",
        "patronymic": "Владимировна",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Девичья фамилия: Новик",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": ["4", "5"],  # Мамина мама (Гречка Регина)
        "children": ["1", "6"],  # Наталья и Татьяна
        "spouse_ids": ["3"],
        "collapsed_branches": False
    }
    
    # 3. Юркевич Юрий Тимофеевич - папа
    tree["persons"]["3"] = {
        "name": "Юрий",
        "surname": "Юркевич",
        "patronymic": "Тимофеевич",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "male",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": ["7", "8"],  # Папины родители
        "children": ["1", "6"],  # Наталья и Татьяна
        "spouse_ids": ["2"],
        "collapsed_branches": False
    }
    
    # 4. Гречка Регина Кирилловна - мамина мама
    tree["persons"]["4"] = {
        "name": "Регина",
        "surname": "Гречка",
        "patronymic": "Кирилловна",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Мама Светланы (Новик)",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": [],
        "children": ["2"],  # Светлана
        "spouse_ids": ["5"],
        "collapsed_branches": False
    }
    
    # 5. Новик (дедушка) - мамин папа
    tree["persons"]["5"] = {
        "name": "Владимир",
        "surname": "Новик",
        "patronymic": "",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "male",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Папа Светланы",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": [],
        "children": ["2"],  # Светлана
        "spouse_ids": ["4"],
        "collapsed_branches": False
    }
    
    # 6. Юркевич Татьяна - папина сестра
    tree["persons"]["6"] = {
        "name": "Татьяна",
        "surname": "Юркевич",
        "patronymic": "",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Сестра Натальи",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": ["2", "3"],  # Светлана и Юрий
        "children": [],
        "spouse_ids": [],
        "collapsed_branches": False
    }
    
    # 7. Федорова (Юркевич) Анна Тимофеевна - папина сестра
    tree["persons"]["7"] = {
        "name": "Анна",
        "surname": "Федорова",
        "patronymic": "Тимофеевна",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Девичья фамилия: Юркевич. Сестра Юрия.",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": ["8", "9"],  # Родители Юрия
        "children": [],
        "spouse_ids": [],
        "collapsed_branches": False
    }
    
    # 8. Тимофей Юркевич - папин папа
    tree["persons"]["8"] = {
        "name": "Тимофей",
        "surname": "Юркевич",
        "patronymic": "",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "male",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Папа Юрия и Анны",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": [],
        "children": ["3", "7"],  # Юрий и Анна
        "spouse_ids": ["9"],
        "collapsed_branches": False
    }
    
    # 9. Бабушка (папина мама)
    tree["persons"]["9"] = {
        "name": "",
        "surname": "Юркевич",
        "patronymic": "",
        "birth_date": "",
        "death_date": "",
        "is_deceased": False,
        "gender": "female",
        "photo": None,
        "photo_path": "",
        "photo_full": None,
        "birth_place": "",
        "biography": "",
        "burial_place": "",
        "burial_date": "",
        "occupation": "",
        "education": "",
        "address": "",
        "notes": "Мама Юрия и Анны",
        "phone": "",
        "email": "",
        "vk": "",
        "telegram": "",
        "whatsapp": "",
        "blood_type": "",
        "rh_factor": "",
        "allergies": "",
        "chronic_conditions": "",
        "links": [],
        "photo_album": [],
        "parents": [],
        "children": ["3", "7"],  # Юрий и Анна
        "spouse_ids": ["8"],
        "collapsed_branches": False
    }
    
    # === Браки ===
    tree["marriages"] = [
        {"persons": ["2", "3"]},  # Светлана и Юрий
        {"persons": ["4", "5"]},  # Регина и Владимир (Новик)
        {"persons": ["8", "9"]},  # Тимофей и жена
    ]
    
    return tree

def main():
    print("="*60)
    print("Создание дерева для Натальи Емельяновой")
    print("="*60)
    
    # 1. Вход как Наталья
    print(f"\n[1] Вход как {NATALYA_LOGIN}...")
    try:
        token = get_token(NATALYA_LOGIN, NATALYA_PASSWORD)
        print("[OK] Token получен")
    except Exception as e:
        print(f"[ERROR] Не удалось войти: {e}")
        print("Попробуем создать дерево через Андрея...")
        token = get_token(ANDREY_LOGIN, ANDREY_PASSWORD)
    
    # 2. Проверяем текущее дерево
    print("\n[2] Проверка текущего дерева...")
    try:
        tree = download_tree(token)
        persons_count = len(tree.get("persons", {}))
        print(f"[INFO] На сервере: {persons_count} персон")
        
        if persons_count > 0:
            print("[WARN] Дерево не пустое! Продолжить? (y/n)")
            # response = input()
            # if response.lower() != 'y':
            #     return
    except Exception as e:
        print(f"[INFO] Дерево не найдено или ошибка: {e}")
        tree = {"persons": {}, "marriages": []}
    
    # 3. Создаём новое дерево
    print("\n[3] Создание дерева...")
    natalya_tree = create_natalya_tree()
    print(f"[INFO] Создано {len(natalya_tree['persons'])} персон")
    print(f"[INFO] Создано {len(natalya_tree['marriages'])} браков")
    
    # 4. Загружаем на сервер
    print("\n[4] Загрузка на сервер...")
    result = upload_tree(token, natalya_tree, f"Дерево {NATALYA_LOGIN}")
    print(f"[OK] {result}")
    
    # 5. Проверка
    print("\n[5] Проверка...")
    tree2 = download_tree(token)
    persons2 = tree2.get("persons", {})
    print(f"[INFO] На сервере: {len(persons2)} персон")
    
    # Выводим список персон
    print("\n[INFO] Персоны в дереве:")
    for pid, p in persons2.items():
        print(f"   [{pid}] {p.get('surname')} {p.get('name')} {p.get('patronymic', '')}")
    
    print("\n" + "="*60)
    print("Готово! Дерево Натальи Емельяновой создано")
    print("="*60)

if __name__ == "__main__":
    main()
