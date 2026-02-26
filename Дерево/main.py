# -*- coding: utf-8 -*-
"""
Точка входа приложения «Семейное древо».
Запуск: python main.py (из папки Дерево)
"""
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


def main():
    """Запуск приложения."""
    def start_app(username):
        root = tk.Tk()

        # Применяем цвета из загруженной палитры
        _apply_ui_colors(root)

        data_file = f"family_tree_{username}.json"
        app = FamilyTreeApp(root, data_file=data_file, username=username)
        
        # Принудительно применяем цвета ПОСЛЕ создания FamilyTreeApp
        _apply_ui_colors(root)
        if hasattr(app, 'canvas'):
            app.canvas.config(bg=constants.CANVAS_BG)
        
        root.protocol("WM_DELETE_WINDOW", app.on_exit)
        root.mainloop()

    run_login_window(start_app)


def _apply_ui_colors(root):
    """Применяет цвета палитры к интерфейсу."""
    style = ttk.Style()
    
    # Фон окна
    root.configure(bg=constants.WINDOW_BG)
    
    # Сохраняем палитру для использования в FamilyTreeApp
    root.ui_palette = {k: getattr(constants, k, v) for k, v in constants.PALETTE_DEFAULTS.items()}


if __name__ == "__main__":
    main()
