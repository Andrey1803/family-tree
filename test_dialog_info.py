# -*- coding: utf-8 -*-
"""Тест: сбор информации о диалоге add_sibling_dialog"""
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

_tree_dir = _here / "Дерево"
if str(_tree_dir) not in sys.path:
    sys.path.insert(0, str(_tree_dir))

import tkinter as tk
from tkinter import ttk
import constants
from app import FamilyTreeApp
from models import FamilyTreeModel
import inspect

def collect_info():
    """Сбор информации о приложении и диалоге"""
    print("=" * 60)
    print("SBOR INFORMATSII O PRILOZHENII")
    print("=" * 60)
    
    # 1. Проверяем, какой файл app.py используется
    import app as app_module
    print(f"\n1. Fail app.py: {app_module.__file__}")
    
    # 2. Проверяем исходный код add_sibling_dialog
    print("\n2. Proverka koda add_sibling_dialog:")
    src = inspect.getsource(FamilyTreeApp.add_sibling_dialog)
    
    # Ищем создание btn_frame
    if 'btn_frame = ttk.Frame(dialog)' in src:
        idx = src.index('btn_frame = ttk.Frame(dialog)')
        lines_before = src[:idx].count('\n')
        lines_after = src[idx:].count('\n')
        print(f"   [OK] btn_frame создан (stroka {lines_before + 1} iz {lines_before + lines_after + 1})")
    else:
        print("   [ERR] btn_frame NE naiden v kode!")
    
    # Ищем pack для btn_frame
    if 'btn_frame.pack(' in src:
        idx = src.index('btn_frame.pack(')
        lines_before = src[:idx].count('\n')
        print(f"   [OK] btn_frame.pack() naiden (stroka {lines_before + 1})")
        # Показываем контекст
        context_start = src.rfind('\n', 0, idx - 50)
        context_end = src.find('\n', idx + 50)
        print(f"   Kontekst: {src[context_start+1:context_end].strip()}")
    else:
        print("   [ERR] btn_frame.pack() NE naiden!")
    
    # Ищем кнопки
    if 'text="Сохранить"' in src:
        idx = src.index('text="Сохранить"')
        lines_before = src[:idx].count('\n')
        print(f"   [OK] Knopka 'Soхранit'' naidena (stroka {lines_before + 1})")
    else:
        print("   [ERR] Knopka 'Soхранit'' NE naidena!")
    
    # 3. Проверяем порядок создания виджетов
    print("\n3. Poriadok sozdaniia vidzhetov v add_sibling_dialog:")
    widget_order = []
    for line in src.split('\n'):
        if 'scroll_container = ' in line or 'btn_frame = ' in line or 'dialog = ' in line:
            widget_order.append(line.strip())
    for i, w in enumerate(widget_order[:5]):
        print(f"   {i+1}. {w}")
    
    # 4. Создаем тестовый диалог и проверяем видимость
    print("\n4. Testirovanie vidimosti knopok:")
    
    root = tk.Tk()
    root.withdraw()
    
    # Создаем тестовое приложение
    data_file = "data/family_tree_Андрей Емельянов.json"
    app = FamilyTreeApp(root, data_file=data_file, username="Тест")
    
    # Находим тестовую персону
    test_person_id = None
    for pid, person in app.model.persons.items():
        if person.parents and person.gender == "Мужской":
            test_person_id = pid
            break
    
    if test_person_id:
        person = app.model.get_person(test_person_id)
        print(f"   Testovaia persona: {person.display_name()} (ID: {test_person_id})")
        
        # Открываем диалог
        dialog = tk.Toplevel(root)
        dialog.title(f"Dobavit' sestru dlia {person.display_name()}")
        dialog.geometry("500x450")
        
        # Sozdaem btn_frame PERVYM
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Sozdaem scroll_container VTORYM
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_container)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Dobavliaem testovye polia
        frame = ttk.Frame(scrollable_frame, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Imia*").grid(row=0, column=0)
        ttk.Entry(frame, width=30).grid(row=0, column=1)
        
        # Dobavliaem knopki
        save_btn = ttk.Button(btn_frame, text="Soхранit'", command=lambda: None)
        save_btn.pack(side=tk.LEFT, padx=10, pady=10)
        cancel_btn = ttk.Button(btn_frame, text="Otmena", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Obnovliaem geometriiu
        dialog.update_idletasks()
        
        # Proveriaem vidimost'
        print(f"\n   Dialog:")
        print(f"   - winfo_ismapped(): {dialog.winfo_ismapped()}")
        print(f"   - winfo_width(): {dialog.winfo_width()}")
        print(f"   - winfo_height(): {dialog.winfo_height()}")
        
        print(f"\n   btn_frame:")
        print(f"   - winfo_ismapped(): {btn_frame.winfo_ismapped()}")
        print(f"   - winfo_x(): {btn_frame.winfo_x()}")
        print(f"   - winfo_y(): {btn_frame.winfo_y()}")
        print(f"   - winfo_width(): {btn_frame.winfo_width()}")
        print(f"   - winfo_height(): {btn_frame.winfo_height()}")
        
        print(f"\n   scroll_container:")
        print(f"   - winfo_ismapped(): {scroll_container.winfo_ismapped()}")
        print(f"   - winfo_y(): {scroll_container.winfo_y()}")
        print(f"   - winfo_height(): {scroll_container.winfo_height()}")
        
        print(f"\n   Кнопка 'Сохранить':")
        print(f"   - winfo_ismapped(): {save_btn.winfo_ismapped()}")
        print(f"   - winfo_x(): {save_btn.winfo_x()}")
        print(f"   - winfo_y(): {save_btn.winfo_y()}")
        
        # Проверяем, перекрывается ли btn_frame
        btn_y = btn_frame.winfo_y()
        scroll_y = scroll_container.winfo_y()
        scroll_height = scroll_container.winfo_height()
        
        print(f"\n   Позиционирование:")
        print(f"   - btn_frame.y = {btn_y}")
        print(f"   - scroll_container.y = {scroll_y}")
        print(f"   - scroll_container.height = {scroll_height}")
        print(f"   - scroll_container.bottom = {scroll_y + scroll_height}")
        
        if btn_y >= scroll_y + scroll_height:
            print(f"   [OK] Knopki NE perekryvaiutsia skroll-oblastiu")
        else:
            print(f"   [ERR] Knopki PEREKRYVAIUTSIA skroll-oblastiu!")
        
        # Сохраняем скриншот структуры
        def print_widget_tree(widget, indent=0):
            result = []
            result.append("  " * indent + f"{type(widget).__name__}: x={widget.winfo_x()}, y={widget.winfo_y()}, w={widget.winfo_width()}, h={widget.winfo_height()}, mapped={widget.winfo_ismapped()}")
            for child in widget.winfo_children():
                result.extend(print_widget_tree(child, indent + 1))
            return result
        
        print(f"\n   Дерево виджетов диалога:")
        for line in print_widget_tree(dialog):
            print(f"   {line}")
        
        # Закрываем через 3 секунды
        def close():
            dialog.destroy()
            root.destroy()
            print("\n" + "=" * 60)
            print("TEST ZAVERSHEN")
            print("=" * 60)
        
        root.after(3000, close)
        root.mainloop()
    else:
        print(f"   [OK] Ne naidena testovaia persona")
        root.destroy()

if __name__ == "__main__":
    collect_info()
