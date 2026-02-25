# -*- coding: utf-8 -*-
"""Тест центрирования детей под родителями. Запуск: python test_recenter.py (из папки Дерево)"""
import sys
import os
from pathlib import Path

_here = Path(__file__).resolve().parent
_inner = _here / "Дерево"
if _inner.exists():
    os.chdir(str(_inner))  # данные в папке Дерево
    sys.path.insert(0, str(_inner))
else:
    sys.path.insert(0, str(_here))

import tkinter as tk
from app import FamilyTreeApp


def test_layout():
    root = tk.Tk()
    root.withdraw()
    try:
        app = FamilyTreeApp(root)
        app.calculate_layout(skip_centering=True)
        n = len(app.coords)
        print(f"Layout OK: {n} persons placed")
        root.destroy()
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()
        return False


if __name__ == "__main__":
    ok = test_layout()
    sys.exit(0 if ok else 1)
