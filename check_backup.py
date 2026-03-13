# -*- coding: utf-8 -*-
import json

# Проверка резервной копии
with open('data/backup_all_trees_20260312_193515.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

print("="*60)
print("Резервная копия от", backup.get('export_date', 'неизвестно'))
print("="*60)

trees = backup.get('trees', [])
print(f"\nВсего деревьев: {len(trees)}")

for tree in trees:
    filename = tree.get('filename', 'unknown')
    data = tree.get('data', {})
    persons = len(data.get('persons', {}))
    marriages = len(data.get('marriages', []))
    print(f"  {filename}: {persons} персон, {marriages} браков")
