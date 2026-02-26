# -*- coding: utf-8 -*-
"""
Сервис управления темами оформления.
Расширяет базовый theme.py с улучшенной архитектурой.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Темы оформления
THEME_LIGHT = "light"
THEME_DARK = "dark"

# Цвета светлой темы
LIGHT_THEME_COLORS = {
    "window_bg": "#f8f9fa",
    "menubar_bg": "#ffffff",
    "canvas_bg": "#f1f5f9",
    "card_text": "#1e293b",
    "statusbar_bg": "#e9ecef",
    "center_label_bg": "#dee2e6",
    "dialog_bg": "#ffffff",
    "male_gradient_start": "#60a5fa",
    "male_gradient_end": "#2563eb",
    "female_gradient_start": "#f472b6",
    "female_gradient_end": "#db2777",
    "deceased_gradient_start": "#9ca3af",
    "deceased_gradient_end": "#6b7280",
    "center_gradient_start": "#fbbf24",
    "center_gradient_end": "#d97706",
}

# Цвета тёмной темы
DARK_THEME_COLORS = {
    "window_bg": "#1a1a2e",
    "menubar_bg": "#16213e",
    "canvas_bg": "#0f0f23",
    "card_text": "#e2e8f0",
    "statusbar_bg": "#16213e",
    "center_label_bg": "#1a1a2e",
    "dialog_bg": "#16213e",
    "male_gradient_start": "#4a90d9",
    "male_gradient_end": "#1e40af",
    "female_gradient_start": "#d94a90",
    "female_gradient_end": "#9d174d",
    "deceased_gradient_start": "#6b7280",
    "deceased_gradient_end": "#374151",
    "center_gradient_start": "#f59e0b",
    "center_gradient_end": "#b45309",
}


class ThemeService:
    """Сервис для управления темами оформления."""

    def __init__(self):
        """Инициализация сервиса."""
        self.current_theme = THEME_LIGHT
        self.settings_service = None

    def set_settings_service(self, settings_service: Any):
        """
        Устанавливает сервис настроек.

        Args:
            settings_service: SettingsService для сохранения настроек.
        """
        self.settings_service = settings_service

    def get_current_theme(self) -> str:
        """
        Возвращает текущую тему.

        Returns:
            Название темы.
        """
        return self.current_theme

    def get_theme_name(self, theme: str) -> str:
        """
        Возвращает отображаемое название темы.

        Args:
            theme: Внутреннее название темы.

        Returns:
            Отображаемое название.
        """
        return "Тёмная" if theme == THEME_DARK else "Светлая"

    def get_theme_colors(self, theme: str) -> Dict[str, str]:
        """
        Возвращает цвета темы.

        Args:
            theme: Название темы.

        Returns:
            Словарь с цветами.
        """
        if theme == THEME_DARK:
            return DARK_THEME_COLORS.copy()
        return LIGHT_THEME_COLORS.copy()

    def load_theme(self) -> str:
        """
        Загружает сохранённую тему.

        Returns:
            Название темы.
        """
        if self.settings_service:
            settings = self.settings_service.load_window_settings()
            theme = settings.get("theme", THEME_LIGHT)
            self.current_theme = theme
            logger.info(f"Загружена тема: {self.get_theme_name(theme)}")
            return theme
        return THEME_LIGHT

    def save_theme(self, theme: str) -> bool:
        """
        Сохраняет тему.

        Args:
            theme: Название темы.

        Returns:
            True если успешно.
        """
        if self.settings_service:
            settings = self.settings_service.load_window_settings()
            settings["theme"] = theme
            result = self.settings_service.save_window_settings(
                settings.get("width", 1200),
                settings.get("height", 800),
                settings.get("x", 100),
                settings.get("y", 100),
                theme,
            )
            if result:
                logger.info(f"Сохранена тема: {self.get_theme_name(theme)}")
            return result
        return False

    def toggle_theme(self) -> str:
        """
        Переключает тему на противоположную.

        Returns:
            Новая тема.
        """
        self.current_theme = THEME_DARK if self.current_theme == THEME_LIGHT else THEME_LIGHT
        self.save_theme(self.current_theme)
        logger.info(f"Переключена тема на: {self.get_theme_name(self.current_theme)}")
        return self.current_theme

    def set_theme(self, theme: str) -> bool:
        """
        Устанавливает тему.

        Args:
            theme: Название темы.

        Returns:
            True если успешно.
        """
        if theme not in (THEME_LIGHT, THEME_DARK):
            logger.warning(f"Неизвестная тема: {theme}")
            return False

        self.current_theme = theme
        return self.save_theme(theme)

    def apply_theme(self, app: Any) -> bool:
        """
        Применяет тему к приложению.

        Args:
            app: Экземпляр FamilyTreeApp.

        Returns:
            True если успешно.
        """
        try:
            import tkinter as tk
            from tkinter import ttk

            colors = self.get_theme_colors(self.current_theme)

            # Настройка стилей
            style = ttk.Style()

            # Настройка цветов окна
            app.root.configure(bg=colors["window_bg"])

            # Обновление констант
            import constants as const
            for attr, value in colors.items():
                if hasattr(const, attr.upper()):
                    setattr(const, attr.upper(), value)

            logger.info(f"Применена тема: {self.get_theme_name(self.current_theme)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка применения темы: {e}")
            return False

    def is_dark_theme(self) -> bool:
        """
        Проверяет, активна ли тёмная тема.

        Returns:
            True если тёмная тема активна.
        """
        return self.current_theme == THEME_DARK

    def is_light_theme(self) -> bool:
        """
        Проверяет, активна ли светлая тема.

        Returns:
            True если светлая тема активна.
        """
        return self.current_theme == THEME_LIGHT
