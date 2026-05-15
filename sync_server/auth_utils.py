# -*- coding: utf-8 -*-
"""Утилиты аутентификации для sync_server (копия корневого auth_utils для деплоя Railway)."""

import hashlib
import json
import os
from typing import Dict

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

SUPER_ADMINS = ["admin", "Андрей Емельянов"]
AUTH_SALT = "FamilyTreeApp_Salt_v1"


def _password_hash(login: str, password: str) -> str:
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    raw = (AUTH_SALT + login + password).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _verify_password(login: str, password: str, stored_data) -> bool:
    if isinstance(stored_data, dict):
        stored_hash = stored_data.get("password", "")
        if not stored_hash:
            return False
    else:
        stored_hash = stored_data

    if not stored_hash:
        return False

    if stored_hash.startswith("$2"):
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False
        return False
    return _password_hash(login, password) == stored_hash


def _load_users(users_file: str) -> Dict[str, str]:
    if not os.path.exists(users_file):
        return {}
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception:
        return {}


def _save_users(users_file: str, users: Dict[str, str]) -> bool:
    try:
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def is_super_admin(username: str) -> bool:
    if not username:
        return False
    return username in SUPER_ADMINS


def auth_check_local(login: str, password: str, users_file: str) -> bool:
    if not login.strip() or not password:
        return False
    login_clean = login.strip()
    users = _load_users(users_file)
    stored = users.get(login_clean)
    if not stored:
        return False
    return _verify_password(login_clean, password, stored)
