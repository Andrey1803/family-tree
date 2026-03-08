# -*- coding: utf-8 -*-
"""Тест: сын племянницы."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

from models import FamilyTreeModel
from kinship import calculate_kinship

# Создаём дерево
model = FamilyTreeModel()

# Создаём персон
id_map = {}
id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
id_map['Брат'] = model.add_person("Брат", "Иванов", "", "", "Мужской")[0]
id_map['Племянница'] = model.add_person("Племянница", "Иванова", "", "", "Женский")[0]
id_map['СынПлемянницы'] = model.add_person("Сын Племянницы", "Иванов", "", "", "Мужской")[0]

# Устанавливаем связи
# Брат - общий родитель со мной
model.add_parent(id_map['Брат'], id_map['Я'])  # Упрощённо: Брат - родитель Я (для теста)

# На самом деле правильно:
model = FamilyTreeModel()
id_map = {}
id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
id_map['Родитель'] = model.add_person("Родитель", "Иванов", "", "", "Мужской")[0]
id_map['Брат'] = model.add_person("Брат", "Иванов", "", "", "Мужской")[0]
id_map['Племянница'] = model.add_person("Племянница", "Иванова", "", "", "Женский")[0]
id_map['СынПлемянницы'] = model.add_person("Сын Племянницы", "Иванов", "", "", "Мужской")[0]

# Правильные связи
model.add_parent(id_map['Я'], id_map['Родитель'])
model.add_parent(id_map['Брат'], id_map['Родитель'])
model.add_parent(id_map['Племянница'], id_map['Брат'])
model.add_parent(id_map['СынПлемянницы'], id_map['Племянница'])

# Вычисляем родство относительно МЕНЯ
relationships = calculate_kinship(model, id_map['Я'])

print("=" * 60)
print("ТЕСТ: Сын племянницы")
print("=" * 60)
print()
print("Дерево:")
print("  Родитель")
print("  /      \\")
print(" Я       Брат")
print("           |")
print("      Племянница")
print("           |")
print("    Сын Племянницы")
print()
print("=" * 60)
print("Результаты (относительно МЕНЯ):")
print("=" * 60)

for pid, rel in relationships.items():
    person = model.get_person(pid)
    print(f"  {person.name:20s} → {rel}")

print()
print("=" * 60)
print(f"Сын племянницы (id={id_map['СынПлемянницы']}) → {relationships.get(id_map['СынПлемянницы'], 'НЕ ОПРЕДЕЛЕНО')}")
print("=" * 60)
