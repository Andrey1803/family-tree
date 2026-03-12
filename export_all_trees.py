# -*- coding: utf-8 -*-
"""Экспорт всех деревьев пользователей в JSON для резервной копии."""

import json
import os
from datetime import datetime

# Путь к данным
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def export_trees():
    """Экспортирует все деревья в один JSON файл."""
    
    all_trees = {
        "export_date": datetime.now().isoformat(),
        "trees": [],
        "users": {}
    }
    
    # Находим все JSON файлы с деревьями
    tree_files = [f for f in os.listdir(DATA_DIR) if f.startswith('family_tree_') and f.endswith('.json')]
    
    print(f"Найдено файлов с деревьями: {len(tree_files)}")
    
    for tree_file in tree_files:
        tree_path = os.path.join(DATA_DIR, tree_file)
        try:
            with open(tree_path, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                all_trees["trees"].append({
                    "filename": tree_file,
                    "data": tree_data
                })
                print(f"✓ Экспортировано: {tree_file}")
        except Exception as e:
            print(f"✗ Ошибка чтения {tree_file}: {e}")
    
    # Экспортируем users.json если есть
    users_path = os.path.join(DATA_DIR, 'users.json')
    if os.path.exists(users_path):
        try:
            with open(users_path, 'r', encoding='utf-8') as f:
                all_trees["users"] = json.load(f)
                print(f"✓ Экспортировано: users.json")
        except Exception as e:
            print(f"✗ Ошибка чтения users.json: {e}")
    
    # Сохраняем резервную копию
    backup_filename = f"backup_all_trees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = os.path.join(DATA_DIR, backup_filename)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(all_trees, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Резервная копия сохранена: {backup_path}")
    print(f"   Деревьев: {len(all_trees['trees'])}")
    print(f"   Пользователей: {len(all_trees['users'].get('users', {}))}")
    
    return backup_path

if __name__ == "__main__":
    export_trees()
