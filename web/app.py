# -*- coding: utf-8 -*-
"""Flask-приложение «Семейное древо» (web-версия)."""

import hashlib
import json
import os
import sys

import zipfile
from io import BytesIO

from flask import Flask, request, jsonify, redirect, url_for, session, render_template, send_file, Response

_web_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_web_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "FamilyTreeWeb_SecretKey_ChangeInProduction")
app.config["JSON_AS_ASCII"] = False

# Папка данных. На Railway: DATA_DIR=/data (volume)
_data_dir = os.environ.get("DATA_DIR") or _project_root
USERS_FILE = os.path.join(_data_dir, "users.json")
AUTH_SALT = "FamilyTreeApp_Salt_v1"


def _password_hash(login: str, password: str) -> str:
    raw = (AUTH_SALT + login + password).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("users", {})
    except Exception:
        return {}


def _save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def auth_check(login: str, password: str) -> bool:
    if not (login or "").strip() or not password:
        return False
    users = _load_users()
    stored = users.get(login.strip())
    return bool(stored and _password_hash(login.strip(), password) == stored)


def auth_register(login: str, password: str):
    login = (login or "").strip()
    if not login:
        return "Введите логин."
    if not password:
        return "Введите пароль."
    if len(password) < 4:
        return "Пароль должен быть не короче 4 символов."
    users = _load_users()
    if login in users:
        return "Такой логин уже занят."
    users[login] = _password_hash(login, password)
    if not _save_users(users):
        return "Ошибка сохранения."
    return None


from tree_service import load_tree, save_tree, DATA_DIR

# Создать папку данных, если её нет (для Railway)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    github_repo = os.environ.get("GITHUB_REPO", "Andrey1803/family-tree")
    exe_filename = "Семейное_древо" + ".exe"  # расширение обязательно латиница
    return render_template("tree.html", username=session.get("username", "Гость"), github_repo=github_repo, exe_filename=exe_filename)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("index"))
        return render_template("login.html")
    login_val = (request.form.get("login") or "").strip()
    password_val = request.form.get("password") or ""
    guest = request.form.get("guest")
    if guest:
        session["username"] = "Гость"
        return redirect(url_for("index"))
    if not login_val:
        return render_template("login.html", error="Введите логин.")
    if not password_val:
        return render_template("login.html", error="Введите пароль.", login=login_val)
    if auth_check(login_val, password_val):
        session["username"] = login_val
        return redirect(url_for("index"))
    return render_template("login.html", error="Неверный логин или пароль.", login=login_val)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    login_val = (request.form.get("login") or "").strip()
    p1 = request.form.get("password") or ""
    p2 = request.form.get("password2") or ""
    if not login_val:
        return render_template("register.html", error="Введите логин.", login=login_val)
    if p1 != p2:
        return render_template("register.html", error="Пароли не совпадают.", login=login_val)
    err = auth_register(login_val, p1)
    if err:
        return render_template("register.html", error=err, login=login_val)
    return redirect(url_for("login"))


@app.route("/sw.js")
def service_worker():
    return app.send_static_file("sw.js"), 200, {"Service-Worker-Allowed": "/"}


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/api/tree", methods=["GET", "POST"])
def api_tree():
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    username = session["username"]
    if request.method == "GET":
        data = load_tree(username)
        # Нормализуем keys в persons
        persons = {str(k): v for k, v in data.get("persons", {}).items()}
        for p in persons.values():
            if isinstance(p, dict):
                for k in ("parents", "children", "spouse_ids"):
                    if k in p and isinstance(p[k], list):
                        p[k] = [str(x) for x in p[k]]
        cc = data.get("current_center")
        return jsonify({
            "persons": persons,
            "marriages": data.get("marriages", []),
            "current_center": str(cc) if cc is not None and str(cc) != "None" else None,
        })
    # POST — сохранить
    j = request.get_json() or {}
    persons = j.get("persons", {})
    marriages = j.get("marriages", [])
    current_center = j.get("current_center")
    out = {"persons": persons, "marriages": marriages, "current_center": current_center}
    if save_tree(username, out):
        return jsonify({"ok": True})
    return jsonify({"error": "Ошибка сохранения"}), 500


@app.route("/download/desktop")
def download_desktop():
    """Скачать Windows-версию: .exe (если собран) или ZIP с исходниками."""
    root_dir = os.path.normpath(os.path.join(_web_dir, ".."))
    bundle_dir = os.path.join(_web_dir, "desktop_bundle")
    exe_path = os.path.join(root_dir, "dist", "Семейное_древо.exe")

    if os.path.isfile(exe_path):
        # ZIP: exe + run_debug.bat (чтобы видеть ошибки при запуске)
        bat_content = (
            "@echo off\r\nchcp 65001 >nul\r\ncd /d \"%~dp0\"\r\n"
            "Семейное_древо.exe\r\necho.\r\npause\r\n"
        ).encode("utf-8")
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(exe_path, "Семейное_древо.exe")
            zf.writestr("run_debug.bat", bat_content)
        buf.seek(0)
        r = send_file(buf, mimetype="application/zip", as_attachment=True, download_name="Семейное_древо.zip")
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        return r
    # Fallback: ZIP с исходниками (из desktop_bundle или из корня проекта)
    use_bundle = os.path.isdir(bundle_dir)
    tree_dir = os.path.join(bundle_dir, "Дерево") if use_bundle else os.path.join(root_dir, "Дерево")
    main_py = os.path.join(bundle_dir, "main.py") if use_bundle else os.path.join(root_dir, "main.py")
    buf = BytesIO()
    bat_src = (
        "@echo off\r\nchcp 65001 >nul\r\ncd /d \"%~dp0\"\r\n"
        "if not exist main.py (\r\n"
        "  echo Ошибка: main.py не найден. Сначала РАСПАКУЙТЕ архив в папку (не запускайте из WinRAR).\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "python main.py\r\necho.\r\npause\r\n"
    ).encode("utf-8")
    readme_src = (
        "Семейное древо — Desktop (исходники)\r\n"
        "=====================================\r\n\r\n"
        "1. РАСПАКУЙТЕ архив в папку (ПКМ - Извлечь).\r\n"
        "   Не запускайте файлы прямо из WinRAR/архива!\r\n\r\n"
        "2. Запуск: дважды нажмите run_debug.bat\r\n"
        "   Требуется: Python 3.8+ (https://python.org)\r\n\r\n"
        "Чтобы получить .exe: на Windows запустите build_exe.bat из полного проекта с GitHub.\r\n"
    ).encode("utf-8")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme_src)
        zf.writestr("run_debug.bat", bat_src)
        if os.path.isfile(main_py):
            zf.write(main_py, "main.py")
        if os.path.isdir(tree_dir):
            for base, dirs, files in os.walk(tree_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    path = os.path.join(base, f)
                    arc = os.path.join("Дерево", os.path.relpath(path, tree_dir))
                    zf.write(path, arc)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name="Семейное_древо_source.zip")


@app.route("/api/photo/<person_id>")
def api_photo(person_id):
    """Возвращает фото персоны: из base64 или из photo_path."""
    if "username" not in session:
        return "", 401
    username = session["username"]
    data = load_tree(username)
    persons = data.get("persons", {})
    p = persons.get(str(person_id)) or persons.get(person_id)
    if not p:
        return "", 404
    pd = p if isinstance(p, dict) else (getattr(p, "__dict__", {}) or {})
    photo_b64 = pd.get("photo")
    photo_path = pd.get("photo_path", "")
    if photo_b64 and isinstance(photo_b64, str) and photo_b64.strip():
        import base64
        try:
            raw = base64.b64decode(photo_b64.strip())
            mt = "image/png" if raw[:4] == b"\x89PNG" else "image/jpeg"
            return Response(raw, mimetype=mt)
        except Exception:
            return "", 404
    if photo_path and isinstance(photo_path, str) and photo_path.strip():
        path = photo_path.strip()
        if not os.path.isabs(path):
            path = os.path.join(_data_dir, path)
        if os.path.isfile(path):
            try:
                ext = os.path.splitext(path)[1].lower()
                mime = "image/png" if ext == ".png" else "image/gif" if ext == ".gif" else "image/jpeg"
                return send_file(path, mimetype=mime)
            except Exception:
                return "", 404
    return "", 404


def _get_lan_ip():
    """IP для доступа с других устройств в локальной сети."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


if __name__ == "__main__":
    lan_ip = _get_lan_ip()
    if lan_ip:
        print(f"Доступ с других устройств в сети: http://{lan_ip}:5000")
    app.run(host="0.0.0.0", debug=True, port=5000)
