# -*- coding: utf-8 -*-
"""Авторизация: вход, регистрация, хранение пользователей."""

import hashlib
import json
import os
import webbrowser
from pathlib import Path
from typing import Dict, Optional

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# Путь к файлу пользователей: в папке data/ (как указано в main.py)
# При запуске из .exe: data/ рядом с exe
# При запуске из исходников: data/ в корне проекта
# На сервере Railway: /app/data/users.json
USERS_FILE = "data/users.json"
# Используем правильный путь для файла запоминания (в той же директории, где и auth.py)
REMEMBER_FILE = Path(__file__).parent / "login_remember.json"
AUTH_SALT = "FamilyTreeApp_Salt_v1"


def _password_hash(login: str, password: str) -> str:
    raw = (AUTH_SALT + login + password).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _verify_password(login: str, password: str, stored_hash) -> bool:
    """Проверить пароль с поддержкой bcrypt и SHA256.
    
    stored_hash может быть:
    - строкой (bcrypt или SHA256 хеш)
    - словарём {"password": "...", "is_admin": true} (расширенный формат)
    """
    # Поддержка расширенного формата (словарь)
    if isinstance(stored_hash, dict):
        stored_hash = stored_hash.get("password", "")
        if not stored_hash:
            return False
    
    if stored_hash.startswith("$2"):
        # bcrypt хеш
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False
        return False
    else:
        # SHA256 хеш (локальный формат)
        return _password_hash(login, password) == stored_hash


def _load_users() -> Dict[str, str]:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception:
        return {}


def _save_users(users: Dict[str, str]) -> bool:
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def auth_check(login: str, password: str) -> bool:
    if not login.strip() or not password:
        return False

    login_clean = login.strip()
    
    # Пробуем проверить на сервере синхронизации
    try:
        import urllib.request
        sync_url = "https://ravishing-caring-production-3656.up.railway.app"
        req = urllib.request.Request(
            f"{sync_url}/api/auth/login",
            data=json.dumps({"login": login_clean, "password": password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('token'):
                return True  # Успешный вход на сервере
            elif data.get('error'):
                # Сервер явно отверг пароль
                print(f"[AUTH] Server error: {data['error']}")
                return False
    except urllib.error.HTTPError as e:
        # HTTP ошибка (401, 403, etc.) — неверный логин/пароль
        try:
            error_data = json.loads(e.read().decode())
            print(f"[AUTH] HTTP Error {e.code}: {error_data.get('error', 'Unknown')}")
        except Exception:
            print(f"[AUTH] HTTP Error {e.code}")
        return False
    except urllib.error.URLError as e:
        # Проблема с подключением к серверу
        print(f"[AUTH] URL Error: {e.reason} — trying local")
        pass  # Пробуем локально
    except Exception as e:
        # Другие ошибки — пробуем локально
        print(f"[AUTH] Error: {type(e).__name__}: {e} — trying local")
        pass

    # Локальная проверка
    users = _load_users()
    stored = users.get(login_clean)
    if not stored:
        print(f"[AUTH] Local: user '{login_clean}' not found")
        return False
    result = _verify_password(login_clean, password, stored)
    print(f"[AUTH] Local: {'OK' if result else 'FAIL'}")
    return result


def _load_remember() -> Dict:
    """Загружает сохранённые логин/пароль (если галочка была включена)."""
    if not REMEMBER_FILE.exists():
        return {}
    try:
        with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get("remember"):
                return {"login": data.get("login", ""), "password": data.get("password", "")}
    except Exception:
        pass
    return {}


def _save_remember(login: str, password: str):
    """Сохраняет логин и пароль для автоподстановки."""
    try:
        with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump({"remember": True, "login": login, "password": password}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _clear_remember():
    """Очищает сохранённые данные (галочка снята)."""
    if REMEMBER_FILE.exists():
        try:
            REMEMBER_FILE.unlink()
        except Exception:
            pass


def auth_register(login: str, password: str) -> Optional[str]:
    login = login.strip()
    if not login:
        return "Введите логин."
    if not password:
        return "Введите пароль."
    if len(password) < 4:
        return "Пароль должен быть не короче 4 символов."
    
    # Пробуем зарегистрировать на сервере синхронизации
    try:
        import urllib.request
        sync_url = "https://ravishing-caring-production-3656.up.railway.app"
        req = urllib.request.Request(
            f"{sync_url}/api/auth/register",
            data=json.dumps({
                "login": login,
                "password": password,
                "email": f"{login}@local.com"
            }).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get('success') or data.get('token'):
                return None  # Успешно зарегистрирован на сервере
    except Exception:
        pass  # Ошибка сервера — пробуем локально
    
    # Локальная регистрация
    users = _load_users()
    if login in users:
        return "Такой логин уже занят."
    users[login] = _password_hash(login, password)
    if not _save_users(users):
        return "Ошибка сохранения учётных данных."
    return None


def run_login_window(on_success):
    """
    Показывает окно входа. При успешном входе вызывает on_success(login).
    """
    # Исправлено: абсолютный импорт вместо relative import
    import constants
    import update_check
    login_root = tk.Tk()
    login_root.configure(bg=constants.AUTH_BG)
    login_root.title("Вход — Семейное древо")
    login_root.geometry("336x252")
    login_root.resizable(False, False)
    # Стиль ttk в тон окна
    _style = ttk.Style()
    _style.configure('TFrame', background=constants.AUTH_BG)
    _style.configure('TLabel', background=constants.AUTH_BG, foreground='#2d2a26')

    frame = ttk.Frame(login_root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Логин", font=("Segoe UI", 10)).pack(anchor=tk.W)
    login_var = tk.StringVar()
    login_entry = ttk.Entry(frame, textvariable=login_var, width=28)
    login_entry.pack(fill=tk.X, pady=(0, 8))
    login_entry.focus_set()

    ttk.Label(frame, text="Пароль", font=("Segoe UI", 10)).pack(anchor=tk.W)
    password_var = tk.StringVar()
    password_entry = ttk.Entry(frame, textvariable=password_var, width=28, show="•")
    password_entry.pack(fill=tk.X, pady=(0, 8))

    remember_var = tk.BooleanVar(value=False)
    remembered = _load_remember()
    if remembered:
        login_var.set(remembered.get("login", ""))
        password_var.set(remembered.get("password", ""))
        remember_var.set(True)
    ttk.Checkbutton(frame, text="Запомнить логин и пароль", variable=remember_var).pack(anchor=tk.W, pady=(0, 12))

    def do_login():
        login = login_var.get().strip()
        password = password_var.get()
        if not login:
            messagebox.showwarning("Вход", "Введите логин.", parent=login_root)
            return
        if not password:
            messagebox.showwarning("Вход", "Введите пароль.", parent=login_root)
            return
        
        print(f"[LOGIN] Attempting login for: {login}")
        try:
            auth_result = auth_check(login, password)
            print(f"[LOGIN] auth_check returned: {auth_result}")
        except Exception as e:
            print(f"[LOGIN] auth_check raised: {type(e).__name__}: {e}")
            auth_result = False
        
        if auth_result:
            print(f"[LOGIN] Success for: {login}")
            if remember_var.get():
                _save_remember(login, password)
            else:
                _clear_remember()
            login_root.destroy()
            on_success(login)
        else:
            print(f"[LOGIN] Failed for: {login}")
            messagebox.showerror("Вход", "Неверный логин или пароль.", parent=login_root)

    def do_register():
        reg = tk.Toplevel(login_root)
        reg.configure(bg=constants.AUTH_BG)
        reg.title("Регистрация")
        reg.geometry("336x231")
        reg.transient(login_root)
        reg.grab_set()
        f = ttk.Frame(reg, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Логин").pack(anchor=tk.W)
        r_login_var = tk.StringVar(value=login_var.get())
        ttk.Entry(f, textvariable=r_login_var, width=28).pack(fill=tk.X, pady=(0, 10))
        ttk.Label(f, text="Пароль").pack(anchor=tk.W)
        r_pass_var = tk.StringVar()
        ttk.Entry(f, textvariable=r_pass_var, width=28, show="•").pack(fill=tk.X, pady=(0, 10))
        ttk.Label(f, text="Повторите пароль").pack(anchor=tk.W)
        r_pass2_var = tk.StringVar()
        ttk.Entry(f, textvariable=r_pass2_var, width=28, show="•").pack(fill=tk.X, pady=(0, 14))

        def submit_register():
            login = r_login_var.get().strip()
            p1, p2 = r_pass_var.get(), r_pass2_var.get()
            if not login:
                messagebox.showwarning("Регистрация", "Введите логин.", parent=reg)
                return
            if p1 != p2:
                messagebox.showerror("Регистрация", "Пароли не совпадают.", parent=reg)
                return
            err = auth_register(login, p1)
            if err:
                messagebox.showerror("Регистрация", err, parent=reg)
                return
            messagebox.showinfo("Регистрация", "Учётная запись создана. Войдите под своим логином.", parent=reg)
            login_var.set(login)
            reg.destroy()

        ttk.Button(f, text="Зарегистрироваться", command=submit_register).pack(pady=4)
        ttk.Button(f, text="Отмена", command=reg.destroy).pack(pady=2)

    def do_guest():
        login_root.destroy()
        on_success("Гость")

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(8, 0))
    ttk.Button(btn_frame, text="Войти", command=do_login).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="Регистрация", command=do_register).pack(side=tk.LEFT)
    ttk.Button(btn_frame, text="Войти без регистрации", command=do_guest).pack(side=tk.LEFT, padx=(8, 0))

    def on_closing():
        if messagebox.askokcancel("Выход", "Закрыть программу?", parent=login_root):
            login_root.destroy()
            login_root.quit()

    def _on_update_available(version, download_url):
        if messagebox.askyesno(
            "Обновление",
            f"Доступна новая версия {version}.\n\nОткрыть страницу скачивания?",
            parent=login_root,
        ):
            try:
                webbrowser.open(download_url)
            except Exception:
                pass

    login_root.protocol("WM_DELETE_WINDOW", on_closing)
    password_entry.bind("<Return>", lambda e: do_login())

    update_check.check_for_updates(
        constants.UPDATE_CHECK_URL,
        _on_update_available,
        login_root,
    )
    login_root.mainloop()
