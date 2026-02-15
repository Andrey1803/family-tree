# -*- coding: utf-8 -*-
"""Регистрация URL-протокола derevo:// для Windows."""

import sys
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

PROTOCOL = "derevo"
PROTOCOL_NAME = "Семейное древо"


def _is_frozen():
    """True, если приложение запущено из .exe (PyInstaller)."""
    return getattr(sys, "frozen", False)


def _get_main_path():
    """Путь к main.py в корне проекта."""
    here = Path(__file__).resolve().parent
    root = here.parent  # корень проекта (родитель Дерево)
    return root / "main.py"


def register_protocol():
    """Регистрирует протокол derevo:// в HKEY_CURRENT_USER (без прав админа)."""
    if winreg is None or sys.platform != "win32":
        return False
    if _is_frozen():
        # Запуск из .exe: путь к exe, аргумент %1 (URL) передастся в sys.argv
        exe_path = Path(sys.executable).resolve()
        cmd = f'"{exe_path}" "%1"'
    else:
        # Запуск из Python: python main.py "%1"
        main_py = _get_main_path()
        if not main_py.is_file():
            return False
        python_exe = Path(sys.executable).resolve().as_posix()
        main_str = str(main_py.resolve()).replace("/", "\\")
        cmd = f'"{python_exe}" "{main_str}" "%1"'
    try:
        base = winreg.HKEY_CURRENT_USER
        key_path = f"Software\\Classes\\{PROTOCOL}"
        with winreg.CreateKey(base, key_path) as k:
            winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"URL:{PROTOCOL_NAME} Protocol")
        with winreg.CreateKey(base, f"{key_path}\\shell\\open\\command") as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, cmd)
        return True
    except Exception:
        return False


def get_launch_url():
    """Если приложение запущено по протоколу derevo://, возвращает переданный URL."""
    for arg in sys.argv[1:]:
        if arg.startswith("derevo://"):
            return arg
    return None
