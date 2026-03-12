# -*- coding: utf-8 -*-
"""Общие утилиты аутентификации для desktop, web и sync_server."""

import hashlib
import json
import os
from typing import Dict, Optional

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# Список супер-админов
SUPER_ADMINS = ["admin", "Андрей Емельянов"]

# Соль для хеширования
AUTH_SALT = "FamilyTreeApp_Salt_v1"


def _password_hash(login: str, password: str) -> str:
    """
    Хеширует пароль.

    Если bcrypt доступны — использует bcrypt.
    Иначе — fallback на SHA256 (для обратной совместимости).
    """
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback для обратной совместимости
        raw = (AUTH_SALT + login + password).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def _verify_password(login: str, password: str, stored_data) -> bool:
    """
    Проверяет пароль против хеша.

    Автоматически определяет тип хеша (bcrypt или legacy SHA256).
    stored_data может быть строкой (старый формат) или словарём (новый формат).
    """
    # Извлекаем хеш из данных
    if isinstance(stored_data, dict):
        stored_hash = stored_data.get("password", "")
        if not stored_hash:
            return False
    else:
        stored_hash = stored_data

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


def _load_users(users_file: str) -> Dict[str, str]:
    """Загружает пользователей из JSON файла."""
    if not os.path.exists(users_file):
        return {}
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception:
        return {}


def _save_users(users_file: str, users: Dict[str, str]) -> bool:
    """Сохраняет пользователей в JSON файл."""
    try:
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def is_super_admin(username: str) -> bool:
    """Проверяет, является ли пользователь супер-админом."""
    if not username:
        return False
    return username in SUPER_ADMINS


def auth_check_local(login: str, password: str, users_file: str) -> bool:
    """
    Проверяет логин и пароль локально (без сервера).

    Args:
        login: Логин пользователя
        password: Пароль
        users_file: Путь к файлу пользователей

    Returns:
        bool: True если аутентификация успешна
    """
    if not login.strip() or not password:
        return False

    login_clean = login.strip()
    users = _load_users(users_file)
    stored = users.get(login_clean)

    if not stored:
        print(f"[AUTH_LOCAL] Local: user '{login_clean}' not found")
        return False

    result = _verify_password(login_clean, password, stored)
    print(f"[AUTH_LOCAL] Local: {'OK' if result else 'FAIL'}")
    return result
