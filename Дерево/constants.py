# -*- coding: utf-8 -*-
"""Константы и палитра цветов для приложения «Семейное древо»."""

import json
import os
import sys

# URL для проверки обновлений (GitHub API — надёжнее, чем Railway)
GITHUB_REPO = "Andrey1803/family-tree"
UPDATE_CHECK_URL = "https://family-tree-production-0e7d.up.railway.app"  # запасной вариант
WEB_VERSION_URL = "https://family-tree-production-0e7d.up.railway.app"  # веб-версия

# --- Пол ---
GENDER_MALE = "Мужской"
GENDER_FEMALE = "Женский"

# === СОВРЕМЕННЫЙ ДИЗАЙН ===
# Улучшенная цветовая палитра с градиентами и современными оттенками

# --- Дизайн: фон окон и интерфейс ---
WINDOW_BG = "#f8f9fa"           # Светлый нейтральный фон
STATUSBAR_BG = "#e9ecef"         # Панель статуса
CENTER_LABEL_BG = "#dee2e6"     # Панель «Центр»
DIALOG_BG = "#ffffff"           # Фон диалогов
AUTH_BG = "#f8f9fa"             # Окна входа/регистрации
MENUBAR_BG = "#ffffff"           # Фон строки меню
MENU_MALE_COLOR = "#2563eb"      # Мужские пункты (современный синий)
MENU_FEMALE_COLOR = "#dc2626"    # Женские пункты (современный красный)

# --- Холст и карточки ---
CANVAS_BG = "#f1f5f9"            # Холст с лёгким оттенком
MARRIAGE_LINE_COLOR = "#f97316"  # Тёплый оранжевый
PARENT_LINE_COLOR = "#3b82f6"    # Мягкий синий
CHILD_LINE_COLOR = "#10b981"     # Свежий зелёный

# Градиенты для карточек
MALE_GRADIENT_START = "#60a5fa"   # Светло-синий
MALE_GRADIENT_END = "#2563eb"     # Насыщенный синий
FEMALE_GRADIENT_START = "#f472b6" # Светло-розовый
FEMALE_GRADIENT_END = "#db2777"   # Насыщенный розовый
DECEASED_GRADIENT_START = "#9ca3af"  # Серый светлый
DECEASED_GRADIENT_END = "#6b7280"    # Серый тёмный
CENTER_GRADIENT_START = "#fbbf24"    # Золотой светлый
CENTER_GRADIENT_END = "#d97706"      # Золотой тёмный

MALE_COLOR = "#2563eb"
FEMALE_COLOR = "#db2777"
DECEASED_COLOR = "#6b7280"
CENTER_COLOR = "#d97706"

CARD_BORDER_COLOR = "#1e293b"
CARD_HOVER_BORDER = "#f59e0b"    # Янтарный при наведении
CARD_INNER_RIM = "#94a3b8"
CARD_TEXT_PRIMARY = "#ffffff"
CARD_TEXT_SECONDARY = "#f1f5f9"
CARD_DATE_BIRTH = "#6ee7b7"
CARD_DATE_DEATH = "#fca5a5"
CARD_PHOTO_PLACEHOLDER_FILL = "#e2e8f0"
CARD_PHOTO_PLACEHOLDER_OUTLINE = "#94a3b8"
CARD_INNER_HIGHLIGHT = "#cbd5e1"
CARD_TOGGLE_BTN_FILL = "#f1f5f9"
CARD_TOGGLE_BTN_OUTLINE = "#334155"
CARD_TOGGLE_BTN_TEXT = "#1e293b"

# Эффекты
CARD_SHADOW_COLOR = "rgba(0, 0, 0, 0.1)"
CARD_SHADOW_OFFSET = 3
CARD_CORNER_RADIUS = 10

# --- Палитра (пользователь может менять через меню) ---
PALETTE_DEFAULTS = {
    "WINDOW_BG": "#f7f5f2",
    "MENUBAR_BG": "#e8e4de",
    "MENU_MALE_COLOR": "#1e40af",
    "MENU_FEMALE_COLOR": "#c41e3a",
    "CANVAS_BG": "#f0ebe3",
    "MALE_COLOR": "#1e40af",
    "FEMALE_COLOR": "#9d174d",
    "DECEASED_COLOR": "#64748b",
    "CENTER_COLOR": "#b45309",
    "MARRIAGE_LINE_COLOR": "#b45309",
    "PARENT_LINE_COLOR": "#475569",
    "CARD_BORDER_COLOR": "#1e293b",
    "CARD_HOVER_BORDER": "#eab308",
    "CARD_INNER_RIM": "#94a3b8",
    "CARD_TEXT_PRIMARY": "#ffffff",
    "CARD_TEXT_SECONDARY": "#e2e8f0",
    "CARD_DATE_BIRTH": "#6ee7b7",
    "CARD_DATE_DEATH": "#fca5a5",
    "CARD_PHOTO_PLACEHOLDER_FILL": "#e2e8f0",
    "CARD_PHOTO_PLACEHOLDER_OUTLINE": "#94a3b8",
    "CARD_INNER_HIGHLIGHT": "#cbd5e1",
    "CARD_TOGGLE_BTN_FILL": "#f1f5f9",
    "CARD_TOGGLE_BTN_OUTLINE": "#334155",
    "CARD_TOGGLE_BTN_TEXT": "#1e293b",
}

# Тёмная тема (альтернативная палитра)
DARK_THEME_DEFAULTS = {
    "WINDOW_BG": "#1e293b",
    "MENUBAR_BG": "#0f172a",
    "MENU_MALE_COLOR": "#60a5fa",
    "MENU_FEMALE_COLOR": "#f472b6",
    "CANVAS_BG": "#0f172a",
    "MALE_COLOR": "#3b82f6",
    "FEMALE_COLOR": "#ec4899",
    "DECEASED_COLOR": "#94a3b8",
    "CENTER_COLOR": "#fbbf24",
    "MARRIAGE_LINE_COLOR": "#f97316",
    "PARENT_LINE_COLOR": "#60a5fa",
    "CARD_BORDER_COLOR": "#334155",
    "CARD_HOVER_BORDER": "#fbbf24",
    "CARD_INNER_RIM": "#475569",
    "CARD_TEXT_PRIMARY": "#f1f5f9",
    "CARD_TEXT_SECONDARY": "#cbd5e1",
    "CARD_DATE_BIRTH": "#34d399",
    "CARD_DATE_DEATH": "#f87171",
    "CARD_PHOTO_PLACEHOLDER_FILL": "#334155",
    "CARD_PHOTO_PLACEHOLDER_OUTLINE": "#64748b",
    "CARD_INNER_HIGHLIGHT": "#475569",
    "CARD_TOGGLE_BTN_FILL": "#334155",
    "CARD_TOGGLE_BTN_OUTLINE": "#64748b",
    "CARD_TOGGLE_BTN_TEXT": "#f1f5f9",
}
PALETTE_LABELS = {
    "WINDOW_BG": "Фон окна и рамка",
    "MENUBAR_BG": "Фон строки меню",
    "MENU_MALE_COLOR": "Меню: мужчины (синий)",
    "MENU_FEMALE_COLOR": "Меню: женщины (красный)",
    "CANVAS_BG": "Фон холста",
    "MALE_COLOR": "Карточка: мужчина",
    "FEMALE_COLOR": "Карточка: женщина",
    "DECEASED_COLOR": "Карточка: умерший",
    "CENTER_COLOR": "Карточка: центр дерева",
    "MARRIAGE_LINE_COLOR": "Линия: супруги",
    "PARENT_LINE_COLOR": "Линия: родители–дети",
    "CARD_BORDER_COLOR": "Рамка карточки",
    "CARD_HOVER_BORDER": "Подсветка при наведении",
    "CARD_INNER_RIM": "Внутренняя линия карточки",
    "CARD_TEXT_PRIMARY": "Текст основной",
    "CARD_TEXT_SECONDARY": "Текст вторичный",
    "CARD_DATE_BIRTH": "Дата рождения",
    "CARD_DATE_DEATH": "Дата смерти",
    "CARD_PHOTO_PLACEHOLDER_FILL": "Заглушка фото (заливка)",
    "CARD_PHOTO_PLACEHOLDER_OUTLINE": "Заглушка фото (контур)",
    "CARD_INNER_HIGHLIGHT": "Разделитель фото/текст",
    "CARD_TOGGLE_BTN_FILL": "Кнопка переключения (заливка)",
    "CARD_TOGGLE_BTN_OUTLINE": "Кнопка переключения (контур)",
    "CARD_TOGGLE_BTN_TEXT": "Кнопка переключения (текст)",
}

# Путь к файлу палитры — в папке data/
# Вычисляется относительно точки входа (sys.executable для .exe или __file__ для скрипта)
if getattr(sys, "frozen", False):
    # Запуск .exe: данные в папке data/ рядом с exe
    _base_dir = os.path.dirname(sys.executable)
else:
    # Запуск из исходников: данные в папке data/ проекта
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE_FILE = os.path.join(_base_dir, "data", "palette.json")


def apply_palette(palette_dict):
    """Применяет словарь цветов к константам модуля (только известные ключи)."""
    mod = sys.modules[__name__]
    applied_count = 0
    for k, v in palette_dict.items():
        if k in PALETTE_DEFAULTS and isinstance(v, str):
            old_val = getattr(mod, k, None)
            setattr(mod, k, v)
            applied_count += 1
            print(f"[APPLY_PALETTE] {k}: {old_val} -> {v}")
    print(f"[APPLY_PALETTE] Всего применено: {applied_count} цветов")

def apply_dark_theme():
    """Применяет тёмную тему оформления."""
    apply_palette(DARK_THEME_DEFAULTS)
    print("[DARK_THEME] Тёмная тема применена")


def load_palette_from_file():
    """Загружает палитру из palette.json; возвращает dict или None."""
    abs_path = os.path.abspath(PALETTE_FILE)
    print(f"[PALETTE] Loading from: {abs_path}")
    if not os.path.exists(abs_path):
        print(f"[PALETTE] File not found")
        return None
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            result = {k: v for k, v in data.items()
                    if k in PALETTE_DEFAULTS and isinstance(v, str)}
            print(f"[PALETTE] Loaded {len(result)} colors")
            return result
    except Exception as e:
        print(f"[PALETTE] Error loading: {e}")
        pass
    return None


def save_palette_to_file():
    """Сохраняет текущие значения палитры в palette.json."""
    mod = sys.modules[__name__]
    data = {k: getattr(mod, k, v) for k, v in PALETTE_DEFAULTS.items()}
    try:
        # Используем абсолютный путь для отладки
        abs_path = os.path.abspath(PALETTE_FILE)
        print(f"[PALETTE] Saving to: {abs_path}")
        print(f"[PALETTE] Data to save: MARRIAGE_LINE_COLOR={data.get('MARRIAGE_LINE_COLOR')}")
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[PALETTE] Saved successfully!")
        return True
    except Exception as e:
        print(f"[PALETTE] Error saving: {e}")
        return False


# --- Фильтры ---
FILTER_ALL = "Все"
FILTER_ALIVE_ONLY = "Только живые"
FILTER_MALE_ONLY = "Только мужчины"
FILTER_FEMALE_ONLY = "Только женщины"
FILTER_WITH_PHOTOS_ONLY = "Только с фото"
FILTER_CHILDLESS_ONLY = "Только бездетные"

# --- Сообщения ---
MSG_SUCCESS_PERSON_ADDED = "Персона успешно добавлена!"
MSG_SUCCESS_PERSON_EDITED = "Персона успешно отредактирована!"
MSG_SUCCESS_PERSON_DELETED = "Персона успешно удалена!"
MSG_SUCCESS_MARRIAGE_ADDED = "Брак успешно добавлен!"
MSG_SUCCESS_MARRIAGE_REMOVED = "Брак успешно удален!"
MSG_ERROR_CANNOT_ADD_TO_SELF = "Невозможно добавить связь с самим собой."
MSG_ERROR_DUPLICATE_MARRIAGE = "Брак между этими людьми уже существует."
MSG_ERROR_BLOOD_RELATIVE_MARRIAGE = "Невозможно заключить брак между кровными родственниками."

MSG_STATUS_DATA_SAVED = "Данные сохранены."
MSG_STATUS_DATA_LOADED = "Данные загружены."
MSG_STATUS_PAN_ACTIVE = "Перемещение..."
MSG_STATUS_PAN_INACTIVE = "Перемещение завершено"
MSG_STATUS_ZOOM_IN = "Приближение..."
MSG_STATUS_ZOOM_OUT = "Отдаление..."
MSG_STATUS_TOOLTIP_VISIBLE = "Подсказка видна"
MSG_STATUS_TOOLTIP_HIDDEN = "Подсказка скрыта"
MSG_STATUS_CONTEXT_MENU_OPENED = "Контекстное меню открыто"
MSG_STATUS_CONTEXT_MENU_CLOSED = "Контекстное меню закрыто"
MSG_STATUS_DIALOG_OPENED = "Диалог открыто"
MSG_STATUS_DIALOG_CLOSED = "Диалог закрыто"
MSG_STATUS_ERROR_GENERIC = "Произошла ошибка"
MSG_STATUS_WARNING_GENERIC = "Предупреждение"
MSG_STATUS_INFO_GENERIC = "Информация"
MSG_STATUS_SUCCESS_GENERIC = "Успех"
MSG_STATUS_LOADING = "Загрузка..."
MSG_STATUS_SAVING = "Сохранение..."
MSG_STATUS_PROCESSING = "Обработка..."
MSG_STATUS_IDLE = "Ожидание..."

# --- Валидация ---
VALIDATION_MSG_NAME_SURNAME_REQUIRED = "Имя и фамилия обязательны для заполнения"
VALIDATION_MSG_GENDER_INVALID = "Пол должен быть 'Мужской' или 'Женский'"
VALIDATION_MSG_BIRTH_DATE_INVALID = "Неверный формат даты рождения (ДД.ММ.ГГГГ)"
VALIDATION_MSG_DEATH_DATE_INVALID = "Неверный формат даты смерти (ДД.ММ.ГГГГ)"
VALIDATION_MSG_DEATH_DATE_NEEDED = "Для умершего человека необходимо указать дату смерти"

# --- Правила для генерации отчеств ---
PATRONYMIC_RULES = [
    ("ий", "евич", "евна"),
    ("ей", "евич", "евна"),
    ("ый", "ович", "овна"),
    ("ай", "аевич", "аевна"),
    ("ой", "ович", "овна"),
    ("я", "евич", "евна"),
    ("а", "ович", "овна"),
    ("ь", "евич", "евна"),
    ("г", "оглы", "кызы"),
    ("к", "ович", "овна"),
    ("м", "ович", "овна"),
    ("н", "ович", "овна"),
    ("р", "ович", "овна"),
    ("с", "ович", "овна"),
    ("т", "ович", "овна"),
    ("в", "ович", "овна"),
    ("й", "евич", "евна"),
]
PATRONYMIC_NAME_RULES = [
    ("ьевич", "ий"),
    ("ьевна", "ий"),
    ("евич", "й"),
    ("евна", "й"),
    ("ович", ""),
    ("овна", ""),
    ("оглы", "г"),
    ("кызы", "г"),
]

# --- Настройки отображения ---
DEFAULT_MARRIAGE_LINE_DASH = None
MIN_WINDOW_WIDTH = 1000
SCALE_LABEL = "Масштаб:"
MAX_PHOTO_SIZE = (60, 50)
