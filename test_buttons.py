# -*- coding: utf-8 -*-
"""Тест: проверка видимости кнопок в диалоге"""
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Тест кнопок")
root.geometry("450x600")

# Создаём скроллируемый фрейм (как в add_person_dialog)
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Добавляем поля формы
for i in range(20):
    ttk.Label(scrollable_frame, text=f"Поле {i}").grid(row=i, column=0, padx=10, pady=8, sticky='e')
    ttk.Entry(scrollable_frame, width=30).grid(row=i, column=1, padx=10, pady=8, sticky='w')

# Кнопки внизу
btn_frame = ttk.Frame(root)
btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

print(f"btn_frame создан в: {btn_frame.master}")
print(f"root.winfo_children(): {root.winfo_children()}")
print(f"btn_frame.winfo_children(): {btn_frame.winfo_children()}")

ttk.Button(btn_frame, text="Сохранить", command=lambda: print("Сохранить нажата")).pack(side=tk.LEFT, padx=5)
ttk.Button(btn_frame, text="Отмена", command=root.destroy).pack(side=tk.LEFT, padx=5)

# Проверка видимости кнопок через 1 секунду
def check_buttons():
    print(f"\n=== Проверка через 1 секунду ===")
    print(f"btn_frame.winfo_ismapped(): {btn_frame.winfo_ismapped()}")
    for child in btn_frame.winfo_children():
        print(f"{child.cget('text')}: winfo_ismapped={child.winfo_ismapped()}, winfo_viewable={child.winfo_viewable()}")
    print(f"btn_frame.winfo_geometry(): {btn_frame.winfo_geometry()}")
    print(f"root.winfo_geometry(): {root.winfo_geometry()}")

root.after(1000, check_buttons)
root.mainloop()
