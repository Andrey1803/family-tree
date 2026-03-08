# -*- coding: utf-8 -*-
from kinship import calculate_kinship
from models import FamilyTreeModel, Person

# Создаём тестовое дерево
m = FamilyTreeModel()

# 1. Дед
p1 = Person(name='Дед', surname='Иванов', gender='Мужской')
p1.id = '1'
m.persons['1'] = p1

# 2. Отец (сын деда)
p2 = Person(name='Отец', surname='Иванов', gender='Мужской')
p2.id = '2'
p2.parents = {'1'}
m.persons['2'] = p2

# 3. Внук (сын отца)
p3 = Person(name='Внук', surname='Иванов', gender='Мужской')
p3.id = '3'
p3.parents = {'2'}
m.persons['3'] = p3

# 4. Дядя (брат отца)
p4 = Person(name='Дядя', surname='Иванов', gender='Мужской')
p4.id = '4'
p4.parents = {'1'}
m.persons['4'] = p4

# 5. Племянник (сын дяди)
p5 = Person(name='Племянник', surname='Иванов', gender='Мужской')
p5.id = '5'
p5.parents = {'4'}
m.persons['5'] = p5

# Синхронизируем children
p1.children = {'2', '4'}
p2.children = {'3'}
p4.children = {'5'}

# Тестируем с центром = ОТЕЦ (2)
print('=== Центр: ОТЕЦ (id=2) ===')
rels = calculate_kinship(m, '2')
for pid, rel in rels.items():
    name = m.persons[pid].name
    print(f'{name} (id={pid}): {rel}')

print()
print('=== Центр: ВНУК (id=3) ===')
rels = calculate_kinship(m, '3')
for pid, rel in rels.items():
    name = m.persons[pid].name
    print(f'{name} (id={pid}): {rel}')

print()
print('Ожидаем для центра ВНУК (3):')
print('Дед (1): Дед')
print('Отец (2): Отец')
print('Дядя (4): Двоюродный дед')
print('Племянник (5): Двоюродный дядя')
