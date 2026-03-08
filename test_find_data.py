# -*- coding: utf-8 -*-
"""Тест: Поиск данных пользователя"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path

print("=" * 60)
print("ТЕСТ: Поиск данных пользователя")
print("=" * 60)

# Пути для поиска
search_paths = [
    Path(__file__).parent / "Дерево" / "data",
    Path(__file__).parent / "data",
    Path(__file__).parent / "Дерево",
    Path(__file__).parent,
]

print("\n🔍 Поиск файлов...")

found_files = []
for search_path in search_paths:
    print(f"\n📁 Проверка: {search_path}")
    if not search_path.exists():
        print("   ❌ Не существует")
        continue
    
    # Ищем JSON файлы
    for json_file in search_path.glob("*.json"):
        if "family" in json_file.name.lower() or "tree" in json_file.name.lower():
            print(f"   ✅ Найдено: {json_file.name}")
            found_files.append(json_file)
            
            # Пробуем прочитать
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                persons = data.get('persons', [])
                marriages = data.get('marriages', [])
                print(f"      Персон: {len(persons)}")
                print(f"      Семей: {len(marriages)}")
            except Exception as e:
                print(f"      ❌ Ошибка чтения: {e}")

print("\n" + "=" * 60)
if found_files:
    print(f"✅ Найдено файлов: {len(found_files)}")
else:
    print("❌ Файлы не найдены")
    print("\nВозможно данные на сервере?")
    
print("=" * 60)
input("Нажмите Enter...")
