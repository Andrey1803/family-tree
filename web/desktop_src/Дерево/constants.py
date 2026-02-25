# -*- coding: utf-8 -*-
"""Константы и палитра цветов для приложения «Семейное древо»."""

import json
import os
import sys

# --- Пол ---
GENDER_MALE = "Мужской"
GENDER_FEMALE = "Женский"

# --- Дизайн: холст и карточки ---
CANVAS_BG = "#f5f0e8"
MARRIAGE_LINE_COLOR = "#b45309"
PARENT_LINE_COLOR = "#475569"
CHILD_LINE_COLOR = "#0d9488"

MALE_COLOR = "#1e40af"
FEMALE_COLOR = "#9d174d"
DECEASED_COLOR = "#64748b"
CENTER_COLOR = "#b45309"

CARD_BORDER_COLOR = "#1e293b"
CARD_HOVER_BORDER = "#eab308"
CARD_INNER_RIM = "#94a3b8"
CARD_TEXT_PRIMARY = "#ffffff"
CARD_TEXT_SECONDARY = "#e2e8f0"
CARD_DATE_BIRTH = "#6ee7b7"
CARD_DATE_DEATH = "#fca5a5"
CARD_PHOTO_PLACEHOLDER_FILL = "#e2e8f0"
CARD_PHOTO_PLACEHOLDER_OUTLINE = "#94a3b8"
CARD_INNER_HIGHLIGHT = "#cbd5e1"
CARD_TOGGLE_BTN_FILL = "#f1f5f9"
CARD_TOGGLE_BTN_OUTLINE = "#334155"
CARD_TOGGLE_BTN_TEXT = "#1e293b"

# --- Палитра (пользователь может менять через меню) ---
PALETTE_DEFAULTS = {
    "CANVAS_BG": "#f5f0e8",
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
PALETTE_LABELS = {
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
PALETTE_FILE = "palette.json"


def apply_palette(palette_dict):
    """Применяет словарь цветов к константам модуля (только известные ключи)."""
    mod = sys.modules[__name__]
    for k, v in palette_dict.items():
        if k in PALETTE_DEFAULTS and isinstance(v, str):
            setattr(mod, k, v)


def load_palette_from_file():
    """Загружает палитру из palette.json; возвращает dict или None."""
    if not os.path.exists(PALETTE_FILE):
        return None
    try:
        with open(PALETTE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {k: v for k, v in data.items()
                        if k in PALETTE_DEFAULTS and isinstance(v, str)}
    except Exception:
        pass
    return None


def save_palette_to_file():
    """Сохраняет текущие значения палитры в palette.json."""
    mod = sys.modules[__name__]
    data = {k: getattr(mod, k, v) for k, v in PALETTE_DEFAULTS.items()}
    try:
        with open(PALETTE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
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
MSG_STATUS_TOOLTIP_VISIBLE = "Подсказка видна"
MSG_STATUS_TOOLTIP_HIDDEN = "Подсказка скрыта"
MSG_STATUS_ZOOM_IN = "Приближение"
MSG_STATUS_ZOOM_OUT = "Отдаление"
MSG_STATUS_PAN_ACTIVE = "Перемещение активно"
MSG_STATUS_PAN_INACTIVE = "Перемещение неактивно"
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
