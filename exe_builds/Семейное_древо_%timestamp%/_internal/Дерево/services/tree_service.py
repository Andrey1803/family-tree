# -*- coding: utf-8 -*-
"""
Сервис операций с семейным деревом.
Инкапсулирует логику загрузки, сохранения, валидации данных.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class TreeService:
    """Сервис для работы с данными семейного дерева."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Инициализация сервиса.

        Args:
            data_dir: Директория для хранения данных. Если None, используется текущая.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Создаёт директорию данных, если она не существует."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Ошибка создания директории данных: {e}")

    def get_tree_path(self, username: str) -> Path:
        """
        Получает путь к файлу дерева пользователя.

        Args:
            username: Имя пользователя.

        Returns:
            Путь к файлу дерева.
        """
        safe_name = (username or "Гость").replace("..", "").strip() or "Гость"
        return self.data_dir / f"family_tree_{safe_name}.json"

    def load_tree(self, username: str) -> Dict[str, Any]:
        """
        Загружает дерево пользователя из JSON.

        Args:
            username: Имя пользователя.

        Returns:
            Словарь с данными дерева: {persons, marriages, current_center, version}.
        """
        path = self.get_tree_path(username)
        if not path.exists():
            return self._create_empty_tree()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Применяем миграции
            from data_migrations import migrate_data, get_current_version
            target_version = get_current_version()
            current_version = data.get("version", "1.0.0")
            
            if current_version != target_version:
                logger.info(f"Применение миграции данных: {current_version} -> {target_version}")
                data = migrate_data(data, target_version)

            # Нормализация данных
            persons = {str(k): self._normalize_person(v) for k, v in data.get("persons", {}).items()}
            marriages = data.get("marriages", [])
            current_center = data.get("current_center")
            version = data.get("version", target_version)

            return {
                "persons": persons,
                "marriages": marriages,
                "current_center": current_center,
                "version": version,
            }
        except Exception as e:
            logger.error(f"Ошибка загрузки дерева: {e}")
            return self._create_empty_tree()

    def _normalize_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует данные персоны (приводит списки, значения по умолчанию)."""
        if not isinstance(person_data, dict):
            return person_data

        for key in ("parents", "children", "spouse_ids"):
            if key in person_data:
                val = person_data[key]
                if val is None:
                    person_data[key] = []
                elif not isinstance(val, list):
                    person_data[key] = list(val)
                else:
                    person_data[key] = [str(x) for x in val]

        # Значения по умолчанию
        defaults = {
            "name": "", "surname": "", "patronymic": "",
            "birth_date": "", "death_date": "", "gender": "",
            "photo": None, "photo_path": "", "is_deceased": False,
            "maiden_name": "", "birth_place": "", "biography": "",
            "burial_place": "", "burial_date": "", "photo_album": [],
            "links": [], "occupation": "", "education": "",
            "address": "", "notes": "", "collapsed_branches": False,
        }
        for k, v in defaults.items():
            if k not in person_data:
                person_data[k] = v

        return person_data

    def _create_empty_tree(self) -> Dict[str, Any]:
        """Создаёт пустое дерево."""
        return {
            "persons": {},
            "marriages": [],
            "current_center": None,
            "version": "1.3.0",
        }

    def save_tree(self, username: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Сохраняет дерево пользователя в JSON.

        Args:
            username: Имя пользователя.
            data: Данные дерева.

        Returns:
            (success, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        path = self.get_tree_path(username)

        try:
            # Подготовка данных к сохранению
            persons = {}
            for pid, p in data.get("persons", {}).items():
                pp = dict(p) if isinstance(p, dict) else getattr(p, "__dict__", {})
                # Нормализация списков
                for k in ("parents", "children", "spouse_ids"):
                    if k in pp:
                        pp[k] = list(pp[k]) if pp[k] and not isinstance(pp[k], list) else (pp[k] or [])
                persons[str(pid)] = pp

            # Нормализация браков
            marriages_out = []
            for m in data.get("marriages", []):
                if isinstance(m, (list, tuple)) and len(m) == 2:
                    a, b = str(m[0]), str(m[1])
                    marriages_out.append(sorted([a, b]))

            out = {
                "persons": persons,
                "marriages": marriages_out,
                "current_center": str(data.get("current_center")) if data.get("current_center") else None,
                "version": "1.3.0",
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            logger.info(f"Дерево сохранено: {path}")
            return True, None

        except Exception as e:
            logger.error(f"Ошибка сохранения дерева: {e}")
            return False, str(e)

    def validate_person(self, person_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Валидирует данные персоны.

        Args:
            person_data: Данные персоны.

        Returns:
            (is_valid, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        from constants import (
            GENDER_MALE, GENDER_FEMALE,
            VALIDATION_MSG_NAME_SURNAME_REQUIRED,
            VALIDATION_MSG_GENDER_INVALID,
            VALIDATION_MSG_BIRTH_DATE_INVALID,
            VALIDATION_MSG_DEATH_DATE_INVALID,
            VALIDATION_MSG_DEATH_DATE_NEEDED,
        )

        # Имя и фамилия обязательны
        if not (person_data.get("name") or "").strip():
            return False, VALIDATION_MSG_NAME_SURNAME_REQUIRED
        if not (person_data.get("surname") or "").strip():
            return False, VALIDATION_MSG_NAME_SURNAME_REQUIRED

        # Проверка пола
        gender = person_data.get("gender", "")
        if gender and gender not in (GENDER_MALE, GENDER_FEMALE):
            return False, VALIDATION_MSG_GENDER_INVALID

        # Проверка дат
        birth_date = person_data.get("birth_date", "")
        death_date = person_data.get("death_date", "")
        is_deceased = person_data.get("is_deceased", False)

        if birth_date and not self._validate_date(birth_date):
            return False, VALIDATION_MSG_BIRTH_DATE_INVALID

        if death_date and not self._validate_date(death_date):
            return False, VALIDATION_MSG_DEATH_DATE_INVALID

        if is_deceased and not death_date:
            return False, VALIDATION_MSG_DEATH_DATE_NEEDED

        return True, None

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """
        Проверяет формат даты (ДД.ММ.ГГГГ).

        Args:
            date_str: Строка даты.

        Returns:
            True если формат корректен.
        """
        if not date_str:
            return True
        try:
            parts = date_str.split(".")
            if len(parts) != 3:
                return False
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 1900):
                return False
            return True
        except (ValueError, IndexError):
            return False

    def create_backup_path(self, original_path: Path) -> Path:
        """
        Создаёт путь для резервной копии файла.

        Args:
            original_path: Путь к оригинальному файлу.

        Returns:
            Путь для резервной копии.
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir / f"{original_path.stem}_{timestamp}{original_path.suffix}"
