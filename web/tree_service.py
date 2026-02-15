# -*- coding: utf-8 -*-
"""Сервис работы с деревом: загрузка/сохранение JSON, совместим с desktop."""

import json
import os

# Корень проекта. На Railway: DATA_DIR=/data (volume для хранения)
DATA_DIR = os.environ.get("DATA_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path(username):
    """Путь к файлу дерева пользователя."""
    safe = (username or "Гость").replace("..", "").strip() or "Гость"
    return os.path.join(DATA_DIR, f"family_tree_{safe}.json")


def load_tree(username):
    """Загружает дерево из JSON. Возвращает {persons: {}, marriages: [], current_center}."""
    path = get_data_path(username)
    if not os.path.exists(path):
        return {"persons": {}, "marriages": [], "current_center": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        persons = data.get("persons", {})
        marriages_raw = data.get("marriages", [])
        marriages = [tuple(p) for p in marriages_raw if len(p) == 2]
        return {
            "persons": persons,
            "marriages": marriages,
            "current_center": data.get("current_center"),
        }
    except Exception:
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
