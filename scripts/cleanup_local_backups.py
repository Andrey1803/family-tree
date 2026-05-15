# -*- coding: utf-8 -*-
"""Удаляет локальные папки FamilyTree_v* (не в git). Освобождает сотни МБ."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for folder in sorted(root.glob("FamilyTree_v*")):
    if folder.is_dir():
        print(f"Removing {folder.name}...")
        shutil.rmtree(folder, ignore_errors=True)
print("Done.")
