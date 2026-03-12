# -*- coding: utf-8 -*-
"""
Современный дизайн для приложения «Семейное древо».

Включает:
- Градиентные карточки персон
- Сглаженные линии связей
- Современные тени и эффекты
- Улучшенную цветовую палитру
"""

import tkinter as tk
from tkinter import ttk
import math

# === СОВРЕМЕННАЯ ЦВЕТОВАЯ ПАЛИТРА ===

# Градиенты для карточек (начальный, конечный цвет)
GRADIENT_MALE = ("#4A90E2", "#357ABD")      # Синий градиент
GRADIENT_FEMALE = ("#E94B8A", "#D6337A")    # Розовый градиент
GRADIENT_CENTER = ("#F5A623", "#D48806")    # Золотой для центральной персоны
GRADIENT_DECEASED = ("#95A5A6", "#7F8C8D")  # Серый для умерших

# Тени и эффекты
SHADOW_COLOR = "rgba(0, 0, 0, 0.15)"
SHADOW_OFFSET = 3
SHADOW_BLUR = 8

# Скругления
CARD_RADIUS = 12
CORNER_RADIUS = 8

# Современные цвета линий
LINE_COLORS = {
    "marriage": "#E67E22",      # Тёплый оранжевый
    "parent": "#3498DB",        # Мягкий синий
    "child": "#2ECC71",         # Свежий зелёный
    "highlight": "#F39C12",     # Золотой для выделения
}

# Толщины линий
LINE_WIDTHS = {
    "marriage": 3,
    "parent": 2.5,
    "child": 2,
}

# Шрифты
FONTS = {
    "title": ("Segoe UI Semibold", 11),
    "subtitle": ("Segoe UI", 9),
    "dates": ("Segoe UI", 8),
    "info": ("Segoe UI", 8),
}

# Размеры
CARD_SHADOW_OFFSET = 2
CARD_CORNER_RADIUS = 10


def interpolate_color(color1, color2, factor):
    """
    Интерполяция между двумя цветами.
    
    Args:
        color1: Первый цвет (hex).
        color2: Второй цвет (hex).
        factor: Коэффициент интерполяции (0.0 - 1.0).
    
    Returns:
        str: Промежуточный цвет в формате hex.
    """
    # Удаляем # и преобразуем в RGB
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    
    # Интерполяция
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def create_gradient_colors(start_color, end_color, steps=10):
    """
    Создаёт список цветов для градиента.
    
    Args:
        start_color: Начальный цвет.
        end_color: Конечный цвет.
        steps: Количество шагов градиента.
    
    Returns:
        list: Список цветов.
    """
    colors = []
    for i in range(steps):
        factor = i / (steps - 1)
        colors.append(interpolate_color(start_color, end_color, factor))
    return colors


def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """
    Рисует скруглённый прямоугольник.
    
    Args:
        canvas: Tkinter Canvas.
        x1, y1: Координаты верхнего левого угла.
        x2, y2: Координаты нижнего правого угла.
        radius: Радиус скругления.
        **kwargs: Параметры для create_polygon.
    
    Returns:
        ID нарисованного объекта.
    """
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_modern_card(canvas, x, y, width, height, person, is_center=False, is_hovered=False):
    """
    Рисует современную карточку персоны с градиентом и тенью.
    
    Args:
        canvas: Tkinter Canvas.
        x, y: Позиция верхнего левого угла.
        width, height: Размеры карточки.
        person: Объект Person.
        is_center: Центральная персона.
        is_hovered: Наведение курсора.
    
    Returns:
        dict: ID нарисованных объектов.
    """
    objects = {}
    
    # Определяем градиент
    if is_center:
        gradient = GRADIENT_CENTER
    elif person.is_deceased:
        gradient = GRADIENT_DECEASED
    elif person.gender == "Мужской":
        gradient = GRADIENT_MALE
    else:
        gradient = GRADIENT_FEMALE
    
    # Усиливаем цвет при наведении
    if is_hovered:
        gradient = (gradient[0], gradient[1])
    
    # Рисуем тень
    shadow_offset = CARD_SHADOW_OFFSET
    shadow_points = get_rounded_rect_points(
        x + shadow_offset, y + shadow_offset,
        x + width + shadow_offset, y + height + shadow_offset,
        CARD_CORNER_RADIUS
    )
    objects['shadow'] = canvas.create_polygon(
        shadow_points, 
        smooth=True,
        fill="rgba(0,0,0,0.1)",
        outline=""
    )
    
    # Рисуем основной прямоугольник с градиентом
    rect_points = get_rounded_rect_points(x, y, x + width, y + height, CARD_CORNER_RADIUS)
    objects['background'] = canvas.create_polygon(
        rect_points,
        smooth=True,
        fill=gradient[0],
        outline=gradient[1],
        width=2
    )
    
    # Добавляем градиентный эффект (несколько полупрозрачных слоёв)
    for i in range(3):
        inset = i * 8
        alpha = 0.08 - i * 0.02
        grad_points = get_rounded_rect_points(
            x + inset, y + inset,
            x + width - inset, y + height - inset * 2,
            CARD_CORNER_RADIUS - inset
        )
        objects[f'gradient_{i}'] = canvas.create_polygon(
            grad_points,
            smooth=True,
            fill=gradient[1],
            stipple='gray50',
            tags='gradient'
        )
    
    # Рисуем рамку
    objects['border'] = canvas.create_polygon(
        rect_points,
        smooth=True,
        fill='',
        outline=gradient[1],
        width=3
    )
    
    return objects


def get_rounded_rect_points(x1, y1, x2, y2, radius):
    """
    Возвращает точки для скруглённого прямоугольника.
    
    Args:
        x1, y1: Верхний левый угол.
        x2, y2: Нижний правый угол.
        radius: Радиус скругления.
    
    Returns:
        list: Список координат точек.
    """
    points = []
    
    # Верхняя сторона
    points.extend([x1 + radius, y1])
    points.extend([x2 - radius, y1])
    
    # Правый верхний угол
    points.extend([x2, y1])
    points.extend([x2, y1 + radius])
    
    # Правая сторона
    points.extend([x2, y2 - radius])
    points.extend([x2, y2])
    
    # Правый нижний угол
    points.extend([x2 - radius, y2])
    points.extend([x1 + radius, y2])
    
    # Нижняя сторона
    points.extend([x1, y2])
    points.extend([x1, y2 - radius])
    
    # Левый нижний угол
    points.extend([x1, y1 + radius])
    points.extend([x1, y1])
    
    # Левый верхний угол
    points.extend([x1 + radius, y1])
    
    return points


def draw_smooth_line(canvas, x1, y1, x2, y2, color, width=2, curved=False):
    """
    Рисует сглаженную линию.
    
    Args:
        canvas: Tkinter Canvas.
        x1, y1: Начальная точка.
        x2, y2: Конечная точка.
        color: Цвет линии.
        width: Толщина.
        curved: Сделать изогнутой.
    
    Returns:
        ID линии.
    """
    if curved:
        # Кривая Безье
        mid_x = (x1 + x2) / 2
        control_y = min(y1, y2) - 30
        return canvas.create_line(
            x1, y1,
            mid_x, control_y,
            x2, y2,
            smooth=True,
            fill=color,
            width=width,
            capstyle=tk.ROUND
        )
    else:
        return canvas.create_line(
            x1, y1, x2, y2,
            fill=color,
            width=width,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND
        )


def draw_modern_connection(canvas, x1, y1, x2, y2, line_type="parent"):
    """
    Рисует современную линию связи.
    
    Args:
        canvas: Tkinter Canvas.
        x1, y1: Начальная точка.
        x2, y2: Конечная точка.
        line_type: Тип линии (parent, marriage, child).
    
    Returns:
        ID линии.
    """
    color = LINE_COLORS.get(line_type, LINE_COLORS["parent"])
    width = LINE_WIDTHS.get(line_type, 2)
    
    # Рисуем основную линию
    line_id = draw_smooth_line(canvas, x1, y1, x2, y2, color, width)
    
    # Добавляем свечение
    glow_id = canvas.create_line(
        x1, y1, x2, y2,
        fill=color,
        width=width + 4,
        capstyle=tk.ROUND,
        stipple='gray25'
    )
    
    # Перемещаем свечение под основную линию
    canvas.tag_lower(glow_id, line_id)
    
    return line_id


def draw_person_icon(canvas, x, y, gender, size=20):
    """
    Рисует современную иконку персоны.
    
    Args:
        canvas: Tkinter Canvas.
        x, y: Позиция.
        gender: Пол.
        size: Размер.
    
    Returns:
        dict: ID объектов.
    """
    objects = {}
    
    # Цвет иконки
    if gender == "Мужской":
        color = "#3498DB"
    else:
        color = "#E94B8A"
    
    # Рисуем круг
    r = size // 2
    objects['circle'] = canvas.create_oval(
        x - r, y - r, x + r, y + r,
        fill=color,
        outline="white",
        width=2
    )
    
    # Рисуем символ (упрощённо)
    if gender == "Мужской":
        # Стрелка вверх (символ мужчины)
        objects['symbol'] = canvas.create_line(
            x, y + r//2, x, y - r//2,
            fill="white",
            width=2,
            arrow=tk.FIRST
        )
    else:
        # Крестик (символ женщины)
        objects['symbol'] = canvas.create_line(
            x - r//2, y, x + r//2, y,
            fill="white",
            width=2
        )
    
    return objects


def apply_modern_style(widget):
    """
    Применяет современный стиль к виджету.
    
    Args:
        widget: Tkinter виджет.
    """
    style = ttk.Style()
    
    # Настройка кнопок
    style.configure(
        'Modern.TButton',
        padding=(20, 10),
        font=('Segoe UI Semibold', 10),
        borderwidth=0,
        focuscolor='none'
    )
    
    # Настройка рамок
    style.configure(
        'Modern.TLabelframe',
        background='#f8f9fa',
        foreground='#2c3e50',
        borderwidth=0,
        padding=15
    )
    
    style.configure(
        'Modern.TLabelframe.Label',
        background='#f8f9fa',
        foreground='#2c3e50',
        font=('Segoe UI Semibold', 11)
    )
    
    # Настройка записей
    style.configure(
        'Modern.TEntry',
        padding=8,
        borderwidth=0,
        relief=tk.FLAT
    )


def create_shadow_text(canvas, x, y, text, font, fill, shadow_offset=1):
    """
    Создаёт текст с тенью.
    
    Args:
        canvas: Tkinter Canvas.
        x, y: Позиция.
        text: Текст.
        font: Шрифт.
        fill: Цвет текста.
        shadow_offset: Смещение тени.
    
    Returns:
        ID текста.
    """
    # Тень
    shadow_id = canvas.create_text(
        x + shadow_offset, y + shadow_offset,
        text=text,
        font=font,
        fill="rgba(0,0,0,0.2)",
        anchor=tk.NW
    )
    
    # Основной текст
    text_id = canvas.create_text(
        x, y,
        text=text,
        font=font,
        fill=fill,
        anchor=tk.NW
    )
    
    return text_id


# === ИНДИКАТОРЫ ===

def draw_status_indicator(canvas, x, y, status_type, size=8):
    """
    Рисует индикатор статуса.
    
    Args:
        canvas: Tkinter Canvas.
        x, y: Позиция.
        status_type: Тип статуса (alive, deceased, selected).
        size: Размер.
    """
    if status_type == "alive":
        color = "#2ECC71"  # Зелёный
    elif status_type == "deceased":
        color = "#95A5A6"  # Серый
    elif status_type == "selected":
        color = "#F39C12"  # Золотой
    else:
        color = "#3498DB"  # Синий
    
    r = size // 2
    return canvas.create_oval(
        x - r, y - r, x + r, y + r,
        fill=color,
        outline="white",
        width=2
    )


def draw_photo_placeholder(canvas, x, y, width, height):
    """
    Рисует современный плейсхолдер для фото.
    
    Args:
        canvas: Tkinter Canvas.
        x, y: Позиция.
        width, height: Размеры.
    """
    # Фон
    canvas.create_rectangle(
        x, y, x + width, y + height,
        fill="#ECF0F1",
        outline="#BDC3C7",
        width=1
    )
    
    # Иконка камеры (упрощённо)
    cx, cy = x + width // 2, y + height // 2
    canvas.create_oval(
        cx - 10, cy - 10, cx + 10, cy + 10,
        outline="#95A5A6",
        width=2
    )
    canvas.create_line(
        cx - 5, cy, cx + 5, cy,
        fill="#95A5A6",
        width=2
    )
