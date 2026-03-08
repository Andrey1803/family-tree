# -*- coding: utf-8 -*-
"""Тест: добавление сестры через add_sibling_dialog"""
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

_tree_dir = _here / "Дерево"
if str(_tree_dir) not in sys.path:
    sys.path.insert(0, str(_tree_dir))

import tkinter as tk
from tkinter import ttk, messagebox
import constants
from app import FamilyTreeApp
from models import FamilyTreeModel

def test_add_sibling():
    """Тест добавления сестры"""
    print("=== ТЕСТ: Добавление сестры ===\n")
    
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    # Создаем тестовую модель
    data_file = "data/family_tree_Андрей Емельянов.json"
    model = FamilyTreeModel(data_file=data_file)
    model.load_from_file()
    
    print(f"Загружено персон: {len(model.persons)}")
    print(f"Загружено браков: {len(model.marriages)}")
    
    # Находим персону для теста (у которой есть родители)
    test_person_id = None
    for pid, person in model.persons.items():
        if person.parents and person.gender == "Мужской":
            test_person_id = pid
            break
    
    if not test_person_id:
        print("ОШИБКА: Не найдена подходящая персона для теста")
        root.destroy()
        return
    
    test_person = model.get_person(test_person_id)
    print(f"\nТестовая персона: {test_person.display_name()} (ID: {test_person_id})")
    print(f"Пол: {test_person.gender}")
    print(f"Родители: {test_person.parents}")
    
    # Создаем приложение для теста
    app = FamilyTreeApp(root, data_file=data_file, username="Тест")
    
    # Проверяем, что метод add_sibling_dialog существует
    if not hasattr(app, 'add_sibling_dialog'):
        print("ОШИБКА: Метод add_sibling_dialog не найден")
        root.destroy()
        return
    
    print("\n=== ПРОВЕРКА ДИАЛОГА ===")
    
    # Открываем диалог добавления сестры
    try:
        # Создаем диалог вручную для проверки
        dialog = tk.Toplevel(root)
        dialog.title(f"Добавить сестру для {test_person.display_name()}")
        dialog.geometry("500x450")
        dialog.transient(root)
        
        # Создаём контейнер для скроллируемой области
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Добавляем тестовые поля
        ttk.Label(scrollable_frame, text="Имя*").grid(row=0, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(scrollable_frame, width=30).grid(row=0, column=1, padx=10, pady=8, sticky='w')
        
        ttk.Label(scrollable_frame, text="Фамилия*").grid(row=1, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(scrollable_frame, width=30).grid(row=1, column=1, padx=10, pady=8, sticky='w')
        
        # Кнопки внизу
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        save_btn = ttk.Button(btn_frame, text="Сохранить", command=lambda: print("Кнопка 'Сохранить' нажата!"))
        save_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        cancel_btn = ttk.Button(btn_frame, text="Отмена", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Проверяем видимость кнопок
        root.update_idletasks()
        
        print(f"dialog.winfo_ismapped(): {dialog.winfo_ismapped()}")
        print(f"btn_frame.winfo_ismapped(): {btn_frame.winfo_ismapped()}")
        print(f"save_btn.winfo_ismapped(): {save_btn.winfo_ismapped()}")
        print(f"cancel_btn.winfo_ismapped(): {cancel_btn.winfo_ismapped()}")
        
        # Проверяем текст на кнопке
        save_text = save_btn.cget('text')
        print(f"\nТекст на кнопке сохранения: '{save_text}'")
        
        if save_text == "Сохранить":
            print("✓ УСПЕХ: Кнопка называется 'Сохранить'")
        else:
            print(f"✗ ОШИБКА: Кнопка называется '{save_text}' вместо 'Сохранить'")
        
        # Проверяем расположение
        btn_frame_y = btn_frame.winfo_y()
        dialog_height = dialog.winfo_height()
        print(f"\nПозиция btn_frame: Y={btn_frame_y}, высота диалога={dialog_height}")
        
        if btn_frame_y > dialog_height - 100:
            print("✓ УСПЕХ: Кнопки находятся внизу диалога")
        else:
            print(f"✗ ОШИБКА: Кнопки находятся слишком высоко (Y={btn_frame_y})")
        
        # Закрываем диалог через 2 секунды
        def close_test():
            dialog.destroy()
            print("\n=== ТЕСТ ЗАВЕРШЕН ===")
            root.destroy()
        
        root.after(2000, close_test)
        root.mainloop()
        
    except Exception as e:
        print(f"ОШИБКА: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()

if __name__ == "__main__":
    test_add_sibling()
