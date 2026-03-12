# -*- coding: utf-8 -*-
"""
Создание дерева для Натальи Емельяновой (Юркевич).
Используем уникальные ID: n1, n2, n3...
"""
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

NATALYA_LOGIN = "Наталья Емельянова"
NATALYA_PASSWORD = "130196"

def get_token(login, password):
    req = urllib.request.Request(
        f"{SYNC_URL}/api/auth/login",
        data=json.dumps({"login": login, "password": password}).encode(),
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

def upload_tree(token, tree_data, tree_name):
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
    
    tree = {"persons": {}, "marriages": []}
    
    # n1: Наталья Емельянова (Юркевич)
    tree["persons"]["n1"] = {
        "name": "Наталья", "surname": "Емельянова", "patronymic": "",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "female",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Девичья фамилия: Юркевич",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": ["n2", "n3"], "children": [], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # n2: Юркевич Светлана Владимировна (Новик) - мама
    tree["persons"]["n2"] = {
        "name": "Светлана", "surname": "Юркевич", "patronymic": "Владимировна",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "female",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Девичья фамилия: Новик",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": ["n4"], "children": ["n1", "n6"], "spouse_ids": ["n3"], "collapsed_branches": 0
    }
    
    # n3: Юркевич Юрий Тимофеевич - папа
    tree["persons"]["n3"] = {
        "name": "Юрий", "surname": "Юркевич", "patronymic": "Тимофеевич",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "male",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": ["n8"], "children": ["n1", "n6"], "spouse_ids": ["n2"], "collapsed_branches": 0
    }
    
    # n4: Гречка Регина Кирилловна - мамина мама
    tree["persons"]["n4"] = {
        "name": "Регина", "surname": "Гречка", "patronymic": "Кирилловна",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "female",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Мама Светланы",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": [], "children": ["n2"], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # n5: Новик (дедушка) - мамин папа
    tree["persons"]["n5"] = {
        "name": "Владимир", "surname": "Новик", "patronymic": "",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "male",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Папа Светланы",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": [], "children": ["n2"], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # n6: Юркевич Татьяна - сестра
    tree["persons"]["n6"] = {
        "name": "Татьяна", "surname": "Юркевич", "patronymic": "",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "female",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Сестра Натальи",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": ["n2", "n3"], "children": [], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # n7: Федорова (Юркевич) Анна Тимофеевна - папина сестра
    tree["persons"]["n7"] = {
        "name": "Анна", "surname": "Федорова", "patronymic": "Тимофеевна",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "female",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Девичья фамилия: Юркевич",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": ["n8"], "children": [], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # n8: Тимофей Юркевич - папин папа
    tree["persons"]["n8"] = {
        "name": "Тимофей", "surname": "Юркевич", "patronymic": "",
        "birth_date": "", "death_date": "", "is_deceased": 0, "gender": "male",
        "photo": None, "photo_path": "", "photo_full": None,
        "birth_place": "", "biography": "", "burial_place": "", "burial_date": "",
        "occupation": "", "education": "", "address": "", "notes": "Папа Юрия и Анны",
        "phone": "", "email": "", "vk": "", "telegram": "", "whatsapp": "",
        "blood_type": "", "rh_factor": "", "allergies": "", "chronic_conditions": "",
        "links": [], "photo_album": [],
        "parents": [], "children": ["n3", "n7"], "spouse_ids": [], "collapsed_branches": 0
    }
    
    # === Браки ===
    tree["marriages"] = [
        {"persons": ["n2", "n3"]},  # Светлана и Юрий
    ]
    
    return tree

def main():
    print("="*60)
    print("Создание дерева для Натальи Емельяновой")
    print("="*60)
    
    # 1. Вход
    print(f"\n[1] Вход как {NATALYA_LOGIN}...")
    token = get_token(NATALYA_LOGIN, NATALYA_PASSWORD)
    print("[OK] Token получен")
    
    # 2. Проверка текущего дерева
    print("\n[2] Проверка текущего дерева...")
    try:
        tree = download_tree(token)
        persons_count = len(tree.get("persons", {}))
        print(f"[INFO] На сервере: {persons_count} персон")
    except Exception as e:
        print(f"[INFO] Дерево пустое: {e}")
    
    # 3. Создаём дерево
    print("\n[3] Создание дерева...")
    natalya_tree = create_natalya_tree()
    print(f"[INFO] Создано {len(natalya_tree['persons'])} персон")
    print(f"[INFO] Создано {len(natalya_tree['marriages'])} браков")
    
    # 4. Загружаем
    print("\n[4] Загрузка на сервер...")
    result = upload_tree(token, natalya_tree, f"Дерево {NATALYA_LOGIN}")
    print(f"[OK] {result}")
    
    # 5. Проверка
    print("\n[5] Проверка...")
    tree2 = download_tree(token)
    persons2 = tree2.get("persons", {})
    print(f"[INFO] На сервере: {len(persons2)} персон")
    
    print("\n[INFO] Персоны в дереве:")
    for pid, p in sorted(persons2.items()):
        print(f"   [{pid}] {p.get('surname')} {p.get('name')} {p.get('patronymic', '')}")
    
    print("\n" + "="*60)
    print("Готово! Дерево Натальи Емельяновой создано")
    print("="*60)

if __name__ == "__main__":
    main()
