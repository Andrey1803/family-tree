# -*- coding: utf-8 -*-
"""
Сервис управления настройками пользователя.
Окно, темы, предпочтения.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SettingsService:
    """Сервис для управления настройками пользователя."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Инициализация сервиса.

        Args:
            data_dir: Директория для данных. Если None, используется текущая.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Создаёт директорию данных, если она не существует."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Ошибка создания директории данных: {e}")

    def load_window_settings(self) -> Dict[str, Any]:
        """
        Загружает настройки окна.

        Returns:
            Словарь с настройками: {width, height, x, y, theme}.
        """
        path = self.data_dir / "window_settings.json"
        defaults = {
            "width": 1200,
            "height": 800,
            "x": 100,
            "y": 100,
            "theme": "light",
        }

        if not path.exists():
            return defaults

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**defaults, **data}
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек окна: {e}")
            return defaults

    def save_window_settings(self, width: int, height: int, x: int, y: int, theme: str = "light") -> bool:
        """
        Сохраняет настройки окна.

        Args:
            width: Ширина окна.
            height: Высота окна.
            x: Позиция X.
            y: Позиция Y.
            theme: Тема оформления.

        Returns:
            True если успешно.
        """
        path = self.data_dir / "window_settings.json"
        data = {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "theme": theme,
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек окна: {e}")
            return False

    def load_palette(self) -> Optional[Dict[str, str]]:
        """
        Загружает цветовую палитру.

        Returns:
            Словарь с цветами или None.
        """
        from constants import PALETTE_DEFAULTS
        path = self.data_dir / "palette.json"

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Фильтрация только известных ключей
            return {k: v for k, v in data.items() if k in PALETTE_DEFAULTS and isinstance(v, str)}
        except Exception as e:
            logger.error(f"Ошибка загрузки палитры: {e}")
            return None

    def save_palette(self, palette: Dict[str, str]) -> bool:
        """
        Сохраняет цветовую палитру.

        Args:
            palette: Словарь с цветами.

        Returns:
            True если успешно.
        """
        from constants import PALETTE_DEFAULTS
        path = self.data_dir / "palette.json"

        # Фильтрация только известных ключей
        filtered = {k: v for k, v in palette.items() if k in PALETTE_DEFAULTS and isinstance(v, str)}

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(filtered, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения палитры: {e}")
            return False

    def load_login_remember(self) -> Optional[str]:
        """
        Загружает запомненный логин.

        Returns:
            Логин или None.
        """
        path = self.data_dir / "login_remember.json"

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("login")
        except Exception:
            return None

    def save_login_remember(self, login: str) -> bool:
        """
        Сохраняет запомненный логин.

        Args:
            login: Логин для запоминания.

        Returns:
            True если успешно.
        """
        path = self.data_dir / "login_remember.json"

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"login": login}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения логина: {e}")
            return False

    def clear_login_remember(self) -> bool:
        """
        Удаляет запомненный логин.

        Returns:
            True если успешно.
        """
        path = self.data_dir / "login_remember.json"

        try:
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления логина: {e}")
            return False

    def get_user_settings_path(self, username: str) -> Path:
        """
        Получает путь к файлу настроек пользователя.

        Args:
            username: Имя пользователя.

        Returns:
            Путь к файлу настроек.
        """
        safe_name = (username or "Гость").replace("..", "").strip() or "Гость"
        return self.data_dir / f"user_settings_{safe_name}.json"

    def load_user_settings(self, username: str) -> Dict[str, Any]:
        """
        Загружает настройки пользователя.

        Args:
            username: Имя пользователя.

        Returns:
            Словарь с настройками.
        """
        path = self.get_user_settings_path(username)

        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки пользователя.

        Args:
            username: Имя пользователя.
            settings: Настройки.

        Returns:
            True если успешно.
        """
        path = self.get_user_settings_path(username)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек пользователя: {e}")
            return False
