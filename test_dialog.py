# -*- coding: utf-8 -*-
"""Проверка диалогов добавления родственников"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

def test_dialog():
    """Тест диалога с кнопками внизу"""
    root = tk.Tk()
    root.title("Тест диалога")
    root.geometry("400x300")
    
    dialog = tk.Toplevel(root)
    dialog.title("Диалог добавления")
    dialog.geometry("500x400")
    
    # Прокручиваемая область
    main_frame = ttk.Frame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Много полей для проверки прокрутки
    for i in range(20):
        ttk.Label(scrollable_frame, text=f"Поле {i+1}").grid(row=i, column=0, padx=10, pady=5)
        ttk.Entry(scrollable_frame, width=30).grid(row=i, column=1, padx=10, pady=5)
    
    # Кнопки внизу (вне прокручиваемой области)
    button_frame = ttk.Frame(dialog)
    button_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    ttk.Button(button_frame, text="Сохранить", command=lambda: messagebox.showinfo("OK", "Сохранено!")).pack(side=tk.LEFT, padx=10, pady=10)
    ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10, pady=10)
    
    # Делаем диалог модальным
    dialog.transient(root)
    dialog.grab_set()
    
    root.mainloop()

if __name__ == "__main__":
    test_dialog()
