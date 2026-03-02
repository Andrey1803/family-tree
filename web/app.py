# -*- coding: utf-8 -*-
"""Flask-приложение «Семейное древо» (web-версия)."""

import json
import os
import sys
import urllib.request
import secrets
import shutil
import base64
import logging
from datetime import datetime

import zipfile
from io import BytesIO

# Настройка логирования для Railway
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# Попытка импорта reportlab для PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from flask import Flask, request, jsonify, redirect, url_for, session, render_template, send_file, Response

_web_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_web_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Настройки сервера синхронизации
SYNC_SERVER_URL = os.environ.get("SYNC_SERVER_URL") or "https://ravishing-caring-production-3656.up.railway.app"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "FamilyTreeApp_Fixed_Secret_Key_2026"
app.config["JSON_AS_ASCII"] = False
app.config["SESSION_COOKIE_SECURE"] = False  # Разрешить HTTP
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Папка данных. На Railway: DATA_DIR=/data (volume)
# Если DATA_DIR не установлен — используем папку рядом с web/
if os.environ.get("DATA_DIR"):
    _data_dir = os.environ.get("DATA_DIR")
else:
    # Railway: рабочая папка /app, data лежит в /app/data
    # Локально: рабочая папка проекта, data лежит в ./data
    cwd = os.getcwd()
    if cwd == "/app":
        # Railway
        _data_dir = "/app/data"
    else:
        # Локально
        _data_dir = os.path.join(_web_dir, "..", "data")
    
# Файл пользователей
USERS_FILE = os.path.join(_data_dir, "users.json")

# Проверяем, есть ли файл, если нет — пробуем в корне проекта
if not os.path.exists(USERS_FILE):
    USERS_FILE = os.path.join(_project_root, "users.json")

# Версия хеширования для миграции
AUTH_SALT = "FamilyTreeApp_Salt_v1"


def _load_users():
    if not os.path.exists(USERS_FILE):
        print(f"[LOAD_USERS] File not found: {USERS_FILE}")
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            users = data.get("users", {})
            print(f"[LOAD_USERS] Loaded {len(users)} users from {USERS_FILE}")
            print(f"[LOAD_USERS] Keys: {list(users.keys())}")
            return users
    except Exception as e:
        print(f"[LOAD_USERS] Error: {e}")
        return {}


def _save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def is_admin(username: str) -> bool:
    """Проверяет, является ли пользователь администратором."""
    if not username:
        return False
    # Супер-админ
    if username == "admin":
        return True
    # Проверяем флаг is_admin в локальных пользователях
    users = _load_users()
    print(f"[IS_ADMIN] username='{username}', users_file={USERS_FILE}, exists={os.path.exists(USERS_FILE)}")
    print(f"[IS_ADMIN] loaded users: {list(users.keys())}")
    user_data = users.get(username, {})
    is_admin_result = isinstance(user_data, dict) and user_data.get("is_admin")
    print(f"[IS_ADMIN] user_data={user_data}, is_admin={is_admin_result}")
    if is_admin_result:
        return True
    return False


def _password_hash(login: str, password: str) -> str:
    """
    Хеширует пароль.
    
    Если bcrypt доступен — использует bcrypt.
    Иначе — fallback на SHA256 (для обратной совместимости).
    """
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback для обратной совместимости
        import hashlib
        raw = (AUTH_SALT + login + password).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def _get_user_password_hash(user_data):
    """Извлекает хеш пароля из данных пользователя."""
    if isinstance(user_data, dict):
        return user_data.get("password", "")
    return user_data  # Старый формат - просто строка с хешем


def _verify_password(login: str, password: str, stored_data) -> bool:
    """
    Проверяет пароль против хеша.

    Автоматически определяет тип хеша (bcrypt или legacy SHA256).
    stored_data может быть строкой (старый формат) или словарём (новый формат).
    """
    # Извлекаем хеш из данных пользователя
    stored_hash = _get_user_password_hash(stored_data)
    
    if stored_hash.startswith("$2"):
        # bcrypt хеш
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False
        else:
            # bcrypt недоступен, но хеш bcrypt — не можем проверить
            return False
    else:
        # Legacy SHA256 хеш
        import hashlib
        raw = (AUTH_SALT + login + password).encode("utf-8")
        computed = hashlib.sha256(raw).hexdigest()
        return computed == stored_hash


def auth_check(login: str, password: str) -> bool:
    """Проверить логин/пароль: сначала сервер, потом локально"""
    if not (login or "").strip() or not password:
        return False

    login_clean = (login or "").strip()
    
    # 1. Пробуем сервер синхронизации
    try:
        req = urllib.request.Request(
            f"{SYNC_SERVER_URL}/api/auth/login",
            data=json.dumps({"login": login_clean, "password": password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('token'):
                # Сохраняем токен в сессии
                session['server_token'] = data['token']
                session['server_user_id'] = data.get('user_id')
                print(f"[AUTH] Server login OK: {login_clean}")
                return True
            elif data.get('error'):
                print(f"[AUTH] Server error: {data['error']}")
                return False
    except urllib.error.HTTPError as e:
        # HTTP 401 — неверный пароль
        print(f"[AUTH] Server HTTP {e.code}: неверный логин/пароль")
        return False
    except urllib.error.URLError as e:
        print(f"[AUTH] Server URL Error: {e.reason} — trying local")
        pass  # Пробуем локально
    except Exception as e:
        print(f"[AUTH] Server Error: {type(e).__name__}: {e} — trying local")
        pass  # Пробуем локально

    # 2. Локальная проверка
    users = _load_users()
    stored = users.get(login_clean)
    if stored:
        result = _verify_password(login_clean, password, stored)
        print(f"[AUTH] Local {'OK' if result else 'FAIL'}: {login_clean}")
        if result:
            session['username'] = login_clean
        return result
    
    print(f"[AUTH] User not found: {login_clean}")
    return False


def auth_register(login: str, password: str):
    """Зарегистрировать пользователя ТОЛЬКО через сервер синхронизации"""
    login = (login or "").strip()
    if not login:
        return "Введите логин."
    if not password:
        return "Введите пароль."
    if len(password) < 4:
        return "Пароль должен быть не короче 4 символов."
    
    # Регистрируем ТОЛЬКО на сервере синхронизации
    try:
        req = urllib.request.Request(
            f"{SYNC_SERVER_URL}/api/auth/register",
            data=json.dumps({
                "login": login,
                "password": password,
                "email": f"{login}@local.com"
            }).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('success') or data.get('token') or data.get('message'):
                # Успешно зарегистрирован на сервере
                return None
            else:
                return data.get('message', 'Ошибка регистрации')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        if 'уже занят' in error_body or 'already' in error_body.lower():
            return "Такой логин уже занят."
        return f"Ошибка сервера: {e.code}"
    except Exception as e:
        return f"Ошибка подключения к серверу: {str(e)}"
    if not _save_users(users):
        return "Ошибка сохранения."
    return None


from tree_service import load_tree, save_tree, DATA_DIR

# Импортируем email сервис
try:
    from email_service import send_verification_code, verify_code, cleanup_expired_codes
except ImportError:
    # Если email_service не доступен
    def send_verification_code(email): return None
    def verify_code(email, code): return False
    def cleanup_expired_codes(): pass

# Создать папку данных, если её нет (для Railway)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass


try:
    from version import VERSION
except ImportError:
    VERSION = "1.0.0"


@app.route("/api/version")
def api_version():
    """Версия приложения и ссылка на скачивание (для desktop проверки обновлений)."""
    base = request.url_root.rstrip("/")
    return jsonify({
        "version": VERSION,
        "download_url": f"{base}/download/exe",
    })


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("tree.html", username=session.get("username", "Гость"))


@app.route("/download/exe")
def download_exe():
    """Прокси: скачивает Tree.zip с GitHub, отдаёт пользователю. Без перехода на GitHub."""
    github_repo = os.environ.get("GITHUB_REPO", "Andrey1803/family-tree")
    url = f"https://github.com/{github_repo}/releases/latest/download/Tree.zip"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        return Response(data, mimetype="application/zip", headers={
            "Content-Disposition": "attachment; filename=Tree.zip",
        })
    except Exception:
        return redirect(f"https://github.com/{github_repo}/releases/latest")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            # Админу сразу перенаправляем на админ-панель
            if is_admin(session["username"]):
                return redirect(url_for("admin_panel"))
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
        # Админу сразу перенаправляем на админ-панель
        if is_admin(login_val):
            # Для локальных администраторов пробуем получить токен сервера
            if not session.get('server_token'):
                try:
                    req = urllib.request.Request(
                        f"{SYNC_SERVER_URL}/api/auth/login",
                        data=json.dumps({"login": login_val, "password": password_val}).encode(),
                        headers={'Content-Type': 'application/json'},
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())
                        if data.get('token'):
                            session['server_token'] = data['token']
                            session['server_user_id'] = data.get('user_id')
                            print(f"[LOGIN] Admin {login_val} got server token")
                except Exception as e:
                    print(f"[LOGIN] Admin {login_val} local only: {e}")
            return redirect(url_for("admin_panel"))
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
    
    # После успешной регистрации — автоматически входим
    if auth_check(login_val, p1):
        session["username"] = login_val
        return redirect(url_for("index"))
    
    return redirect(url_for("login"))


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """API регистрация (принимает JSON)"""
    data = request.get_json() or {}
    login_val = (data.get("login") or "").strip()
    p1 = data.get("password") or ""
    p2 = data.get("password2") or p1
    
    if not login_val:
        return jsonify({"error": "Введите логин."}), 400
    if p1 != p2:
        return jsonify({"error": "Пароли не совпадают."}), 400
    
    err = auth_register(login_val, p1)
    if err:
        return jsonify({"error": err}), 400
    
    return jsonify({"message": "Пользователь успешно зарегистрирован"}), 200


@app.route("/api/auth/session", methods=["POST"])
def api_session():
    """Сохранить токен сессии после входа через сервер синхронизации"""
    data = request.get_json() or {}
    token = data.get('token')
    user_id = data.get('user_id')
    login = data.get('login')

    if token:
        session['server_token'] = token
        session['server_user_id'] = user_id
        if login:
            session['username'] = login

        # Проверяем, что токен работает
        # Для админа проверяем через /api/admin/stats, для остальных через /api/sync/download
        try:
            if login == 'admin':
                # Админ проверяется через admin/stats
                req = urllib.request.Request(
                    f"{SYNC_SERVER_URL}/api/admin/stats",
                    headers={'Authorization': f'Bearer {token}'},
                    method='GET'
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    stats = json.loads(resp.read().decode())
                    total_persons = stats.get('overview', {}).get('total_persons', 0)
                    print(f"[SESSION] Admin token OK, total persons on server: {total_persons}")
                    return jsonify({"ok": True, "persons": total_persons, "is_admin": True}), 200
            else:
                # Обычные пользователи через sync/download
                req = urllib.request.Request(
                    f"{SYNC_SERVER_URL}/api/sync/download",
                    headers={'Authorization': f'Bearer {token}'},
                    method='GET'
                )
                resp = urllib.request.urlopen(req, timeout=10)
                tree_data = json.loads(resp.read().decode())
                persons_count = len(tree_data.get('tree', {}).get('persons', {}))
                print(f"[SESSION] Token OK, persons: {persons_count}")
                return jsonify({"ok": True, "persons": persons_count}), 200
        except Exception as e:
            print(f"[SESSION] Token check failed: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "No token"}), 400


@app.route("/api/auth/login-local", methods=["POST"])
def api_login_local():
    """Локальный вход (для пользователей из users.json)"""
    data = request.get_json() or {}
    login_val = (data.get("login") or "").strip()
    password = data.get("password") or ""

    if not login_val or not password:
        return jsonify({"error": "Введите логин и пароль"}), 400

    if auth_check(login_val, password):
        session["username"] = login_val
        return jsonify({"ok": True}), 200

    return jsonify({"error": "Неверный логин или пароль"}), 401


@app.route("/api/auth/send-code", methods=["POST"])
def api_send_code():
    """Отправить код подтверждения на email."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    login = data.get('login', '').strip()

    logger.info(f"Запрос кода подтверждения для email: {email}")

    if not email:
        return jsonify({"error": "Введите email"}), 400

    # Проверяем формат email
    if '@' not in email or '.' not in email:
        return jsonify({"error": "Неверный формат email"}), 400

    # Проверяем, не занят ли email
    try:
        req = urllib.request.Request(
            f"{SYNC_SERVER_URL}/api/auth/check-email",
            data=json.dumps({"email": email}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            check_data = json.loads(resp.read().decode())
            if check_data.get('exists'):
                return jsonify({"error": "Этот email уже зарегистрирован"}), 400
    except Exception as e:
        logger.error(f"Ошибка проверки email: {e}")
        pass  # Игнорируем ошибки проверки

    # Отправляем код
    logger.info(f"Вызов send_verification_code для {email}")
    code = send_verification_code(email)

    if code:
        # Код отправлен на email (не показываем код на экране)
        logger.info(f"Код сгенерирован и отправлен на {email}")
        return jsonify({
            "message": "Код отправлен на email"
        }), 200
    else:
        logger.error("Ошибка при отправке кода")
        return jsonify({"error": "Ошибка отправки кода"}), 500


@app.route("/api/auth/verify-code", methods=["POST"])
def api_verify_code():
    """Проверить код подтверждения."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({"error": "Введите email и код"}), 400
    
    if verify_code(email, code):
        return jsonify({"message": "Код подтверждён"}), 200
    else:
        return jsonify({"error": "Неверный код или истёк срок действия"}), 400


@app.route("/sw.js")
def service_worker():
    return app.send_static_file("sw.js"), 200, {"Service-Worker-Allowed": "/"}


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/admin")
def admin_panel():
    """Панель администратора — только статистика и просмотр чужих деревьев."""
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # Проверяем права администратора
    if is_admin(username):
        return render_template("admin.html", username=username)

    # Проверяем через сервер синхронизации (если есть токен)
    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/stats",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                # Если запрос успешен - пользователь админ
                return render_template("admin.html", username=username)
        except Exception as e:
            print(f"[ADMIN] Access denied for {username}: {e}")

    # Доступ запрещён
    return render_template("admin.html", username=username), 403


def check_admin_access(username):
    """Проверяет права администратора через сервер или локально."""
    if not username:
        return False
    
    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/stats",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"[CHECK_ADMIN] {username} is admin via server")
                return True
        except Exception as e:
            print(f"[CHECK_ADMIN] Server check failed: {e}")
    
    # Fallback на локальную проверку
    result = is_admin(username)
    print(f"[CHECK_ADMIN] {username} is_admin={result} (local)")
    return result


@app.route("/api/admin/stats")
def api_admin_stats():
    """Статистика для админ-панели (прокси на сервер синхронизации)."""
    if "username" not in session:
        print(f"[API_ADMIN_STATS] No username in session")
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    print(f"[API_ADMIN_STATS] username='{username}'")
    # Проверяем права администратора
    if not check_admin_access(username):
        print(f"[API_ADMIN_STATS] User {username} is not admin")
        return jsonify({"error": "Требуется права администратора"}), 403
    print(f"[API_ADMIN_STATS] User {username} is admin, proceeding...")

    server_token = session.get('server_token')
    if not server_token:
        # Возвращаем локальную статистику
        return _get_local_stats()

    try:
        req = urllib.request.Request(
            f"{SYNC_SERVER_URL}/api/admin/stats",
            headers={'Authorization': f'Bearer {server_token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        print(f"[ADMIN] Stats from sync server failed: {e}")
        return _get_local_stats()


def _get_local_stats():
    """Локальная статистика (fallback)."""
    print("[STATS] Loading local stats...")
    users = _load_users()
    print(f"[STATS] Loaded {len(users)} users from {USERS_FILE}")
    total_persons = 0
    total_trees = 0

    for username in users.keys():
        tree_data = load_tree(username)
        persons_count = len(tree_data.get("persons", {}))
        print(f"[STATS] User {username}: {persons_count} persons")
        total_trees += 1
        total_persons += persons_count

    print(f"[STATS] Total: {total_trees} trees, {total_persons} persons")
    return jsonify({
        "overview": {
            "total_users": len(users),
            "active_users": len(users),
            "total_trees": total_trees,
            "total_persons": total_persons,
            "active_sessions": 1
        },
        "recent_users": [],
        "recent_syncs": [],
        "daily_stats": []
    })


@app.route("/api/admin/users")
def api_admin_users():
    """Список всех пользователей."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    if not check_admin_access(username):
        return jsonify({"error": "Требуется права администратора"}), 403

    # Пробуем загрузить с сервера синхронизации
    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/users",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                server_data = json.loads(response.read().decode())
                print(f"[ADMIN] Loaded users from sync server: {len(server_data.get('users', []))}")
                # Возвращаем данные с сервера
                return jsonify(server_data)
        except Exception as e:
            print(f"[ADMIN] Error loading users from sync server: {e}")
            # Fallback на локальные данные

    # Локальные данные (fallback)
    print("[ADMIN] Loading users from local file")
    users = _load_users()
    users_list = []

    for login, data in users.items():
        user_info = {
            "id": hash(login) % 10000,
            "login": login,
            "email": None,  # Заглушка для локальных пользователей
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True,
            "is_admin": is_admin(login)
        }
        users_list.append(user_info)

    print(f"[ADMIN] Loaded {len(users_list)} local users")
    return jsonify({"users": users_list})


@app.route("/api/admin/debug-users")
def api_admin_debug_users():
    """Отладка: проверить путь и загрузку пользователей."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован", "session_username": None}), 401
    
    username = session["username"]
    if not is_admin(username):
        return jsonify({"error": "Не админ", "session_username": username}), 403
    
    return jsonify({
        "users_file": USERS_FILE,
        "users_file_exists": os.path.exists(USERS_FILE),
        "data_dir": _data_dir,
        "project_root": _project_root,
        "server_token": session.get('server_token') is not None,
        "session_username": username,
        "session_username_repr": repr(username),
        "loaded_users": _load_users()
    })


@app.route("/api/check-session")
def api_check_session():
    """Проверка сессии."""
    username = session.get("username")
    server_token = session.get('server_token')
    
    print(f"[CHECK_SESSION] username={username}, repr={repr(username)}")
    print(f"[CHECK_SESSION] server_token={server_token is not None}")
    
    # Проверяем админа через сервер синхронизации, если есть токен
    is_admin_result = False
    if server_token and username:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/stats",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                is_admin_result = True
                print(f"[CHECK_SESSION] Admin via server: YES")
        except Exception as e:
            print(f"[CHECK_SESSION] Admin via server: NO - {e}")
    
    if not is_admin_result:
        is_admin_result = is_admin(username) if username else False
    
    return jsonify({
        "username": username,
        "username_type": str(type(username)),
        "is_admin": is_admin_result,
        "has_server_token": server_token is not None,
        "users_file": USERS_FILE,
        "users_file_exists": os.path.exists(USERS_FILE) if username else None
    })


@app.route("/api/admin/user/<int:user_id>/toggle", methods=["POST"])
def api_admin_toggle_user(user_id):
    """Активировать/деактивировать пользователя."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    if not check_admin_access(username):
        return jsonify({"error": "Требуется права администратора"}), 403

    # Для локальных пользователей просто возвращаем успех
    # Реальное управление через сервер синхронизации
    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/user/{user_id}/toggle",
                headers={'Authorization': f'Bearer {server_token}'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return jsonify({"message": "Статус пользователя изменён"})
        except Exception as e:
            print(f"[ADMIN] Toggle failed: {e}")

    return jsonify({"message": "Статус пользователя изменён (локально)"})


@app.route("/api/admin/user/<int:user_id>/delete", methods=["POST"])
def api_admin_delete_user(user_id):
    """Удалить пользователя (только супер-админ admin)."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    # Только супер-админ может удалять
    if username != "admin":
        return jsonify({"error": "Только супер-админ может удалять пользователей"}), 403

    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/user/{user_id}/delete",
                headers={'Authorization': f'Bearer {server_token}'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return jsonify({"message": "Пользователь удалён"})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return jsonify({"error": "Пользователь не найден на сервере"}), 404
            elif e.code == 403:
                return jsonify({"error": "Нет прав для удаления на сервере"}), 403
            else:
                print(f"[ADMIN] Delete HTTP error: {e.code}")
        except Exception as e:
            print(f"[ADMIN] Delete failed: {e}")

    # Локальное удаление (если пользователь в users.json)
    users = _load_users()
    # Находим пользователя по ID (хеш от login)
    target_login = None
    for login, data in users.items():
        if login == "admin":
            continue
        # Для локальных пользователей просто проверяем наличие
        if hash(login) % 10000 == user_id:
            target_login = login
            break
    
    if target_login and target_login in users:
        del users[target_login]
        if _save_users(users):
            return jsonify({"message": "Пользователь удалён локально"})
        else:
            return jsonify({"error": "Ошибка сохранения"}), 500

    return jsonify({"error": "Пользователь не найден. Удаление работает только через сервер синхронизации."}), 404


@app.route("/api/admin/user/<int:user_id>/trees", methods=["GET"])
def api_admin_get_user_trees(user_id):
    """Получить деревья пользователя."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    if not check_admin_access(username):
        return jsonify({"error": "Требуется права администратора"}), 403

    server_token = session.get('server_token')
    if server_token:
        try:
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/user/{user_id}/trees",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return jsonify(data)
        except Exception as e:
            print(f"[ADMIN] Get trees failed: {e}")

    # Fallback: возвращаем локальное дерево
    return jsonify({"trees": []})


@app.route("/api/admin/trees")
def api_admin_all_trees():
    """Получить все деревья (для вкладки Деревья)."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    if not check_admin_access(username):
        return jsonify({"error": "Требуется права администратора"}), 403

    # Пробуем получить деревья с сервера синхронизации
    server_token = session.get('server_token')
    if server_token:
        try:
            # Получаем список пользователей с сервера
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/admin/users",
                headers={'Authorization': f'Bearer {server_token}'},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                users_data = json.loads(response.read().decode())
                users_list = users_data.get('users', [])
                
                trees = []
                for user in users_list:
                    user_login = user.get('login')
                    user_id = user.get('id')
                    
                    # Получаем дерево пользователя
                    try:
                        tree_req = urllib.request.Request(
                            f"{SYNC_SERVER_URL}/api/admin/user/{user_id}/trees",
                            headers={'Authorization': f'Bearer {server_token}'},
                            method='GET'
                        )
                        with urllib.request.urlopen(tree_req, timeout=10) as tree_resp:
                            tree_data = json.loads(tree_resp.read().decode())
                            user_trees = tree_data.get('trees', [])
                            
                            for tree in user_trees:
                                trees.append({
                                    "id": tree.get('id'),
                                    "user_id": user_id,
                                    "user_login": user_login,
                                    "name": tree.get('name', f"Дерево {user_login}"),
                                    "persons": tree.get('persons', {}),
                                    "marriages": tree.get('marriages', []),
                                    "created_at": tree.get('created_at'),
                                    "updated_at": tree.get('updated_at')
                                })
                    except Exception as e:
                        print(f"[ADMIN] Error loading tree for {user_login}: {e}")
                
                return jsonify({"trees": trees})
                
        except Exception as e:
            print(f"[ADMIN] Error loading from sync server: {e}")
            # Fallback на локальные данные

    # Локальные данные (fallback)
    try:
        users = _load_users()
        trees = []

        for user_login in users.keys():
            # Пропускаем admin - у него нет дерева
            if user_login == "admin":
                continue
                
            try:
                tree_data = load_tree(user_login)
                persons = tree_data.get("persons", {})
                marriages = tree_data.get("marriages", [])

                trees.append({
                    "id": hash(user_login) % 10000,
                    "user_id": hash(user_login) % 10000,
                    "user_login": user_login,
                    "name": f"Дерево {user_login}",
                    "persons": persons,
                    "marriages": marriages,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"[ADMIN] Error loading local tree for {user_login}: {e}")

        return jsonify({"trees": trees})
    except Exception as e:
        print(f"[ADMIN] Error loading local trees: {e}")
        return jsonify({"trees": []})


@app.route("/api/tree", methods=["GET", "POST"])
def api_tree():
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    server_token = session.get('server_token')
    server_user_id = session.get('server_user_id')

    print(f"[API_TREE] ===== START =====")
    print(f"[API_TREE] username='{username}'")
    print(f"[API_TREE] username repr={repr(username)}")
    print(f"[API_TREE] has_token={server_token is not None}, user_id={server_user_id}")

    if request.method == "GET":
        # Для админа: проверяем, запрашивает ли он дерево конкретного пользователя
        tree_owner = request.args.get('tree_owner')
        if is_admin(username) and tree_owner:
            print(f"[API_TREE] Admin requesting tree for: {tree_owner}")
            # Админ запрашивает дерево другого пользователя
            # Загружаем с сервера синхронизации
            if server_token:
                try:
                    # Сначала получаем ID пользователя
                    users_req = urllib.request.Request(
                        f"{SYNC_SERVER_URL}/api/admin/users",
                        headers={'Authorization': f'Bearer {server_token}'},
                        method='GET'
                    )
                    with urllib.request.urlopen(users_req, timeout=10) as users_resp:
                        users_data = json.loads(users_resp.read().decode())
                        users_list = users_data.get('users', [])
                        target_user = next((u for u in users_list if u.get('login') == tree_owner), None)
                        
                        if target_user:
                            target_user_id = target_user.get('id')
                            # Получаем дерево пользователя
                            tree_req = urllib.request.Request(
                                f"{SYNC_SERVER_URL}/api/admin/user/{target_user_id}/trees",
                                headers={'Authorization': f'Bearer {server_token}'},
                                method='GET'
                            )
                            with urllib.request.urlopen(tree_req, timeout=10) as tree_resp:
                                tree_data_resp = json.loads(tree_resp.read().decode())
                                user_trees = tree_data_resp.get('trees', [])
                                
                                if user_trees:
                                    tree = user_trees[0]  # Берём первое дерево
                                    persons = {str(k): v for k, v in tree.get("persons", {}).items()}
                                    for p in persons.values():
                                        if isinstance(p, dict):
                                            for k in ("parents", "children", "spouse_ids"):
                                                if k in p and isinstance(p[k], list):
                                                    p[k] = [str(x) for x in p[k]]
                                    cc = tree.get("current_center") or next(iter(persons.keys()), None)
                                    print(f"[API_TREE] Admin loaded tree for {tree_owner}: {len(persons)} persons")
                                    return jsonify({
                                        "persons": persons,
                                        "marriages": tree.get("marriages", []),
                                        "current_center": cc,
                                    })
                except Exception as e:
                    print(f"[API_TREE] Error loading tree for {tree_owner}: {e}")
        
        # Обычная загрузка дерева текущего пользователя
        # Пробуем загрузить с сервера синхронизации
        if server_token:
            try:
                print(f"[API_TREE] Downloading from sync server...")
                req = urllib.request.Request(
                    f"{SYNC_SERVER_URL}/api/sync/download",
                    headers={'Authorization': f'Bearer {server_token}'},
                    method='GET'
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    tree_data = data.get('tree', {})
                    persons_count = len(tree_data.get("persons", {}))
                    print(f"[API_TREE] Sync server returned {persons_count} persons")
                    
                    # Если сервер вернул пустое дерево, пробуем загрузить локальное
                    if persons_count == 0:
                        print(f"[API_TREE] Server returned empty tree, trying local file...")
                        local_data = load_tree(username)
                        if len(local_data.get("persons", {})) > 0:
                            print(f"[API_TREE] Loaded {len(local_data['persons'])} persons from local file")
                            persons = {str(k): v for k, v in local_data.get("persons", {}).items()}
                            for p in persons.values():
                                if isinstance(p, dict):
                                    for k in ("parents", "children", "spouse_ids"):
                                        if k in p and isinstance(p[k], list):
                                            p[k] = [str(x) for x in p[k]]
                            cc = local_data.get("current_center")
                            return jsonify({
                                "persons": persons,
                                "marriages": local_data.get("marriages", []),
                                "current_center": str(cc) if cc is not None and str(cc) != "None" else None,
                            })
                        else:
                            print(f"[API_TREE] Local file also empty, creating empty tree for {username}")
                            # Создаём пустое дерево для нового пользователя
                            empty_tree = {"persons": {}, "marriages": [], "current_center": None}
                            save_tree(username, empty_tree)
                    
                    # Если сервер вернул дерево с персонами, используем его
                    if persons_count > 0:
                        persons = {str(k): v for k, v in tree_data.get("persons", {}).items()}
                        for p in persons.values():
                            if isinstance(p, dict):
                                for k in ("parents", "children", "spouse_ids"):
                                    if k in p and isinstance(p[k], list):
                                        p[k] = [str(x) for x in p[k]]
                        cc = tree_data.get("current_center")
                        return jsonify({
                            "persons": persons,
                            "marriages": tree_data.get("marriages", []),
                            "current_center": str(cc) if cc is not None and str(cc) != "None" else None,
                        })
            except Exception as e:
                print(f"[API_TREE] Download from sync server failed: {e}")

        # Fallback на локальный файл
        print(f"[API_TREE] Fallback to local file for username='{username}'")
        data = load_tree(username)
        persons_count = len(data.get("persons", {}))
        print(f"[API_TREE] Local file loaded {persons_count} persons for '{username}'")
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
    
    # Сохраняем на сервер синхронизации
    if server_token:
        try:
            tree_data = {"persons": persons, "marriages": marriages, "current_center": current_center}
            req = urllib.request.Request(
                f"{SYNC_SERVER_URL}/api/sync/upload",
                data=json.dumps({"tree": tree_data, "tree_name": f"Дерево {username}"}).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {server_token}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                if result.get('success') or result.get('message'):
                    return jsonify({"ok": True})
        except Exception as e:
            print(f"[WEB] Upload to sync server failed: {e}")
    
    # Fallback на локальный файл
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


@app.route("/api/export/pdf")
def api_export_pdf():
    """Экспорт дерева в PDF."""
    if not REPORTLAB_AVAILABLE:
        return jsonify({"error": "Reportlab не установлен. Экспорт в PDF недоступен."}), 503
    
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    
    username = session["username"]
    data = load_tree(username)
    persons = data.get("persons", {})
    
    if not persons:
        return jsonify({"error": "Дерево пусто"}), 400
    
    # Создаём PDF в памяти
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                           rightMargin=1*cm, leftMargin=1*cm,
                           topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                fontSize=18, leading=22, alignment=1, spaceAfter=20)
    
    # Заголовок
    elements.append(Paragraph(f"Семейное древо: {username}", title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Таблица с персонами
    table_data = [['№', 'ФИО', 'Пол', 'Дата рождения', 'Дата смерти', 'Место рождения', 'Примечания']]
    
    for idx, (pid, p) in enumerate(sorted(persons.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0), 1):
        full_name = f"{p.get('surname', '')} {p.get('name', '')} {p.get('patronymic', '')}".strip()
        table_data.append([
            str(idx),
            full_name,
            p.get('gender', ''),
            p.get('birth_date', ''),
            p.get('death_date', '') if p.get('is_deceased') else '',
            p.get('birth_place', ''),
            (p.get('notes', '') or '')[:50] + '...' if len(p.get('notes', '') or '') > 50 else p.get('notes', '')
        ])
    
    table = Table(table_data, colWidths=[0.8*cm, 4*cm, 1.5*cm, 2.5*cm, 2.5*cm, 3*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Статистика
    elements.append(Paragraph("Статистика", styles['Heading2']))
    
    male_count = sum(1 for p in persons.values() if p.get('gender') == 'Мужской')
    female_count = sum(1 for p in persons.values() if p.get('gender') == 'Женский')
    deceased_count = sum(1 for p in persons.values() if p.get('is_deceased'))
    
    stats_data = [
        ['Всего персон', str(len(persons))],
        ['Мужчин', str(male_count)],
        ['Женщин', str(female_count)],
        ['Умерших', str(deceased_count)],
        ['Живых', str(len(persons) - deceased_count)],
    ]
    
    stats_table = Table(stats_data, colWidths=[5*cm, 3*cm])
    stats_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
    ]))
    
    elements.append(stats_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"family_tree_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


@app.route("/api/backup/create", methods=["POST"])
def api_backup_create():
    """Создание резервной копии дерева."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    
    username = session["username"]
    data = load_tree(username)
    
    # Создаём ZIP-архив с данными
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Сохраняем JSON дерева
        tree_json = json.dumps(data, ensure_ascii=False, indent=2)
        zf.writestr(f"family_tree_{username}.json", tree_json)
        
        # Сохраняем метаданные
        metadata = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "persons_count": len(data.get("persons", {})),
            "marriages_count": len(data.get("marriages", [])),
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    
    buffer.seek(0)
    
    filename = f"backup_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(buffer, mimetype='application/zip', as_attachment=True, download_name=filename)


@app.route("/api/backup/list")
def api_backup_list():
    """Список резервных копий пользователя."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    
    username = session["username"]
    backups_dir = os.path.join(_data_dir, "backups", username)
    
    if not os.path.exists(backups_dir):
        return jsonify({"backups": []})
    
    backups = []
    for f in os.listdir(backups_dir):
        if f.startswith("backup_") and f.endswith(".zip"):
            filepath = os.path.join(backups_dir, f)
            stat = os.stat(filepath)
            backups.append({
                "filename": f,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    
    # Сортируем по дате (новые первые)
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"backups": backups[:20]})  # Максимум 20 последних


@app.route("/api/backup/restore", methods=["POST"])
def api_backup_restore():
    """Восстановление из резервной копии."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    
    username = session["username"]
    data = request.get_json() or {}
    backup_filename = data.get("filename")
    
    if not backup_filename:
        return jsonify({"error": "Не указан файл резервной копии"}), 400
    
    backups_dir = os.path.join(_data_dir, "backups", username)
    backup_path = os.path.join(backups_dir, backup_filename)
    
    if not os.path.exists(backup_path):
        return jsonify({"error": "Резервная копия не найдена"}), 404
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            # Извлекаем JSON дерева
            tree_filename = f"family_tree_{username}.json"
            if tree_filename not in zf.namelist():
                return jsonify({"error": "Файл дерева не найден в архиве"}), 404
            
            tree_data = json.loads(zf.read(tree_filename))
            
            # Сохраняем восстановленны�� данные
            if save_tree(username, tree_data):
                return jsonify({"ok": True, "message": "Дерево восстановлено"})
            else:
                return jsonify({"error": "Ошибка сохране��ия восстановленных данных"}), 500
    except Exception as e:
        return jsonify({"error": f"Ошибка восстановления: {str(e)}"}), 500


@app.route("/api/stats")
def api_stats():
    """Статистика дерева."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401

    username = session["username"]
    print(f"[API_STATS] username='{username}'")
    data = load_tree(username)
    persons = data.get("persons", {})
    print(f"[API_STATS] Loaded {len(persons)} persons")
    
    # Подсчёт статистики
    male_count = sum(1 for p in persons.values() if p.get('gender') == 'Мужской')
    female_count = sum(1 for p in persons.values() if p.get('gender') == 'Женский')
    deceased_count = sum(1 for p in persons.values() if p.get('is_deceased'))
    
    # Подсчёт поколе��ий (упрощённо)
    def get_generation(pid, visited=None):
        if visited is None:
            visited = set()
        if pid in visited:
            return 0
        visited.add(pid)
        p = persons.get(str(pid)) or persons.get(pid)
        if not p or not p.get('parents'):
            return 1
        return 1 + max(get_generation(pr, visited.copy()) for pr in p.get('parents', []))
    
    max_generation = 0
    for pid in persons:
        gen = get_generation(pid)
        max_generation = max(max_generation, gen)
    
    # Подсчёт браков
    marriages_count = len(data.get("marriages", []))
    
    # Средний возраст (для умерших)
    ages = []
    for p in persons.values():
        if p.get('is_deceased') and p.get('birth_date') and p.get('death_date'):
            try:
                birth = datetime.strptime(p['birth_date'], '%d.%m.%Y')
                death = datetime.strptime(p['death_date'], '%d.%m.%Y')
                age = (death - birth).days // 365
                if 0 < age < 120:
                    ages.append(age)
            except ValueError:
                pass
    
    avg_age = round(sum(ages) / len(ages)) if ages else None
    
    # Статистика по местам рожден��я
    birth_places = {}
    for p in persons.values():
        place = p.get('birth_place', '')
        if place:
            birth_places[place] = birth_places.get(place, 0) + 1
    
    top_places = sorted(birth_places.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        "total_persons": len(persons),
        "male_count": male_count,
        "female_count": female_count,
        "deceased_count": deceased_count,
        "living_count": len(persons) - deceased_count,
        "marriages_count": marriages_count,
        "max_generations": max_generation,
        "average_age": avg_age,
        "top_birth_places": top_places,
    })


@app.route("/api/version/check")
def api_version_check():
    """Проверка наличия обновлений."""
    current_version = VERSION
    
    try:
        # Проверяем последнюю версию на GitHub
        req = urllib.request.Request(
            "https://api.github.com/repos/Andrey1803/family-tree/releases/latest",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            release_data = json.loads(resp.read())
            latest_version = release_data.get("tag_name", "v0.0.0").lstrip('v')
            
            # Сравниваем версии
            def parse_version(v):
                try:
                    return tuple(map(int, v.split('.')))
                except ValueError:
                    return (0, 0, 0)
            
            current = parse_version(current_version)
            latest = parse_version(latest_version)
            
            has_update = latest > current
            
            return jsonify({
                "current_version": current_version,
                "latest_version": latest_version,
                "has_update": has_update,
                "download_url": release_data.get("html_url", ""),
                "release_notes": release_data.get("body", "")[:500] if has_update else "",
            })
    except Exception:
        return jsonify({
            "current_version": current_version,
            "latest_version": current_version,
            "has_update": False,
            "error": "Не удалось проверить ��бновления",
        })


@app.route("/welcome/complete", methods=["POST"])
def api_welcome_complete():
    """Завершение приветственного диалога (создание первой персоны)."""
    if "username" not in session:
        return jsonify({"error": "Не авторизован"}), 401
    
    username = session["username"]
    data = request.get_json() or {}
    
    # Проверяем, есть ли уже персоны
    tree_data = load_tree(username)
    if tree_data.get("persons"):
        return jsonify({"error": "Дерево уже содержит данные"}), 400
    
    # Создаём первую персону
    num_ids = [int(k) for k in tree_data.get("persons", {}).keys() if k.isdigit()]
    new_id = str(max(num_ids) + 1) if num_ids else "1"
    
    new_person = {
        "name": data.get("name", ""),
        "surname": data.get("surname", ""),
        "patronymic": data.get("patronymic", ""),
        "birth_date": data.get("birth_date", ""),
        "birth_place": data.get("birth_place", "Ми��ск, Беларусь"),
        "gender": data.get("gender", "Мужской"),
        "is_deceased": False,
        "death_date": "",
        "maiden_name": "",
        "parents": [],
        "children": [],
        "spouse_ids": [],
        "notes": f"Создано при первом запуске {datetime.now().strftime('%d.%m.%Y')}",
    }
    
    tree_data["persons"][new_id] = new_person
    tree_data["current_center"] = new_id
    
    if save_tree(username, tree_data):
        return jsonify({"ok": True, "person_id": new_id})
    else:
        return jsonify({"error": "Ошибка сохранения"}), 500


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


@app.route("/api/debug/smtp")
def api_debug_smtp():
    """Debug: проверка SMTP настроек (только для админа)."""
    if "username" not in session or session.get("username") != "admin":
        return jsonify({"error": "Требуется авторизация админа"}), 403
    
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from email_config import SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD, SMTP_USE_TLS
        config_ok = bool(SMTP_SERVER and SMTP_PORT and SMTP_LOGIN and SMTP_PASSWORD)
        
        return jsonify({
            "status": "ok" if config_ok else "not_configured",
            "smtp_config": {
                "SMTP_SERVER": SMTP_SERVER,
                "SMTP_PORT": SMTP_PORT,
                "SMTP_LOGIN": SMTP_LOGIN,
                "SMTP_PASSWORD_set": bool(SMTP_PASSWORD),
                "SMTP_USE_TLS": SMTP_USE_TLS,
            },
            "env_vars": {
                "SMTP_SERVER": os.environ.get("SMTP_SERVER", "NOT_SET"),
                "SMTP_PORT": os.environ.get("SMTP_PORT", "NOT_SET"),
                "SMTP_LOGIN": os.environ.get("SMTP_LOGIN", "NOT_SET"),
                "SMTP_PASSWORD": "***" if os.environ.get("SMTP_PASSWORD") else "NOT_SET",
                "SMTP_USE_TLS": os.environ.get("SMTP_USE_TLS", "NOT_SET"),
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    lan_ip = _get_lan_ip()
    if lan_ip:
        print(f"Доступ с других устройств в сети: http://{lan_ip}:5000")
    app.run(host="0.0.0.0", debug=True, port=5000)
