# -*- coding: utf-8 -*-
"""Тест локальной админ-панели"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

print("=" * 60)
print("ТЕСТ: Локальная админ-панель")
print("=" * 60)

from pathlib import Path

# Проверяем путь к data
data_path = Path(__file__).parent.parent / "data"
print(f"\nПуть к data: {data_path}")
print(f"Существует: {data_path.exists()}")

if data_path.exists():
    files = list(data_path.glob("family_tree*.json"))
    print(f"Найдено файлов: {len(files)}")
    for f in files:
        print(f"  - {f.name}")

# Тестируем загрузку
print("\nЗагрузка файла...")
from admin_dashboard_local import LocalAdminDashboard
import tkinter as tk

root = tk.Tk()
root.withdraw()

dashboard = LocalAdminDashboard(root, "Андрей Емельянов")

print(f"Статус: {dashboard.status_var.get()}")
print(f"Персон загружено: {len(dashboard.persons)}")
print(f"Семей загружено: {len(dashboard.marriages)}")

if dashboard.persons:
    print("\nПервые 5 персон:")
    for p in dashboard.persons[:5]:
        print(f"  {p.get('surname')} {p.get('name')} ({p.get('gender')})")

print("\n" + "=" * 60)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 60)

root.destroy()
