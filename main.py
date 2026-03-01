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
            # .exe: данные в папке data/ рядом с exe, скрипты — во временной папке PyInstaller
            _base_dir = os.path.dirname(sys.executable)
            _script_root = sys._MEIPASS
        else:
            # Запуск из исходников: данные в data/, скрипты в папке проекта
            _base_dir = os.path.dirname(os.path.abspath(__file__))
            _script_root = _base_dir
        os.chdir(_base_dir)  # Рабочая папка — корень проекта
        
        # Папка с данными (users.json, family_tree_*.json)
        _data_root = os.path.join(_base_dir, "data")
        if not os.path.isdir(_data_root):
            os.makedirs(_data_root, exist_ok=True)
        
        _inner = os.path.join(_script_root, "Дерево")
        if not os.path.isdir(_inner):
            raise FileNotFoundError(f"Папка Дерево не найдена: {_inner}")
        if _inner not in sys.path:
            sys.path.insert(0, _inner)

        # Добавляем папку проекта в sys.path для импорта модулей (export_pdf и др.)
        if _data_root not in sys.path:
            sys.path.insert(0, _data_root)

        # === ЗАГРУЖАЕМ ПАЛИТРУ ===
        import constants
        _loaded_palette = constants.load_palette_from_file()
        if _loaded_palette:
            constants.apply_palette(_loaded_palette)
            # Принудительно устанавливаем все цвета
            for key, value in _loaded_palette.items():
                if hasattr(constants, key):
                    setattr(constants, key, value)
        # === /ЗАГРУЖАЕМ ПАЛИТРУ ===

        # Запускаем приложение
        sys.path.insert(0, _inner)
        import main as tree_main
        tree_main.main()
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        _show_error(f"{type(e).__name__}: {e}", tb)
        if getattr(sys, "frozen", False):
            input("\nНажмите Enter для выхода...")
        raise
