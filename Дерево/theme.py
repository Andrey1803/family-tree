# -*- coding: utf-8 -*-
"""
Модуль управления темами оформления для приложения «Семейное древо».

Поддерживаемые темы:
- Light (светлая) — тема по умолчанию
- Dark (тёмная) — тёмная тема
"""

import json
import os

# Путь к файлу настроек темы
THEME_SETTINGS_FILE = "theme_settings.json"

# === СВЕТЛАЯ ТЕМА (по умолчанию) ===
LIGHT_THEME = {
    # Основные цвета
    "window_bg": "#f8f9fa",
    "window_fg": "#1e293b",
    
    # Меню
    "menubar_bg": "#ffffff",
    "menubar_fg": "#1e293b",
    "menu_bg": "#ffffff",
    "menu_fg": "#1e293b",
    "menu_active_bg": "#f1f5f9",
    "menu_active_fg": "#1e293b",
    
    # Холст
    "canvas_bg": "#f1f5f9",
    
    # Карточки персон
    "card_male_bg": "#60a5fa",
    "card_female_bg": "#f472b6",
    "card_border": "#1e293b",
    "card_text": "#ffffff",
    "card_text_secondary": "#f1f5f9",
    
    # Линии связей
    "marriage_line": "#f97316",
    "parent_line": "#3b82f6",
    "child_line": "#10b981",
    
    # Панели
    "statusbar_bg": "#e9ecef",
    "statusbar_fg": "#1e293b",
    "center_label_bg": "#dee2e6",
    "center_label_fg": "#1e293b",
    "counter_label_bg": "#e2e8f0",
    "counter_label_fg": "#1e293b",
    
    # Диалоги
    "dialog_bg": "#ffffff",
    "dialog_fg": "#1e293b",
    
    # Кнопки
    "button_bg": "#ffffff",
    "button_fg": "#1e293b",
    "button_active_bg": "#f1f5f9",
    "button_active_fg": "#0f172a",
    "accent_button_bg": "#dc2626",
    "accent_button_fg": "#ffffff",
    
    # Выделение
    "highlight_bg": "#fef3c7",
    "highlight_border": "#f59e0b",
    
    # Прочее
    "entry_bg": "#ffffff",
    "entry_fg": "#1e293b",
    "listbox_bg": "#ffffff",
    "listbox_fg": "#1e293b",
    "tree_bg": "#f8fafc",
    "tree_fg": "#1e293b",
}

# === ТЁМНАЯ ТЕМА ===
DARK_THEME = {
    # Основные цвета
    "window_bg": "#0f172a",
    "window_fg": "#e2e8f0",
    
    # Меню
    "menubar_bg": "#1e293b",
    "menubar_fg": "#e2e8f0",
    "menu_bg": "#1e293b",
    "menu_fg": "#e2e8f0",
    "menu_active_bg": "#334155",
    "menu_active_fg": "#ffffff",
    
    # Холст
    "canvas_bg": "#0f172a",
    
    # Карточки персон
    "card_male_bg": "#3b82f6",
    "card_female_bg": "#ec4899",
    "card_border": "#475569",
    "card_text": "#ffffff",
    "card_text_secondary": "#cbd5e1",
    
    # Линии связей
    "marriage_line": "#f97316",
    "parent_line": "#60a5fa",
    "child_line": "#34d399",
    
    # Панели
    "statusbar_bg": "#1e293b",
    "statusbar_fg": "#e2e8f0",
    "center_label_bg": "#334155",
    "center_label_fg": "#e2e8f0",
    "counter_label_bg": "#334155",
    "counter_label_fg": "#e2e8f0",
    
    # Диалоги
    "dialog_bg": "#1e293b",
    "dialog_fg": "#e2e8f0",
    
    # Кнопки
    "button_bg": "#334155",
    "button_fg": "#e2e8f0",
    "button_active_bg": "#475569",
    "button_active_fg": "#ffffff",
    "accent_button_bg": "#ef4444",
    "accent_button_fg": "#0f172a",
    
    # Выделение
    "highlight_bg": "#422006",
    "highlight_border": "#fbbf24",
    
    # Прочее
    "entry_bg": "#334155",
    "entry_fg": "#e2e8f0",
    "listbox_bg": "#1e293b",
    "listbox_fg": "#e2e8f0",
    "tree_bg": "#0f172a",
    "tree_fg": "#e2e8f0",
}


def get_theme_settings_file():
    """Возвращает путь к файлу настроек темы."""
    return THEME_SETTINGS_FILE


def load_theme():
    """
    Загружает текущую тему из файла настроек.
    
    Returns:
        str: Название текущей темы ('light' или 'dark').
    """
    try:
        if os.path.exists(THEME_SETTINGS_FILE):
            with open(THEME_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('theme', 'light')
    except Exception:
        pass
    return 'light'


def save_theme(theme_name):
    """
    Сохраняет название темы в файл настроек.
    
    Args:
        theme_name: Название темы ('light' или 'dark').
    """
    try:
        with open(THEME_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'theme': theme_name}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения темы: {e}")


def get_theme_colors(theme_name):
    """
    Возвращает словарь цветов для указанной темы.
    
    Args:
        theme_name: Название темы ('light' или 'dark').
        
    Returns:
        dict: Словарь с цветами темы.
    """
    if theme_name == 'dark':
        return DARK_THEME.copy()
    return LIGHT_THEME.copy()


def apply_theme(theme_name, app):
    """
    Применяет тему к приложению.
    
    Args:
        theme_name: Название темы ('light' или 'dark').
        app: Экземпляр FamilyTreeApp.
    """
    colors = get_theme_colors(theme_name)
    
    root = app.root
    
    # Настройка основного окна
    root.configure(bg=colors['window_bg'])
    
    # Настройка стиля
    style = app.style if hasattr(app, 'style') else None
    if style is None:
        from tkinter import ttk
        style = ttk.Style()
        app.style = style
    
    # Настройка стилей ttk
    style.configure('.', 
                    background=colors['window_bg'],
                    foreground=colors['window_fg'],
                    font=('Segoe UI', 9))
    
    style.configure('TFrame', background=colors['window_bg'])
    style.configure('TLabel', background=colors['window_bg'], foreground=colors['window_fg'])
    style.configure('TButton', 
                    background=colors['button_bg'],
                    foreground=colors['button_fg'])
    style.map('TButton',
              background=[('active', colors['button_active_bg'])],
              foreground=[('active', colors['button_active_fg'])])
    
    style.configure('TEntry',
                    fieldbackground=colors['entry_bg'],
                    foreground=colors['entry_fg'])
    
    style.configure('TCombobox',
                    fieldbackground=colors['entry_bg'],
                    foreground=colors['entry_fg'])
    
    style.configure('TLabelframe',
                    background=colors['window_bg'],
                    foreground=colors['window_fg'])
    style.configure('TLabelframe.Label',
                    background=colors['window_bg'],
                    foreground=colors['window_fg'])
    
    # Акцентные кнопки
    style.configure('Accent.TButton',
                    background=colors['accent_button_bg'],
                    foreground=colors['accent_button_fg'])
    style.map('Accent.TButton',
              background=[('active', colors['accent_button_bg'])])
    
    # Настройка меню
    if hasattr(app, 'menu_bar') and app.menu_bar:
        app.menu_bar.configure(bg=colors['menubar_bg'], fg=colors['menubar_fg'])
        
        # Настройка всех подменю
        for menu_name in ['file_menu', 'edit_menu', 'view_menu', 'help_menu']:
            menu = getattr(app, menu_name, None)
            if menu:
                menu.configure(bg=colors['menu_bg'], fg=colors['menu_fg'],
                              activebackground=colors['menu_active_bg'],
                              activeforeground=colors['menu_active_fg'])
    
    # Настройка холста
    if hasattr(app, 'canvas') and app.canvas:
        app.canvas.configure(bg=colors['canvas_bg'])
    
    # Настройка панелей
    if hasattr(app, 'center_label') and app.center_label:
        app.center_label.configure(bg=colors['center_label_bg'], 
                                   fg=colors['center_label_fg'])
    
    if hasattr(app, 'counter_label') and app.counter_label:
        app.counter_label.configure(bg=colors['counter_label_bg'],
                                    fg=colors['counter_label_fg'])
    
    # Настройка контекстного меню
    if hasattr(app, 'context_menu') and app.context_menu:
        app.context_menu.configure(bg=colors['menu_bg'], fg=colors['menu_fg'],
                                   activebackground=colors['menu_active_bg'],
                                   activeforeground=colors['menu_active_fg'])
    
    if hasattr(app, 'add_relative_menu') and app.add_relative_menu:
        app.add_relative_menu.configure(bg=colors['menu_bg'], fg=colors['menu_fg'],
                                        activebackground=colors['menu_active_bg'],
                                        activeforeground=colors['menu_active_fg'])
    
    # Сохраняем текущую тему в приложении
    app.current_theme = theme_name
    app.theme_colors = colors
    
    # Обновляем вид дерева (только если приложение полностью инициализировано)
    if hasattr(app, 'hovered_person_id') and hasattr(app, 'refresh_view'):
        try:
            app.refresh_view()
        except Exception:
            pass  # Игнорируем ошибки при инициализации


def toggle_theme(app):
    """
    Переключает тему с светлой на тёмную и наоборот.
    
    Args:
        app: Экземпляр FamilyTreeApp.
        
    Returns:
        str: Новая текущая тема.
    """
    current = load_theme()
    new_theme = 'dark' if current == 'light' else 'light'
    save_theme(new_theme)
    apply_theme(new_theme, app)
    return new_theme


def get_theme_name(theme_name):
    """
    Возвращает отображаемое название темы.
    
    Args:
        theme_name: Техническое название темы ('light' или 'dark').
        
    Returns:
        str: Отображаемое название на русском.
    """
    if theme_name == 'dark':
        return 'Тёмная'
    return 'Светлая'
