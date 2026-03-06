# -*- coding: utf-8 -*-
"""
Точка входа приложения «Семейное древо».
Запуск: python main.py (из папки Дерево)
"""
import os
import sys
from pathlib import Path

# Папка этого скрипта — первая в пути
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

# Добавляем родительскую папку для импорта модулей (export_pdf и др.)
_parent = _here.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

# Палитра УЖЕ загружена в корневом main.py, просто используем constants
import constants

import tkinter as tk
from tkinter import ttk
from app import FamilyTreeApp
from auth import run_login_window


def main(data_file=None, username=None):
    """Запуск приложения.
    
    Args:
        data_file: Путь к файлу дерева (опционально)
        username: Имя пользователя (опционально)
    """
    def start_app(username):
        root = tk.Tk()

        # Применяем цвета из загруженной палитры
        _apply_ui_colors(root)

        # Файл данных в папке data/ или указанный
        if data_file:
            # Используем указанный файл
            actual_data_file = data_file
        else:
            # Стандартный файл в папке data/
            actual_data_file = os.path.join("data", f"family_tree_{username}.json")
        
        app = FamilyTreeApp(root, data_file=actual_data_file, username=username)

        # Принудительно применяем цвета ПОСЛЕ создания FamilyTreeApp
        _apply_ui_colors(root)
        if hasattr(app, 'canvas'):
            app.canvas.config(bg=constants.CANVAS_BG)

        root.protocol("WM_DELETE_WINDOW", app.on_exit)
        root.mainloop()

    # Если username передан напрямую (из админ-панели), запускаем без окна входа
    if username:
        start_app(username)
    else:
        run_login_window(start_app)


def _apply_ui_colors(root):
    """Применяет цвета палитры к интерфейсу."""
    style = ttk.Style()

    # Фон окна
    root.configure(bg=constants.WINDOW_BG)
    
    # Применяем цвета к стилям ttk
    style.configure('TFrame', background=constants.WINDOW_BG)
    style.configure('TLabel', background=constants.WINDOW_BG, foreground='#1e293b')
    style.configure('TButton', background=constants.MENUBAR_BG, foreground='#1e293b')
    style.configure('TMenubutton', background=constants.MENUBAR_BG, foreground='#1e293b')
    style.configure('Horizontal.TScale', background=constants.WINDOW_BG)
    style.configure('Vertical.TScale', background=constants.WINDOW_BG)

    # Сохраняем палитру для использования в FamilyTreeApp
    root.ui_palette = {k: getattr(constants, k, v) for k, v in constants.PALETTE_DEFAULTS.items()}


if __name__ == "__main__":
    main()
