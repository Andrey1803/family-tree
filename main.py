# -*- coding: utf-8 -*-
"""
Запуск приложения «Семейное древо».

Desktop: данные (users.json, family_tree_*.json) — в папке data/ рядом с main.py или .exe.
"""
import os
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


def _parse_args(args):
    """Разбирает аргументы командной строки.
    
    Поддерживаемые параметры:
        --tree-file <путь>  Путь к файлу дерева
        --username <имя>    Имя пользователя
    
    Returns:
        tuple: (tree_file, username)
    """
    tree_file = None
    username = None
    i = 0
    while i < len(args):
        if args[i] == '--tree-file' and i + 1 < len(args):
            tree_file = args[i + 1]
            i += 2
        elif args[i] == '--username' and i + 1 < len(args):
            username = args[i + 1]
            i += 2
        else:
            i += 1
    return tree_file, username


def _setup_paths(base_dir, script_root):
    """Настраивает пути для импорта модулей.
    
    Returns:
        tuple: (data_root, inner_path)
    """
    # Папка с данными (users.json, family_tree_*.json)
    data_root = os.path.join(base_dir, "data")
    if not os.path.isdir(data_root):
        os.makedirs(data_root, exist_ok=True)

    # Папка с приложением
    inner_path = os.path.join(script_root, "Дерево")
    if not os.path.isdir(inner_path):
        raise FileNotFoundError(f"Папка Дерево не найдена: {inner_path}")
    
    # Добавляем пути для импорта
    if inner_path not in sys.path:
        sys.path.insert(0, inner_path)
    if data_root not in sys.path:
        sys.path.insert(0, data_root)
    
    return data_root, inner_path


def _load_palette():
    """Загружает палитру цветов и применяет её.
    
    Returns:
        bool: True если палитра загружена, False иначе
    """
    try:
        import constants
        print(f"[MAIN] PALETTE_FILE = {constants.PALETTE_FILE}")
        loaded_palette = constants.load_palette_from_file()
        if loaded_palette:
            constants.apply_palette(loaded_palette)
            print(f"[MAIN] Применено {len(loaded_palette)} цветов из палитры")
            return True
        else:
            print(f"[MAIN] Палитра не загружена, используются значения по умолчанию")
            return False
    except Exception as e:
        print(f"[MAIN] Ошибка загрузки палитры: {e}")
        return False


if __name__ == "__main__":
    try:
        # Определяем базовые директории
        if getattr(sys, "frozen", False):
            # .exe: данные в папке data/ рядом с exe, скрипты — во временной папке PyInstaller
            base_dir = os.path.dirname(sys.executable)
            script_root = sys._MEIPASS
        else:
            # Запуск из исходников: данные в data/, скрипты в папке проекта
            base_dir = os.path.dirname(os.path.abspath(__file__))
            script_root = base_dir
        
        os.chdir(base_dir)  # Рабочая папка — корень проекта
        print(f"[MAIN] Base directory: {base_dir}")

        # Настраиваем пути
        data_root, inner_path = _setup_paths(base_dir, script_root)
        print(f"[MAIN] Data root: {data_root}")
        print(f"[MAIN] Inner path: {inner_path}")

        # Загружаем палитру
        _load_palette()

        # Разбираем аргументы командной строки
        tree_file, username = _parse_args(sys.argv[1:])
        if tree_file:
            print(f"[MAIN] Tree file: {tree_file}")
        if username:
            print(f"[MAIN] Username: {username}")

        # Запускаем приложение
        import main as tree_main
        tree_main.main(data_file=tree_file, username=username)

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        _show_error(f"{type(e).__name__}: {e}", tb)
        if getattr(sys, "frozen", False):
            input("\nНажмите Enter для выхода...")
        raise
