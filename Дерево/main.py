# -*- coding: utf-8 -*-
"""
Точка входа приложения «Семейное древо».
Запуск: python main.py (из папки Дерево)
"""
import sys
from pathlib import Path

# Папка этого скрипта — первая в пути (чтобы не импортировался Flask app из site-packages)
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

import tkinter as tk

import constants
from app import FamilyTreeApp
from auth import run_login_window


def main():
    def start_app(username):
        loaded = constants.load_palette_from_file()
        if loaded:
            constants.apply_palette(loaded)
        root = tk.Tk()
        data_file = f"family_tree_{username}.json"
        app = FamilyTreeApp(root, data_file=data_file, username=username)
        root.protocol("WM_DELETE_WINDOW", app.on_exit)
        root.mainloop()

    run_login_window(start_app)


if __name__ == "__main__":
    main()
