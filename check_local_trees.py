# -*- coding: utf-8 -*-
import json
import os

data_dir = "data"
files = [
    "family_tree_Гость.json",
    "family_tree_Гость_fixed.json",
    "family_tree_Емельянов Андрей.json",
    "family_tree_admin.json",
    "family_tree_Андрей Емельянов.json"
]

print("="*60)
print("Проверка локальных деревьев")
print("="*60)

for fname in files:
    fpath = os.path.join(data_dir, fname)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                persons = len(d.get("persons", {}))
                marriages = len(d.get("marriages", []))
                print(f"{fname}: {persons} персон, {marriages} браков")
        except Exception as e:
            print(f"{fname}: Ошибка - {e}")
    else:
        print(f"{fname}: НЕ НАЙДЕН")
