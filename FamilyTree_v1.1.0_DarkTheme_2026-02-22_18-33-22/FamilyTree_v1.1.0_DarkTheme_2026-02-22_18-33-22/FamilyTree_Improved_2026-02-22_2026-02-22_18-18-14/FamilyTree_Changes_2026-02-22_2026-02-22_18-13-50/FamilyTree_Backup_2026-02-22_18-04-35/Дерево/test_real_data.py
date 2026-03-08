# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from kinship import calculate_kinship
from models import FamilyTreeModel

# Загружаем реальные данные
m = FamilyTreeModel('../family_tree_Гость.json')
m.load_from_file()

with open('test_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'Всего персон: {len(m.persons)}\n')

    # Для каждой персоны проверяем родство
    for center_id in list(m.persons.keys())[:5]:  # Первые 5 как центр
        center = m.get_person(center_id)
        f.write(f'\n=== Центр: {center.name} {center.surname} (id={center_id}) ===\n')
        
        rels = calculate_kinship(m, center_id)
        for pid, rel in rels.items():
            p = m.get_person(pid)
            f.write(f'{p.name} {p.surname} (id={pid}): {rel}\n')

print('Готово! Проверьте test_output.txt')
