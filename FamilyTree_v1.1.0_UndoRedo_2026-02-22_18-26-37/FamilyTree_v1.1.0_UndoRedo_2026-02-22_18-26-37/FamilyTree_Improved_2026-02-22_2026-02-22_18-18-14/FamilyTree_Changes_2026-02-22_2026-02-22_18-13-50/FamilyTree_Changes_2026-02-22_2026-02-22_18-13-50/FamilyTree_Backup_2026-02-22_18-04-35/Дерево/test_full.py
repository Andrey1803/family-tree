# -*- coding: utf-8 -*-
from kinship import calculate_kinship
from models import FamilyTreeModel

m = FamilyTreeModel('../family_tree_Гость.json')
m.load_from_file()

with open('test_full.txt', 'w', encoding='utf-8') as f:
    # Проверяем для ключевых персон
    for cid in ['1', '2', '5', '23', '36']:
        c = m.get_person(cid)
        f.write(f'\n=== {c.name} {c.surname} (id={cid}) ===\n')
        rels = calculate_kinship(m, cid)
        for pid, rel in sorted(rels.items(), key=lambda x: int(x[0])):
            p = m.get_person(pid)
            f.write(f'{pid}: {p.name} - {rel}\n')

print('Готово! test_full.txt')
