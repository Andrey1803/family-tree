# -*- coding: utf-8 -*-
"""Тест загрузки данных дерева"""
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

# Добавляем папку Дерево
_tree_dir = _here / "Дерево"
if str(_tree_dir) not in sys.path:
    sys.path.insert(0, str(_tree_dir))

from models import FamilyTreeModel

# Тестируем загрузку
data_file = "data/family_tree_Андрей Емельянов.json"
print(f"Пытаемся загрузить: {data_file}")

model = FamilyTreeModel(data_file=data_file)
result = model.load_from_file()

print(f"Результат загрузки: {result}")
print(f"Количество персон: {len(model.persons)}")
print(f"Количество браков: {len(model.marriages)}")
print(f"current_center: {model.current_center}")

if model.persons:
    for pid, p in list(model.persons.items())[:3]:
        print(f"  {pid}: {p.display_name()}, spouse_ids={p.spouse_ids}, parents={p.parents}")
