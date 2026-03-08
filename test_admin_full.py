# -*- coding: utf-8 -*-
"""
Тест админ-панели с подробными логами.
Запускается ОТДЕЛЬНО от основного приложения.
"""

import sys
import io
import json
import traceback
from pathlib import Path

# Настраиваем вывод
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("ТЕСТ АДМИН-ПАНЕЛИ - ПОДРОБНЫЕ ЛОГИ")
print("=" * 70)

# === ШАГ 1: Проверка путей ===
print("\n[ШАГ 1] Проверка путей...")

script_dir = Path(__file__).parent
derevo_dir = script_dir / "Дерево"
data_dir = script_dir / "data"

print(f"  Папка проекта: {script_dir}")
print(f"  Папка Дерево: {derevo_dir} - {'✅' if derevo_dir.exists() else '❌'}")
print(f"  Папка data: {data_dir} - {'✅' if data_dir.exists() else '❌'}")

# === ШАГ 2: Поиск файлов данных ===
print("\n[ШАГ 2] Поиск файлов данных...")

found_files = []
if data_dir.exists():
    for f in data_dir.glob("family_tree*.json"):
        found_files.append(f)
        print(f"  ✅ {f.name}")
        
        # Пробуем прочитать
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            persons = len(data.get('persons', []))
            marriages = len(data.get('marriages', []))
            print(f"     Персон: {persons}, Семей: {marriages}")
        except Exception as e:
            print(f"     ❌ Ошибка чтения: {e}")

if not found_files:
    print("  ❌ Файлы не найдены!")
    print("\n  Проверьте что файлы лежат в:")
    print(f"  {data_dir}")

# === ШАГ 3: Тест загрузки модуля ===
print("\n[ШАГ 3] Загрузка модуля admin_dashboard_local...")

try:
    sys.path.insert(0, str(derevo_dir))
    from admin_dashboard_local import LocalAdminDashboard
    print("  ✅ Модуль загружен")
except Exception as e:
    print(f"  ❌ Ошибка загрузки: {e}")
    traceback.print_exc()
    input("\nНажмите Enter для выхода...")
    exit(1)

# === ШАГ 4: Тест создания панели ===
print("\n[ШАГ 4] Создание админ-панели...")

import tkinter as tk

try:
    root = tk.Tk()
    root.title("ТЕСТ")
    root.geometry("800x600")
    
    print("  ✅ Окно создано")
    
    # Создаём панель
    dashboard = LocalAdminDashboard(root, "Андрей Емельянов")
    print("  ✅ Панель создана")
    
    # Ждём немного для загрузки
    root.update()
    root.after(1000)
    root.update()
    
    print(f"\n[РЕЗУЛЬТАТ]")
    print(f"  Статус: {dashboard.status_var.get()}")
    print(f"  Персон: {len(dashboard.persons)}")
    print(f"  Семей: {len(dashboard.marriages)}")
    
    if dashboard.persons:
        print(f"\n  Первые 3 персоны:")
        for p in dashboard.persons[:3]:
            print(f"    - {p.get('surname', '')} {p.get('name', '')}")
    
    # Показываем окно
    print("\n[ОКНО ОТКРЫТО]")
    print("  Если вы видите окно с данными - тест УСПЕШЕН!")
    print("  Если окно пустое - смотрите логи выше")
    
    root.mainloop()
    
except Exception as e:
    print(f"  ❌ Ошибка: {e}")
    traceback.print_exc()
    input("\nНажмите Enter для выхода...")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 70)
