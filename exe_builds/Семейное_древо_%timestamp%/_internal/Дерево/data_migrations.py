# -*- coding: utf-8 -*-
"""
Миграции данных.
Обновление формата JSON между версиями.
"""

import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)


class MigrationManager:
    """Управляет миграциями данных между версиями."""

    def __init__(self):
        self.migrations: Dict[str, List[Callable]] = {}

    def register_migration(self, from_version: str, to_version: str, func: Callable):
        """
        Регистрирует миграцию.

        Args:
            from_version: Исходная версия.
            to_version: Целевая версия.
            func: Функция миграции.
        """
        key = f"{from_version}->{to_version}"
        self.migrations[key] = func
        logger.debug(f"Зарегистрирована миграция: {key}")

    def migrate(self, data: Dict[str, Any], current_version: str, target_version: str) -> Dict[str, Any]:
        """
        Выполняет миграцию данных.

        Args:
            data: Данные для миграции.
            current_version: Текущая версия данных.
            target_version: Целевая версия.

        Returns:
            Мигрированные данные.
        """
        if current_version == target_version:
            return data

        # Получаем цепочку миграций
        migration_chain = self._get_migration_chain(current_version, target_version)

        if not migration_chain:
            logger.warning(f"Нет пути миграции от {current_version} до {target_version}")
            return data

        # Применяем миграции
        migrated_data = data.copy()
        for from_v, to_v, func in migration_chain:
            try:
                logger.info(f"Применение миграции: {from_v} -> {to_v}")
                migrated_data = func(migrated_data)
                migrated_data["version"] = to_v
            except Exception as e:
                logger.error(f"Ошибка миграции {from_v} -> {to_v}: {e}")
                raise

        return migrated_data

    def _get_migration_chain(self, from_version: str, to_version: str) -> List[tuple]:
        """
        Получает цепочку миграций.

        Args:
            from_version: Исходная версия.
            to_version: Целевая версия.

        Returns:
            Список кортежей (from, to, func).
        """
        chain = []
        current = from_version

        # Простая линейная миграция
        while current != to_version:
            key = f"{current}->{to_version}"
            if key in self.migrations:
                chain.append((current, to_version, self.migrations[key]))
                break

            # Ищем следующую миграцию
            found = False
            for migration_key, func in self.migrations.items():
                src, dst = migration_key.split("->")
                if src == current:
                    chain.append((src, dst, func))
                    current = dst
                    found = True
                    break

            if not found:
                break

        return chain


# === Миграции ===

def migrate_1_0_0_to_1_1_0(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Миграция 1.0.0 -> 1.1.0.
    Добавляет поля для автосохранения и резервных копий.
    """
    # Нормализация perons
    for pid, person in data.get("persons", {}).items():
        if isinstance(person, dict):
            # Добавляем отсутствующие поля
            if "photo_path" not in person:
                person["photo_path"] = ""
            if "is_deceased" not in person:
                person["is_deceased"] = False
            if "death_date" not in person:
                person["death_date"] = ""
            if "maiden_name" not in person:
                person["maiden_name"] = ""

    return data


def migrate_1_1_0_to_1_2_0(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Миграция 1.1.0 -> 1.2.0.
    Добавляет поля для дизайна и тем.
    """
    # Добавляем настройки темы в данные
    if "theme_settings" not in data:
        data["theme_settings"] = {"theme": "light"}

    return data


def migrate_1_2_0_to_1_3_0(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Миграция 1.2.0 -> 1.3.0.
    Добавляет поля для Timeline.
    """
    # Нормализация для Timeline
    for pid, person in data.get("persons", {}).items():
        if isinstance(person, dict):
            if "birth_place" not in person:
                person["birth_place"] = ""
            if "biography" not in person:
                person["biography"] = ""

    return data


def migrate_1_3_0_to_1_4_0(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Миграция 1.3.0 -> 1.4.0 (планируемая).
    Резервная миграция для будущих изменений.
    """
    return data


# === Регистрация миграций ===
_migrations = MigrationManager()

_migrations.register_migration("1.0.0", "1.1.0", migrate_1_0_0_to_1_1_0)
_migrations.register_migration("1.1.0", "1.2.0", migrate_1_1_0_to_1_2_0)
_migrations.register_migration("1.2.0", "1.3.0", migrate_1_2_0_to_1_3_0)
_migrations.register_migration("1.3.0", "1.4.0", migrate_1_3_0_to_1_4_0)


def migrate_data(data: Dict[str, Any], target_version: str = "1.3.0") -> Dict[str, Any]:
    """
    Выполняет миграцию данных до целевой версии.

    Args:
        data: Данные для миграции.
        target_version: Целевая версия.

    Returns:
        Мигрированные данные.
    """
    current_version = data.get("version", "1.0.0")
    return _migrations.migrate(data, current_version, target_version)


def get_current_version() -> str:
    """Возвращает текущую версию формата данных."""
    return "1.3.0"
