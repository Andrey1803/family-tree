# -*- coding: utf-8 -*-
"""
Запуск приложения «Семейное древо».

Desktop: данные (users.json, family_tree_*.json) — в папке с main.py или с .exe.
"""
import os
import runpy
import sys
import traceback


def _show_error(msg: str, full_traceback: str = ""):
    """Показать ошибку (для .exe, когда нет консоли)."""
    try:
        log_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        if full_traceback:
            log_path = os.path.join(log_dir, "error_log.txt")
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(full_traceback)
                msg = f"{msg}\n\nПодробности: error_log.txt"
            except Exception:
                pass
        if len(msg) > 800:
            msg = msg[:800] + "\n...(обрезано)"
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка запуска", msg)
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        if getattr(sys, "frozen", False):
            # .exe: данные рядом с exe, скрипты — во временной папке PyInstaller
            _data_root = os.path.dirname(sys.executable)
            _script_root = sys._MEIPASS
        else:
            _data_root = _script_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(_data_root)  # данные (users.json, family_tree_*.json) — в папке проекта/exe
        _inner = os.path.join(_script_root, "Дерево")
        if not os.path.isdir(_inner):
            raise FileNotFoundError(f"Папка Дерево не найдена: {_inner}")
        if _inner not in sys.path:
            sys.path.insert(0, _inner)
        runpy.run_path(os.path.join(_inner, "main.py"), run_name="__main__")
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        _show_error(f"{type(e).__name__}: {e}", tb)
        if getattr(sys, "frozen", False):
            input("\nНажмите Enter для выхода...")
        raise
