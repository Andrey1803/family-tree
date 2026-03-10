# -*- coding: utf-8 -*-
"""Сервис работы с деревом: загрузка/сохранение JSON, совместим с desktop."""

import json
import os

# Корень проекта
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Папка данных. На Railway: DATA_DIR=/data (volume)
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(_project_root, "data")

# Создаём папку данных, если её нет
os.makedirs(DATA_DIR, exist_ok=True)


def get_data_path(username):
    """Путь к файлу дерева пользователя."""
    # Очищаем имя пользователя от опасных символов
    safe = (username or "Гость").strip()
    # Заменяем опасные символы на подчёркивание
    for char in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']:
        safe = safe.replace(char, '_')
    # Если после очистки пусто — используем "Гость"
    safe = safe or "Гость"
    path = os.path.join(DATA_DIR, f"family_tree_{safe}.json")
    print(f"[TREE_SERVICE] get_data_path: username='{username}', safe='{safe}', path='{path}'")
    return path


def load_tree(username):
    """Загружает дерево из JSON. Возвращает {persons: {}, marriages: [], current_center}.
    
    Добавлена улучшенная обработка ошибок и валидация структуры данных.
    """
    path = get_data_path(username)
    if not os.path.exists(path):
        print(f"[TREE_SERVICE] File not found: {path}")
        return {"persons": {}, "marriages": [], "current_center": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Валидация структуры данных
        if not isinstance(data, dict):
            print(f"[TREE_SERVICE] ERROR: Invalid data type for {username}: expected dict, got {type(data)}")
            return {"persons": {}, "marriages": [], "current_center": None}
        
        persons = data.get("persons", {})
        
        # Проверяем, что persons - это dict, а не list или другой тип
        if not isinstance(persons, dict):
            print(f"[TREE_SERVICE] ERROR: 'persons' should be dict, got {type(persons)} for user {username}")
            # Пытаемся исправить: если это list, конвертируем в dict
            if isinstance(persons, list):
                print(f"[TREE_SERVICE] Attempting to convert list to dict for {username}")
                persons_dict = {}
                for p in persons:
                    if isinstance(p, dict) and "id" in p:
                        persons_dict[str(p["id"])] = p
                persons = persons_dict
            else:
                persons = {}
        
        marriages_raw = data.get("marriages", [])
        
        # Валидация marriages
        if not isinstance(marriages_raw, list):
            print(f"[TREE_SERVICE] WARNING: 'marriages' should be list, got {type(marriages_raw)}")
            marriages_raw = []
        
        marriages = [tuple(p) for p in marriages_raw if isinstance(p, (list, tuple)) and len(p) == 2]
        
        print(f"[TREE_SERVICE] Loaded {len(persons)} persons, {len(marriages)} marriages for {username}")
        
        return {
            "persons": persons,
            "marriages": marriages,
            "current_center": data.get("current_center"),
        }
    except json.JSONDecodeError as e:
        print(f"[TREE_SERVICE] ERROR: JSON decode error for {username}: {e}")
        return {"persons": {}, "marriages": [], "current_center": None}
    except Exception as e:
        print(f"[TREE_SERVICE] ERROR: Unexpected error loading tree for {username}: {type(e).__name__}: {e}")
        return {"persons": {}, "marriages": [], "current_center": None}


def save_tree(username, data):
    """Сохраняет дерево в JSON."""
    path = get_data_path(username)
    persons = data.get("persons", {})
    persons_serial = {}
    for pid, p in persons.items():
        pp = dict(p) if isinstance(p, dict) else (getattr(p, "__dict__", p) or p)
        if isinstance(pp, dict):
            for k in ("parents", "children", "spouse_ids"):
                if k in pp and not isinstance(pp[k], list):
                    pp[k] = list(pp[k]) if pp[k] else []
            persons_serial[str(pid)] = pp
        else:
            persons_serial[str(pid)] = p
    marriages_raw = data.get("marriages", [])
    marriages_out = []
    for m in marriages_raw:
        if isinstance(m, (list, tuple)) and len(m) == 2:
            a, b = str(m[0]), str(m[1])
            marriages_out.append(sorted([a, b]))
    out = {
        "persons": persons_serial,
        "marriages": marriages_out,
        "current_center": str(data.get("current_center")) if data.get("current_center") else None,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
