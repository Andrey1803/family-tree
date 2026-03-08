from models import FamilyTreeModel
m = FamilyTreeModel('../family_tree_Гость.json')
m.load_from_file()

with open('parents.txt', 'w', encoding='utf-8') as f:
    for pid in ['35', '36', '2', '1', '12', '22']:
        p = m.get_person(pid)
        parents = list(p.parents) if p.parents else []
        f.write(f'{pid}: {p.name} - родители: {parents}\n')

print('Готово! parents.txt')
