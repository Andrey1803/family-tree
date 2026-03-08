# -*- coding: utf-8 -*-
"""Тест: проверка диалога добавления персоны"""
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

# Загружаем модули
import constants
from app import FamilyTreeApp

def test_dialog():
    root = tk.Tk()
    root.title("Тест диалога")
    root.geometry("800x600")
    
    # Применяем цвета
    root.configure(bg=constants.WINDOW_BG)
    
    # Создаем приложение
    app = FamilyTreeApp(root, data_file="data/family_tree_Андрей Емельянов.json", username="Тест")
    
    # Ждем 2 секунды и открываем диалог
    def open_dialog():
        print("=== ОТКРЫВАЕМ ДИАЛОГ ===")
        app.add_person_dialog()
        print("Диалог открыт")
        
        # Проверяем, видны ли кнопки
        def check_buttons():
            dialog = root.winfo_children()[-1]  # Последний созданный виджет - диалог
            print(f"\n=== ПРОВЕРКА ДИАЛОГА ===")
            print(f"Dialog type: {type(dialog)}")
            print(f"Dialog children: {dialog.winfo_children()}")
            
            for i, child in enumerate(dialog.winfo_children()):
                print(f"  Child {i}: {type(child).__name__}, mapped={child.winfo_ismapped()}")
                if isinstance(child, ttk.Frame):
                    print(f"    Frame children: {child.winfo_children()}")
                    for j, subchild in enumerate(child.winfo_children()):
                        print(f"      Subchild {j}: {type(subchild).__name__}, mapped={subchild.winfo_ismapped()}")
                        if hasattr(subchild, 'cget'):
                            try:
                                text = subchild.cget('text')
                                if text:
                                    print(f"        Text: '{text}'")
                            except:
                                pass
            
            # Ищем кнопки
            all_buttons = []
            def find_buttons(widget, level=0):
                if isinstance(widget, (ttk.Button, tk.Button)):
                    try:
                        text = widget.cget('text')
                        all_buttons.append((level, text, widget.winfo_ismapped()))
                    except:
                        pass
                for child in widget.winfo_children():
                    find_buttons(child, level+1)
            
            find_buttons(dialog)
            print(f"\n=== НАЙДЕННЫЕ КНОПКИ ===")
            for level, text, mapped in all_buttons:
                print(f"  Уровень {level}: '{text}' (видима: {mapped})")
        
        root.after(1500, check_buttons)
    
    root.after(2000, open_dialog)
    root.mainloop()

if __name__ == "__main__":
    test_dialog()
