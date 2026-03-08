#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для наведения порядка в структуре проекта"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

# Создаём папки
print("Создание папок...")
(DATA_DIR := ROOT / "data").mkdir(exist_ok=True)
(OLD_VERSIONS := ROOT / "_old_versions").mkdir(exist_ok=True)

# Перемещаем старые версии
print("\nПеремещение старых версий...")
for item in ROOT.iterdir():
    if item.is_dir() and item.name.startswith("FamilyTree_"):
        shutil.move(str(item), str(OLD_VERSIONS / item.name))
        print(f"  - {item.name}")

# Перемещаем архив
if (ROOT / "_archive").exists():
    shutil.move(str(ROOT / "_archive"), str(OLD_VERSIONS / "_archive"))
    print("  - _archive")

# Удаляем временные файлы Python
print("\nОчистка временных файлов...")
pycache = ROOT / "__pycache__"
if pycache.exists():
    shutil.rmtree(pycache)
    print("  - __pycache__")

# Перемещаем файлы данных
print("\nПеремещение файлов данных...")
data_files = [
    "family_tree_*.json",
    "users.json",
    "palette.json",
    "window_settings.json",
    "login_remember.json"
]

for pattern in data_files:
    for file in ROOT.glob(pattern):
        shutil.move(str(file), str(DATA_DIR / file.name))
        print(f"  - {file.name}")

print("\n✅ Готово!")
print("\nСтруктура проекта:")
print("  /data - файлы данных")
print("  /_old_versions - старые версии")
print("  /Дерево - desktop приложение")
print("  /web - веб приложение")
print("  /docs - документация")
print("  /tests - тесты")
print("  /scripts - вспомогательные скрипты")
