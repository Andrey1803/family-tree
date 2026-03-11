# -*- coding: utf-8 -*-
"""Главное приложение: FamilyTreeApp — холст, меню, диалоги, отрисовка дерева."""

__all__ = ["FamilyTreeApp"]

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
import json
import os
import base64
import collections
import re
import io
import time
import math
from datetime import datetime

from PIL import Image, ImageTk

import constants


def get_contrast_text_color(bg_color):
    """
    Автоматически определяет контрастный цвет текста для заданного фона.
    Возвращает '#ffffff' (белый) для тёмного фона, '#000000' (чёрный) для светлого.
    
    :param bg_color: Цвет фона в формате '#RRGGBB'
    :return: '#ffffff' или '#000000'
    """
    bg_color = bg_color.lstrip('#')
    if len(bg_color) != 6:
        return '#ffffff'
    try:
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)
    except ValueError:
        return '#ffffff'
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return '#ffffff' if luminance < 128 else '#000000'


def fit_dialog_to_content(dialog, min_width=400, min_height=300, max_width=1200, max_height=900, padding=20):
    """
    Автоматически подстраивает размер диалога под содержимое.
    
    :param dialog: Окно Toplevel
    :param min_width: Минимальная ширина
    :param min_height: Минимальная высота
    :param max_width: Максимальная ширина
    :param max_height: Максимальная высота
    :param padding: Отступы
    """
    dialog.update_idletasks()
    
    # Получаем требуемый размер
    req_width = dialog.winfo_reqwidth() + padding * 2
    req_height = dialog.winfo_reqheight() + padding * 2
    
    # Ограничиваем размерами
    width = max(min_width, min(req_width, max_width))
    height = max(min_height, min(req_height, max_height))
    
    # Центрируем относительно родительского окна
    dialog.update()
    parent_x = dialog.winfo_parentx()
    parent_y = dialog.winfo_parenty()
    parent_width = dialog.winfo_parentwidth()
    parent_height = dialog.winfo_parentheight()
    
    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2
    
    dialog.geometry(f"{width}x{height}+{x}+{y}")
from models import Person, FamilyTreeModel
from ui_helpers import create_form_fields

# Модуль родства
try:
    from kinship import calculate_kinship
    KINSHIP_AVAILABLE = True
except ImportError:
    KINSHIP_AVAILABLE = False
    def calculate_kinship(model, center_id):
        return {}

# Модуль синхронизации
try:
    from sync import sync_to_server
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    def sync_to_server(data_file, username):
        return False

# Модуль резервного копирования
try:
    from backup import BackupManager, AutoSaveManager, init_backup_system
    BACKUP_AVAILABLE = True
except ImportError:
    BACKUP_AVAILABLE = False
    BackupManager = None
    AutoSaveManager = None
    def init_backup_system(*args, **kwargs):
        return None, None

# Модуль отмены/повтора действий
try:
    from undo import UndoManager, create_add_person_action, create_delete_person_action
    from undo import create_edit_person_action, create_add_marriage_action, create_remove_marriage_action
    UNDO_AVAILABLE = True
except ImportError:
    UNDO_AVAILABLE = False
    UndoManager = None
    create_add_person_action = None
    create_delete_person_action = None
    create_edit_person_action = None
    create_add_marriage_action = None
    create_remove_marriage_action = None

# Модуль управления темами
try:
    from theme import apply_theme, toggle_theme, load_theme, get_theme_name, get_theme_colors
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False
    def apply_theme(*args, **kwargs):
        pass
    def toggle_theme(*args, **kwargs):
        return 'light'
    def load_theme():
        return 'light'
    def get_theme_name(x):
        return 'Светлая'
    def get_theme_colors(x):
        return {}

class FamilyTreeApp:
    def __init__(self, root, data_file=None, username=None):
        self.root = root
        self.username = username
        
        # Отмечаем пользователя как активного
        try:
            from active_users import mark_user_active
            if username:
                mark_user_active(username)
                print(f"[ACTIVE] Пользователь {username} отмечен как активный")
        except Exception as e:
            print(f"[ACTIVE] Ошибка отметки активности: {e}")
        self.base_title = "Семейное древо"
        if username:
            self.base_title += f" — {username}"
        self.root.title(self.base_title)
        self.modified_indicator = " *"  # Индикатор несохранённых изменений

        # === ПРИМЕНЯЕМ ПАЛИТРУ В САМОМ НАЧАЛЕ (до создания виджетов) ===
        print(f"[APP.__INIT__] MARRIAGE_LINE_COLOR = {constants.MARRIAGE_LINE_COLOR}")
        print(f"[APP.__INIT__] CANVAS_BG = {constants.CANVAS_BG}")
        # ================================================================

        # Авто-синхронизация при запуске (если есть username)
        # ВКЛЮЧЕНО: загрузка дерева с сервера при старте
        if username:
            self.root.after(1000, self.auto_sync_on_startup)  # Через 1 секунду

        # Создание стилей для кнопок
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='black', background='#e74c3c')
        style.configure('Success.TButton', foreground='black', background='#27ae60')
        # Попробуем загрузить последние настройки окна
        try:
            with open("window_settings.json", 'r') as f:
                settings = json.load(f)
                width = settings.get("width", 1200)
                height = settings.get("height", 800)
                x = settings.get("x", 100)
                y = settings.get("y", 100)
        except FileNotFoundError:
            width = 1200
            height = 800
            x = 100
            y = 100
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        # --- ПЕРЕМЕННЫЕ (файл дерева — свой у каждого пользователя) ---
        actual_data_file = data_file or "family_tree.json"
        print(f"[DEBUG] __init__: data_file={data_file}, actual={actual_data_file}")
        self.model = FamilyTreeModel(data_file=actual_data_file)
        print(f"[DEBUG] __init__: model.data_file={self.model.data_file}")
        
        # Автосохранение каждые 5 минут
        self.auto_save_interval = 300000  # 5 минут в миллисекундах
        self.schedule_auto_save()
        self.canvas = tk.Canvas(root, bg=constants.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.photo_images = {}  # Хранит ссылки на PhotoImage
        self.coords = {}  # Хранит координаты {pid: (x, y)}
        self.visible_persons_in_coords = {}  # Персоны, видимые с учётом скрытия
        self.units = {}  # Супружеские пары {unit_id: [pid1, pid2]}
        self.level_structure = {}  # Структура уровней {level_num: [pid, ...]}
        self.last_selected_person_id = None
        self.current_scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.drag_start_time = 0
        self.DRAG_THRESHOLD = 5  # Порог движения в пикселях для начала перетаскивания
        self.search_results = []
        self.search_index = -1
        self.focus_mode_active = False  # ← ИНИЦИАЛИЗИРУЕМ ОДИН РАЗ (было дублирование!)
        self.precomputed_hidden_nodes = set()
        self.active_filters = {"gender": constants.FILTER_ALL, "status": constants.FILTER_ALL, "photos_only": False, "childless": False}
        # --- /ПЕРЕМЕННЫЕ ---
        # --- НАСТРОЙКИ РАЗМЕРОВ ---
        self.BASE_CARD_WIDTH = 120
        self.BASE_CARD_HEIGHT = 100
        self.BASE_PARENT_LINE_WIDTH = 2
        self.BASE_MARRIAGE_LINE_WIDTH = 3
        self.CARD_WIDTH = self.BASE_CARD_WIDTH
        self.CARD_HEIGHT = self.BASE_CARD_HEIGHT
        self.PARENT_LINE_WIDTH = self.BASE_PARENT_LINE_WIDTH
        self.MARRIAGE_LINE_WIDTH = self.BASE_MARRIAGE_LINE_WIDTH
        # --- /НАСТРОЙКИ РАЗМЕРОВ ---
        # Присваиваем глобальную константу как атрибут экземпляра
        self.MIN_WINDOW_WIDTH = constants.MIN_WINDOW_WIDTH
        # --- МЕНЮ ---
        self.menu_bar = tk.Menu(root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Новый", command=self.new_file)
        self.file_menu.add_command(label="Сохранить", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Экспорт в CSV", command=self.export_to_csv)
        self.file_menu.add_command(label="Импорт из CSV", command=self.import_from_csv)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="🌐 Открыть веб-версию", command=self.open_web_version)

        # Админ-панель только для Андрея Емельянова
        if self.username == "Емельянов Андрей" or self.username == "Андрей Емельянов":
            self.file_menu.add_separator()
            self.file_menu.add_command(label="👑 Админ-панель", command=self.open_admin_panel)

        # Персональная панель для всех пользователей
        self.file_menu.add_separator()
        self.file_menu.add_command(label="👤 Моя панель", command=self.open_user_dashboard)

        self.file_menu.add_separator()
        self.file_menu.add_command(label="Зарегистрировать протокол (веб → приложение)", command=self._register_protocol)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=self.on_exit)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Фильтры", command=self.open_filter_dialog)
        self.view_menu.add_command(label="Цвет интерфейса...", command=self.open_color_palette_dialog)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="🌙 Тёмная тема", command=lambda: self.toggle_theme(dark=True))
        self.view_menu.add_command(label="☀️ Светлая тема", command=lambda: self.toggle_theme(dark=False))
        self.view_menu.add_separator()
        self.view_menu.add_command(label="📅 Временная шкала", command=self.open_timeline)
        self.menu_bar.add_cascade(label="Вид", menu=self.view_menu)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        # Пункты меню Отмена/Повтор (если доступен модуль undo)
        self.undo_menu_item = None
        self.redo_menu_item = None
        if UNDO_AVAILABLE:
            self.undo_menu_item = self.edit_menu.add_command(
                label="Отмена", 
                command=self.undo,
                accelerator="Ctrl+Z"
            )
            self.redo_menu_item = self.edit_menu.add_command(
                label="Повтор", 
                command=self.redo,
                accelerator="Ctrl+Y"
            )
            self.edit_menu.add_separator()
            # Инициализация менеджера отмены (передаём model, а не self)
            self.undo_manager = UndoManager(self.model)
        else:
            self.undo_manager = None
        self.edit_menu.add_command(label="Найти", command=self.open_search_dialog)
        self.menu_bar.add_cascade(label="Правка", menu=self.edit_menu)
        
        # Меню "Сервис" (если доступны модули backup/theme)
        if BACKUP_AVAILABLE or THEME_AVAILABLE:
            self.service_menu = tk.Menu(self.menu_bar, tearoff=0)
            if BACKUP_AVAILABLE:
                self.service_menu.add_command(label="Резервные копии...", command=self.open_backup_dialog)
                self.service_menu.add_separator()
            if THEME_AVAILABLE:
                self.service_menu.add_command(label="Сменить тему", command=self.toggle_theme_menu)
            self.menu_bar.add_cascade(label="Сервис", menu=self.service_menu)
        
        # --- МЕНЮ СПРАВКА ---
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="О программе", command=self._show_about_dialog)
        self.help_menu.add_command(label="О разработчике", command=self._show_developer_dialog)
        self.menu_bar.add_cascade(label="Справка", menu=self.help_menu)
        # --- /МЕНЮ СПРАВКА ---
        
        root.config(menu=self.menu_bar)
        # --- /МЕНЮ ---
        # --- СТАТУСБАР И ПАНЕЛЬ ЦЕНТРА (в тон холста) ---
        # Счётчик персон
        self.counter_label = tk.Label(root, text="Персон: 0", bd=1, relief=tk.SUNKEN, anchor=tk.CENTER,
                                     bg="#e2e8f0", fg="#1e293b", font=("Segoe UI", 9, "bold"))
        self.counter_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.statusbar = tk.Label(root, text=constants.MSG_STATUS_IDLE, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                 bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9))
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.center_label = tk.Label(root, text="Центр: Не выбран", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     bg="#e2e8f0", fg="#1e293b", font=("Segoe UI", 9, "bold"))
        self.center_label.pack(side=tk.BOTTOM, fill=tk.X)
        # --- /ЦЕНТР ---
        # --- КОНТЕКСТНОЕ МЕНЮ ---
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Просмотреть", command=self.view_person)
        self.context_menu.add_command(label="Редактировать", command=self.edit_person)
        self.context_menu.add_command(label="Удалить", command=self.delete_person)
        self.context_menu.add_separator()
        
        # Создаём подменю "Родственник" с поддержкой цветов
        self.add_relative_menu = tk.Menu(self.context_menu, tearoff=0)
        
        # Группа 1: Родители
        self.add_relative_menu.add_command(label="👨 Отец... (синий)",
                                           command=lambda: self.add_parent_dialog(self.last_selected_person_id, "Мужской"))
        self.add_relative_menu.add_command(label="👩 Мать... (красный)",
                                           command=lambda: self.add_parent_dialog(self.last_selected_person_id, "Женский"))
        self.add_relative_menu.add_separator()
        
        # Группа 2: Дети
        self.add_relative_menu.add_command(label="👦 Сын... (синий)",
                                           command=lambda: self.add_child_dialog(self.last_selected_person_id, "Мужской"))
        self.add_relative_menu.add_command(label="👧 Дочь... (красный)",
                                           command=lambda: self.add_child_dialog(self.last_selected_person_id, "Женский"))
        self.add_relative_menu.add_separator()
        
        # Группа 3: Братья/Сёстры
        self.add_relative_menu.add_command(label="👤 Брат... (синий)",
                                           command=lambda: self.add_sibling_dialog(self.last_selected_person_id, "Мужской"))
        self.add_relative_menu.add_command(label="👤 Сестра... (красный)",
                                           command=lambda: self.add_sibling_dialog(self.last_selected_person_id, "Женский"))
        self.add_relative_menu.add_separator()
        
        # Группа 4: Супруги
        self.add_relative_menu.add_command(label="💍 Супруг(а)...",
                                           command=lambda: self.add_spouse_dialog(self.last_selected_person_id))
        self.context_menu.add_cascade(label="➕ Родственник", menu=self.add_relative_menu)
        # --- /КОНТЕКСТНОЕ МЕНЮ ---
        # --- СВЯЗИ КЛАВИШ ---
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-1>", self.stop_pan)
        self.canvas.bind("<MouseWheel>", self.zoom)
        # === ИСПРАВЛЕНО: ДОБАВЛЕНА ПРИВЯЗКА ГОРЯЧЕЙ КЛАВИШИ Ctrl+F ===
        self.root.bind("<Control-f>", lambda e: self.toggle_focus_mode())
        # Горячие клавиши для часто используемых действий
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-e>", lambda e: self.edit_person())
        self.root.bind("<Delete>", lambda e: self.delete_person())
        self.root.bind("<F2>", lambda e: self.edit_person())
        self.root.bind("<F3>", lambda e: self.open_search_dialog())
        self.root.bind("<Control-d>", lambda e: self.add_person_dialog())
        # === КОНЕЦ ИСПРАВЛЕНИЯ ===
        # Привязки для отмены/повтора (если доступен модуль undo)
        if UNDO_AVAILABLE:
            self.root.bind("<Control-z>", lambda e: self.undo())
            self.root.bind("<Control-y>", lambda e: self.redo())
        # --- /СВЯЗИ КЛАВИШ ---
        # --- ЗАГРУЗКА ---
        # СНАЧАЛА загружаем данные из файла
        self.model.load_from_file()
        print(f"[APP.__INIT__] Загружено {len(self.model.persons)} персон, {len(self.model.marriages)} браков")

        # Если current_center не установлен, но есть персоны с супругами — установить на первую
        if not self.model.current_center:
            for pid, person in self.model.get_all_persons().items():
                if getattr(person, 'spouse_ids', None):
                    self.model.current_center = pid
                    break
            # Если нет супругов — установить на первую персону
            if not self.model.current_center and self.model.get_all_persons():
                self.model.current_center = next(iter(self.model.get_all_persons().keys()))

        self.hovered_person_id = None  # ID персоны под курсором
        self.selected_person_id = None  # ID выбранной персоны (центр)

        # Принудительно применяем цвета из палитры ПЕРЕД отрисовкой
        self.apply_ui_colors_from_palette()
        
        # Применяем стили для тёмной темы если нужно
        is_dark_theme = constants.WINDOW_BG.lower() in ['#1e293b', '#0f172a', '#1a1a2e', '#16213e', '#2d3748', '#1a202c', '#2c3e50']
        if is_dark_theme:
            style = ttk.Style()
            # Применяем ко ВСЕМ виджетам сразу
            style.theme_use('clam')  # Используем тему clam для лучшего контроля
            style.configure('.', background='#1e293b', foreground='#ffffff')
            style.configure('TButton', background='#2d3748', foreground='#ffffff', font=('Arial', 10, 'bold'))
            style.configure('TEntry', fieldbackground='#2d3748', foreground='#ffffff', insertcolor='#ffffff')
            style.configure('TCombobox', fieldbackground='#2d3748', foreground='#ffffff')
            style.configure('TCheckbutton', background='#1e293b', foreground='#ffffff')
            style.configure('TRadiobutton', background='#1e293b', foreground='#ffffff')
            style.configure('TLabel', background='#1e293b', foreground='#ffffff')
            style.configure('TFrame', background='#1e293b')
            style.map('TButton', background=[('active', '#4a5568'), ('pressed', '#1a202c')])
            
            # Применяем цвета к меню (tk.Menu, не ttk)
            self.menu_bar.configure(bg='#0f172a', fg='#ffffff')
            self.file_menu.configure(bg='#0f172a', fg='#ffffff', activebackground='#1e293b', activeforeground='#ffffff')
            self.view_menu.configure(bg='#0f172a', fg='#ffffff', activebackground='#1e293b', activeforeground='#ffffff')
            self.edit_menu.configure(bg='#0f172a', fg='#ffffff', activebackground='#1e293b', activeforeground='#ffffff')
            self.help_menu.configure(bg='#0f172a', fg='#ffffff', activebackground='#1e293b', activeforeground='#ffffff')
            if hasattr(self, 'service_menu'):
                self.service_menu.configure(bg='#0f172a', fg='#ffffff', activebackground='#1e293b', activeforeground='#ffffff')

        # Обновляем виджеты перед отрисовкой, чтобы canvas имел размеры
        self.root.update_idletasks()

        # СНАЧАЛА отрисовываем дерево, ПОТОМ показываем диалоги
        self.refresh_view()
        self.root.update_idletasks()  # Обновляем после отрисовки

        # Теперь показываем приветственный диалог (если нужно)
        self.check_first_run()

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        # --- /ЗАГРУЗКА ---



    def on_person_enter(self, pid):
        """Выделение персоны при наведении курсора."""
        if pid != self.hovered_person_id:
            self.hovered_person_id = pid
            self.refresh_view()

    def on_person_leave(self, pid):
        """Снятие выделения при уходе курсора."""
        if self.hovered_person_id == pid:
            self.hovered_person_id = None
            self.refresh_view()

    def on_person_click(self, pid):
        """Устанавливает персону как центр дерева. Показывает только её ветку. Места на холсте не меняются."""
        if pid is None or pid not in self.model.get_all_persons():
            return
        # Единая «выбранная» персона для меню и редактора
        self.last_selected_person_id = pid
        # Устанавливаем центр
        self.model.current_center = pid

        # Обновляем метку центра
        center_person = self.model.get_person(pid)
        if center_person:
            self.center_label.config(text=f"Центр: {center_person.display_name()}")

        # Сбрасываем режим фокуса (предки видны по умолчанию)
        self.focus_mode_active = False

        # Перерисовка без пересчёта раскладки — выбранная персона остаётся на месте; не центрируем её на экране
        already_placed = any(str(k) == str(pid) for k in self.coords)
        if not already_placed:
            self._skip_centering_once = True
        self.refresh_view(skip_layout=already_placed)
        
        # Плавное центрирование на персоне (как в web-версии)
        self.center_canvas_on_person_animated(pid)

    def on_person_double_click(self, pid):
        """Двойной клик по персоне: выбор и открытие редактора."""
        persons = self.model.get_all_persons()
        key = next((k for k in persons if str(k) == str(pid)), pid)
        if key not in persons:
            return
        self.last_selected_person_id = key
        self.model.current_center = key
        center_person = self.model.get_person(key)
        if center_person:
            self.center_label.config(text=f"Центр: {center_person.display_name()}")
        self.edit_person()

    def center_canvas_on_person_animated(self, pid, duration=600):
        """
        Плавное центрирование холста на персоне (как в web-версии).
        
        Args:
            pid: ID персоны
            duration: Длительность анимации в мс
        """
        if pid is None or str(pid) not in self.coords:
            return
        
        # Получаем координаты персоны
        x, y = self.coords[str(pid)]
        
        # Получаем размеры холста и контента
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            bbox = self.canvas.bbox("all")
            
            if not bbox:
                return
            
            bbox_x0, bbox_y0, bbox_x2, bbox_y2 = bbox
            content_width = bbox_x2 - bbox_x0
            content_height = bbox_y2 - bbox_y0
            
            if content_width <= 0 or content_height <= 0:
                return
            
            # Вычисляем целевую позицию
            target_scroll_x = ((x - bbox_x0) - canvas_width / 2) / content_width
            target_scroll_y = ((y - bbox_y0) - canvas_height / 2) / content_height
            
            # Ограничиваем [0, 1]
            target_scroll_x = max(0, min(1, target_scroll_x))
            target_scroll_y = max(0, min(1, target_scroll_y))
            
            # Текущая позиция
            start_scroll_x = self.canvas.xview()[0]
            start_scroll_y = self.canvas.yview()[0]
            
            # Проверяем, нужно ли перемещать
            if abs(target_scroll_x - start_scroll_x) < 0.01 and abs(target_scroll_y - start_scroll_y) < 0.01:
                return
            
            # Анимация
            start_time = self.root.tk.call('clock', 'milliseconds')
            
            def animate():
                current_time = self.root.tk.call('clock', 'milliseconds')
                elapsed = current_time - start_time
                progress = min(elapsed / duration, 1.0)
                
                # Ease-in-out cubic
                eased = 4 * progress * progress * progress if progress < 0.5 else 1 - pow(-2 * progress + 2, 3) / 2
                
                current_scroll_x = start_scroll_x + (target_scroll_x - start_scroll_x) * eased
                current_scroll_y = start_scroll_y + (target_scroll_y - start_scroll_y) * eased
                
                self.canvas.xview_moveto(current_scroll_x)
                self.canvas.yview_moveto(current_scroll_y)
                
                if progress < 1.0:
                    self.root.after(16, animate)  # ~60 FPS
            
            animate()
            
        except Exception as e:
            print(f"[ANIMATION] Error: {e}")

    def check_first_run(self):
        """Если дерево пустое (новый пользователь после входа) — предлагаем заполнить свои данные."""
        persons = self.model.get_all_persons()
        if persons:
            return  # У пользователя уже есть данные
        # Для многопользовательского режима: пустое дерево = новый пользователь
        if self.username:
            self.root.after(100, self.show_welcome_dialog)
            return
        # Без логина (режим без входа): проверяем старый флаг в user_settings.json
        settings_file = "user_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if settings.get("first_run_completed", False):
                        return
            except Exception:
                pass
        self.root.after(100, self.show_welcome_dialog)

    def show_welcome_dialog(self):
        """Показывает диалог приветствия и регистрации нового пользователя."""
        welcome = tk.Toplevel(self.root)
        welcome.title("Добро пожаловать в Генеалогическое Древо!")
        welcome.geometry("500x480")
        welcome.resizable(False, False)
        welcome.transient(self.root)
        welcome.grab_set()

        # Центрируем окно
        welcome.update_idletasks()
        x = (self.root.winfo_screenwidth() - welcome.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - welcome.winfo_height()) // 2
        welcome.geometry(f"+{x}+{y}")

        # Заголовок (для нового пользователя после входа или первого запуска)
        tk.Label(welcome, text="Добро пожаловать! Создайте свою первую запись в древе",
                 font=("Arial", 14, "bold"), pady=10).pack()

        tk.Label(welcome, text="Заполните свои данные (это будет ваша карточка в дереве):",
                 font=("Arial", 10), pady=5).pack()

        # Фрейм для полей ввода
        form_frame = tk.Frame(welcome, padx=20, pady=10)
        form_frame.pack(fill="both", expand=True)

        # Поля ввода
        fields = {}

        # Имя
        tk.Label(form_frame, text="Имя*", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=5)
        fields['first_name'] = tk.Entry(form_frame, width=30)
        fields['first_name'].grid(row=0, column=1, pady=5, sticky="w")
        self._enable_copy_paste(fields['first_name'])

        # Фамилия
        tk.Label(form_frame, text="Фамилия*", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        fields['last_name'] = tk.Entry(form_frame, width=30)
        fields['last_name'].grid(row=1, column=1, pady=5, sticky="w")
        self._enable_copy_paste(fields['last_name'])

        # Отчество (опционально)
        tk.Label(form_frame, text="Отчество", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
        fields['patronymic'] = tk.Entry(form_frame, width=30)
        fields['patronymic'].grid(row=2, column=1, pady=5, sticky="w")
        self._enable_copy_paste(fields['patronymic'])

        # Дата рождения
        tk.Label(form_frame, text="Дата рождения", font=("Arial", 10)).grid(row=3, column=0, sticky="w", pady=5)
        fields['birth_date'] = tk.Entry(form_frame, width=30)
        fields['birth_date'].grid(row=3, column=1, pady=5, sticky="w")
        fields['birth_date'].insert(0, "")
        fields['birth_date'].bind("<KeyPress>", self._date_entry_keypress)
        fields['birth_date'].bind("<<Paste>>", lambda e, ent=fields['birth_date']: self._date_entry_on_paste(ent))
        fields['birth_date'].bind("<FocusOut>", self.normalize_date_on_focusout)

        # Пол
        tk.Label(form_frame, text="Пол*", font=("Arial", 10)).grid(row=4, column=0, sticky="w", pady=5)
        gender_var = tk.StringVar(value="Мужской")
        gender_frame = tk.Frame(form_frame)
        gender_frame.grid(row=4, column=1, sticky="w", pady=5)
        tk.Radiobutton(gender_frame, text="Мужской", variable=gender_var, value="Мужской").pack(side="left", padx=5)
        tk.Radiobutton(gender_frame, text="Женский", variable=gender_var, value="Женский").pack(side="left", padx=5)
        fields['gender'] = gender_var

        # Место рождения (предзаполнено для Беларуси)
        tk.Label(form_frame, text="Место рождения", font=("Arial", 10)).grid(row=5, column=0, sticky="w", pady=5)
        fields['birth_place'] = tk.Entry(form_frame, width=30)
        fields['birth_place'].grid(row=5, column=1, pady=5, sticky="w")
        fields['birth_place'].insert(0, "Минск, Беларусь")

        # Примечание
        tk.Label(welcome, text="* — обязательные поля",
                 font=("Arial", 8), fg="gray", pady=5).pack()

        # Кнопка (только "Создать", без отмены)
        btn_frame = tk.Frame(welcome, pady=15)
        btn_frame.pack(fill="x")

        def on_submit():
            # Валидация
            if not fields['first_name'].get().strip():
                messagebox.showerror("Ошибка", "Поле 'Имя' обязательно для заполнения")
                return
            if not fields['last_name'].get().strip():
                messagebox.showerror("Ошибка", "Поле 'Фамилия' обязательно для заполнения")
                return

            # Создаём персону
            person_data = {
                'first_name': fields['first_name'].get().strip(),
                'last_name': fields['last_name'].get().strip(),
                'patronymic': fields['patronymic'].get().strip(),
                'birth_date': fields['birth_date'].get().strip(),
                'birth_place': fields['birth_place'].get().strip(),
                'gender': fields['gender'].get(),
                'death_date': '',
                'death_place': '',
                'occupation': '',
                'notes': f"Создано при первом запуске программы {time.strftime('%d.%m.%Y')}"
            }

            # Сохраняем настройки
            self.save_user_settings(person_data)

            # Создаём персону в модели
            self.create_user_person_from_registration(person_data)

            welcome.destroy()
            self.statusbar.config(text=f"Добро пожаловать, {person_data['first_name']}! Ваша персона создана.")
            messagebox.showinfo("Успешно",
                                f"Персона «{person_data['last_name']} {person_data['first_name']}» создана!\nТеперь вы можете добавлять родственников через контекстное меню.")

        tk.Button(btn_frame, text="Создать персону", command=on_submit,
                  width=20, bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(padx=10)

        # Фокус на поле имени
        fields['first_name'].focus_set()
        welcome.bind("<Return>", lambda e: on_submit())

    def save_user_settings(self, person_data):
        """Сохраняет настройки пользователя и флаг первого запуска (файл свой у каждого пользователя)."""
        settings = {
            "first_run_completed": True,
            "user_person": {
                "first_name": person_data['first_name'],
                "last_name": person_data['last_name'],
                "patronymic": person_data['patronymic'],
                "birth_date": person_data['birth_date'],
                "birth_place": person_data['birth_place'],
                "gender": person_data['gender']
            },
            "window_settings": {
                "width": self.root.winfo_width(),
                "height": self.root.winfo_height(),
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y()
            },
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        settings_file = f"user_settings_{self.username}.json" if self.username else "user_settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек пользователя: {e}")

    def create_user_person_from_registration(self, person_data):
        """Создаёт персону в модели на основе данных регистрации."""
        # Генерируем уникальный ID
        person_id = str(len(self.model.persons) + 1)

        # Создаём объект персоны (ВАЖНО: используем атрибуты name/surname, а не first_name/last_name!)
        new_person = Person(
            name=person_data['first_name'],  # ← name = first_name
            surname=person_data['last_name'],  # ← surname = last_name
            patronymic=person_data['patronymic'],
            birth_date=person_data['birth_date'],
            gender=person_data['gender']
        )
        new_person.id = person_id

        # Добавляем в модель
        self.model.persons[person_id] = new_person

        # Устанавливаем как центр дерева
        self.model.current_center = person_id

        # Обновляем отображение
        self.refresh_view()

        # Выбираем созданную персону
        self.last_selected_person_id = person_id

        # Автосохранение
        self.model.save_to_file()

        return person_id

    # --- Ввод дат ДД.ММ.ГГГГ с автоподстановкой точек и проверками ---
    @staticmethod
    def _date_digits_to_formatted(digits):
        """
        Из строки цифр (до 8) собирает дату день.месяц.год (ДД.ММ.ГГГГ при полной дате).
        Корректно обрабатывает частичный ввод: 1 -> 1, 12 -> 12, 123 -> 12.3, 1234 -> 12.34 и т.д.
        """
        digits = digits[:8]  # Ограничиваем 8-ю цифрами
        if not digits:
            return ""

        # Если ровно 8 цифр, пытаемся отформатировать как полную дату
        if len(digits) == 8:
            try:
                d, m = int(digits[:2]), int(digits[2:4])
                y = digits[4:8]
                # Проверяем день и месяц на валидность (грубую)
                if 1 <= d <= 31 and 1 <= m <= 12:
                    return f"{d:02d}.{m:02d}.{y}"
            except ValueError:
                pass  # Если парсинг не удался, переходим к стандартной логике форматирования ниже

        # --- ИСПРАВЛЕННАЯ ЛОГИКА ФОРМАТИРОВАНИЯ ---
        # Начинаем формировать строку, добавляя точки по мере накопления достаточного количества цифр.
        formatted_parts = []

        # Берем первые 2 цифры как день
        day_part = digits[:2]
        if day_part:
            formatted_parts.append(day_part)

        # Если введено 3 или 4 цифры, добавляем точку и следующие 2 цифры как месяц
        if 3 <= len(digits) <= 4:
            month_part = digits[2:4]
            if month_part:  # Проверяем, что часть месяца не пуста (на случай len==3)
                formatted_parts.append(month_part)
        elif len(digits) > 4:  # Если введено больше 4 цифр, формируем месяц и год
            # Месяц из 3-4 позиций
            month_part = digits[2:4]
            if month_part:
                formatted_parts.append(month_part)

            # Год из 5-8 позиций
            year_part = digits[4:8]
            if year_part:  # Проверяем, что часть года не пуста
                formatted_parts.append(year_part)

        # Соединяем части точками
        return ".".join(formatted_parts)

    def _enable_copy_paste(self, widget):
        """
        Включает копирование (Ctrl+C), вставку (Ctrl+V) и вырезание (Ctrl+X) для виджета Entry или Text.
        Использует буфер обмена главного окна и явную вставку/копирование.
        """
        # Буфер привязан к главному окну приложения
        try:
            root = self.root
        except AttributeError:
            root = widget.winfo_toplevel()
        is_text = widget.winfo_class() == "Text"

        def _clipboard_get():
            try:
                return root.clipboard_get()
            except tk.TclError:
                return ""

        def _clipboard_set(text):
            try:
                root.clipboard_clear()
                root.clipboard_append(text)
            except tk.TclError:
                pass

        def do_copy():
            try:
                if is_text:
                    if widget.tag_ranges(tk.SEL):
                        text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                        _clipboard_set(text)
                else:
                    if widget.selection_present():
                        i, j = widget.index(tk.SEL_FIRST), widget.index(tk.SEL_LAST)
                        text = widget.get(i, j)
                        _clipboard_set(text)
            except (Exception, tk.TclError):
                pass

        def do_cut():
            try:
                if is_text:
                    if widget.tag_ranges(tk.SEL):
                        text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                        _clipboard_set(text)
                        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    if widget.selection_present():
                        i, j = widget.index(tk.SEL_FIRST), widget.index(tk.SEL_LAST)
                        text = widget.get(i, j)
                        _clipboard_set(text)
                        widget.delete(i, j)
            except (Exception, tk.TclError):
                pass

        def do_paste():
            text = _clipboard_get()
            if not text:
                return
            try:
                if is_text:
                    try:
                        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        pass
                    widget.insert(tk.INSERT, text)
                else:
                    try:
                        if widget.selection_present():
                            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        pass
                    widget.insert(tk.INSERT, text)
            except Exception:
                pass

        def on_copy(e):
            do_copy()
            return "break"

        def on_cut(e):
            do_cut()
            return "break"

        def on_paste(e):
            do_paste()
            return "break"

        def on_select_all(e):
            try:
                if is_text:
                    widget.tag_add(tk.SEL, "1.0", tk.END)
                    widget.mark_set(tk.INSERT, tk.END)
                else:
                    widget.select_range(0, len(widget.get() or ""))
            except Exception:
                pass
            return "break"

        def on_paste_ev(e):
            do_paste()
            return "break"

        def on_copy_ev(e):
            do_copy()
            return "break"

        def on_cut_ev(e):
            do_cut()
            return "break"

        def has_selection():
            try:
                if is_text:
                    return bool(widget.tag_ranges(tk.SEL))
                return bool(widget.selection_present())
            except (tk.TclError, Exception):
                return False

        def ctrl_key_handler(e):
            # По keycode (физическая клавиша) — работает при любой раскладке (рус/англ)
            k = getattr(e, "keycode", None)
            if k is None:
                k = getattr(e, "keysym_num", 0)
            sym = (getattr(e, "keysym", "") or "").lower()
            if k == 86 or sym == "v":
                do_paste()
                return "break"
            if k == 67 or sym == "c":
                do_copy()
                return "break"
            if k == 88 or sym == "x":
                do_cut()
                return "break"
            if k == 65 or sym == "a":
                on_select_all(e)
                return "break"
            return None

        def show_context_menu(e):
            widget.focus_set()
            menu = tk.Menu(widget, tearoff=0)
            menu.add_command(label="Вставить", command=do_paste, state=tk.NORMAL if _clipboard_get() else tk.DISABLED)
            menu.add_command(label="Копировать", command=do_copy, state=tk.NORMAL if has_selection() else tk.DISABLED)
            menu.add_command(label="Вырезать", command=do_cut, state=tk.NORMAL if has_selection() else tk.DISABLED)
            menu.add_separator()
            menu.add_command(label="Выделить всё", command=lambda: on_select_all(None))
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()

        widget.bind("<Control-Key>", ctrl_key_handler)
        widget.bind("<<Paste>>", on_paste_ev)
        widget.bind("<<Copy>>", on_copy_ev)
        widget.bind("<<Cut>>", on_cut_ev)
        widget.bind("<Button-3>", show_context_menu)
        try:
            widget.bind("<Command-c>", on_copy)
            widget.bind("<Command-v>", on_paste)
            widget.bind("<Command-x>", on_cut)
            widget.bind("<Command-a>", on_select_all)
        except tk.TclError:
            pass

    def _date_entry_keypress(self, event):
        """
        Обрабатывает ввод в поле даты: только цифры и управляющие клавиши.
        Сразу вставляет разделители (точки) и не даёт ввести лишнее.
        Читаем/пишем через textvariable при наличии — иначе ttk.Entry с StringVar теряет цифры после 2-й.
        """
        if event.keysym in ('Tab', 'Return', 'Escape', 'Up', 'Down', 'Left', 'Right'):
            return None
        if (event.state & 0x4):
            return None

        entry = event.widget
        try:
            tv = entry.cget("textvariable")
            old = entry.getvar(tv) if tv else entry.get()
            cursor = int(entry.index(tk.INSERT))
        except Exception:
            return None

        digits_old = "".join(c for c in (old or "") if c.isdigit())
        digit_pos = sum(1 for i in range(min(cursor, len(old))) if old[i].isdigit())

        if event.keysym == 'BackSpace':
            if digit_pos <= 0 or not digits_old:
                return None
            new_digits = digits_old[:digit_pos - 1] + digits_old[digit_pos:]
        elif event.keysym == 'Delete':
            if digit_pos >= len(digits_old) or not digits_old:
                return None
            new_digits = digits_old[:digit_pos] + digits_old[digit_pos + 1:]
        elif event.char and event.char.isdigit():
            if len(digits_old) >= 8:
                return "break"
            new_digits = digits_old[:digit_pos] + event.char + digits_old[digit_pos:]
        else:
            return "break" if event.char else None

        formatted = self._date_digits_to_formatted(new_digits)
        entry.delete(0, tk.END)
        entry.insert(0, formatted)
        try:
            tv = entry.cget("textvariable")
            if tv:
                entry.setvar(tv, formatted)
        except Exception:
            pass
        if event.keysym == 'BackSpace':
            target_digit = max(0, digit_pos - 1)
        elif event.keysym == 'Delete':
            target_digit = digit_pos
        else:
            target_digit = digit_pos + 1
        new_cursor = len(formatted)
        n = 0
        for i, ch in enumerate(formatted):
            if ch.isdigit():
                n += 1
                if n >= target_digit:
                    new_cursor = i + 1
                    break
        try:
            entry.icursor(min(new_cursor, len(formatted)))
        except Exception:
            pass
        return "break"

    def _date_entry_apply_format(self, entry):
        """Применяет формат ДД.ММ.ГГГГ к полю (для вставки из буфера)."""
        try:
            tv = entry.cget("textvariable")
            old = entry.getvar(tv) if tv else entry.get()
        except Exception:
            return
        digits = "".join(c for c in (old or "") if c.isdigit())[:8]
        formatted = self._date_digits_to_formatted(digits)
        if formatted == (old or ""):
            return
        entry.delete(0, tk.END)
        entry.insert(0, formatted)
        try:
            if tv:
                entry.setvar(tv, formatted)
        except Exception:
            pass
        try:
            entry.icursor(len(formatted))
        except Exception:
            pass

    def _date_entry_on_paste(self, entry):
        """После вставки: через 50 ms форматируем (виджет уже обновился)."""
        entry.after(50, lambda: self._date_entry_apply_format(entry))

    def normalize_date_on_focusout(self, event):
        """
        При уходе фокуса: оставляем только цифры, форматируем в ДД.ММ.ГГГГ.
        Проверки: день 1–31, месяц 1–12, год 4 цифры; невалидное очищаем; полную дату нормализуем с нулями.
        """
        entry = event.widget
        try:
            tv = entry.cget("textvariable")
            value = (entry.getvar(tv) if tv else entry.get()).strip()
        except Exception:
            return None
        if not value:
            return None

        digits = "".join(c for c in value if c.isdigit())[:8]
        formatted = self._date_digits_to_formatted(digits)
        if formatted != value:
            entry.delete(0, tk.END)
            entry.insert(0, formatted)
            try:
                tv = entry.cget("textvariable")
                if tv:
                    entry.setvar(tv, formatted)
            except Exception:
                pass
            value = formatted

        if not value:
            return None
        parts = [p.strip() for p in value.split(".")]
        if len(parts) == 1:
            if parts[0].isdigit() and 1 <= int(parts[0]) <= 31:
                return None
        elif len(parts) == 2:
            if parts[0].isdigit() and parts[1].isdigit():
                d, m = int(parts[0]), int(parts[1])
                if 1 <= d <= 31 and 1 <= m <= 12:
                    return None
        elif len(parts) == 3:
            if self.model._validate_date(value):
                try:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    normalized = f"{day:02d}.{month:02d}.{year:04d}"
                    if normalized != value:
                        entry.delete(0, tk.END)
                        entry.insert(0, normalized)
                except ValueError:
                    pass
            return None

        entry.delete(0, tk.END)
        return None


    def show_context_menu(self, event):
        """Отображает контекстное меню при клике правой кнопкой мыши по карточке персоны."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item_ids = self.canvas.find_overlapping(x, y, x, y)
        clicked_pid = None
        for item_id in item_ids:
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("card_"):
                    clicked_pid = tag.split('_')[1]
                    break
            if clicked_pid is not None:
                break

        # По пустому полю — ничего не делаем
        if clicked_pid is None:
            return

        # Выбор персоны при правом клике: приводим id к ключу модели
        if clicked_pid is not None:
            persons = self.model.get_all_persons()
            key = next((k for k in persons if str(k) == str(clicked_pid)), None)
            if key is not None:
                self.last_selected_person_id = key
                self.model.current_center = key
                center_person = self.model.get_person(key)
                if center_person:
                    self.center_label.config(text=f"Центр: {center_person.display_name()}")
        else:
            self.last_selected_person_id = None

        # Обновляем пункты контекстного меню в зависимости от выбранной персоны
        person = self.model.get_person(self.last_selected_person_id) if self.last_selected_person_id else None

        # Очищаем подменю "Родственник"
        self.add_relative_menu.delete(0, 'end')

        if person:
            # --- ПРОВЕРКА НАЛИЧИЯ РОДИТЕЛЕЙ ---
            has_father = False
            has_mother = False
            for parent_id in person.parents:
                parent = self.model.get_person(parent_id)
                if parent:
                    if parent.gender == "Мужской":
                        has_father = True
                    elif parent.gender == "Женский":
                        has_mother = True
            # --- /ПРОВЕРКА НАЛИЧИЯ РОДИТЕЛЕЙ ---

            # Добавляем пункты в зависимости от пола персоны
            if person.gender == "Мужской":
                self.add_relative_menu.add_command(label="Жена...",
                                                   command=lambda
                                                       p=self.last_selected_person_id: self.add_spouse_dialog(p))
                self.add_relative_menu.add_command(label="Сын...",
                                                   command=lambda p=self.last_selected_person_id: self.add_child_dialog(
                                                       p, "Мужской"))
                self.add_relative_menu.add_command(label="Дочь...",
                                                   command=lambda p=self.last_selected_person_id: self.add_child_dialog(
                                                       p, "Женский"))
            else:
                self.add_relative_menu.add_command(label="Муж...",
                                                   command=lambda
                                                       p=self.last_selected_person_id: self.add_spouse_dialog(p))
                self.add_relative_menu.add_command(label="Сын...",
                                                   command=lambda p=self.last_selected_person_id: self.add_child_dialog(
                                                       p, "Мужской"))
                self.add_relative_menu.add_command(label="Дочь...",
                                                   command=lambda p=self.last_selected_person_id: self.add_child_dialog(
                                                       p, "Женский"))

            # Общие пункты для обоих полов — с проверкой наличия родителей
            if not has_father:
                self.add_relative_menu.add_command(label="Отец...",
                                                   command=lambda
                                                       p=self.last_selected_person_id: self.add_parent_dialog(p,
                                                                                                              "Мужской"))
            if not has_mother:
                self.add_relative_menu.add_command(label="Мать...",
                                                   command=lambda
                                                       p=self.last_selected_person_id: self.add_parent_dialog(p,
                                                                                                              "Женский"))

            self.add_relative_menu.add_command(label="Брат...",
                                               command=lambda p=self.last_selected_person_id: self.add_sibling_dialog(p,
                                                                                                                      "Мужской"))
            self.add_relative_menu.add_command(label="Сестра...",
                                               command=lambda p=self.last_selected_person_id: self.add_sibling_dialog(p,
                                                                                                                      "Женский"))

        # Отображаем контекстное меню
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
            self.statusbar.config(text=constants.MSG_STATUS_CONTEXT_MENU_OPENED)
        finally:
            self.context_menu.grab_release()

    def _register_protocol(self):
        """Регистрирует протокол derevo:// для открытия из веб-версии."""
        try:
            from protocol_win import register_protocol
            if register_protocol():
                messagebox.showinfo("Протокол", "Протокол derevo:// успешно зарегистрирован.\nТеперь на веб-странице можно нажать «Открыть в приложении».")
            else:
                messagebox.showerror("Ошибка", "Регистрация протокола возможна только в Windows.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def open_web_version(self):
        """Открывает веб-версию приложения в браузере."""
        import webbrowser
        url = constants.WEB_VERSION_URL
        webbrowser.open(url)

    def open_admin_panel(self):
        """Открыть админ-панель (только для Андрея Емельянова)"""
        # Проверяем, что вошёл Андрей Емельянов
        if self.username != "Емельянов Андрей" and self.username != "Андрей Емельянов":
            messagebox.showerror("Доступ запрещён",
                "Админ-панель доступна только для пользователя:\nАндрей Емельянов")
            return

        # Открываем ПОЛНУЮ админ-панель с данными с сервера
        # Если пароль не сохранён, будет запрошен у пользователя
        from admin_dashboard_full import open_admin_dashboard
        open_admin_dashboard(self.username, None)

    def open_user_dashboard(self):
        """Открыть персональную панель пользователя (данные с сервера)"""
        # Получаем пароль из файла запоминания
        try:
            from auth import _load_remember
            remembered = _load_remember()
            password = remembered.get("password", "")
            
            if not password:
                # Если пароля нет, запрашиваем у пользователя
                dialog = tk.Toplevel(self.root)
                dialog.title("👤 Вход в панель")
                dialog.transient(self.root)
                dialog.grab_set()
                
                ttk.Label(dialog, text="Введите пароль для доступа к панели", padding=10).pack()
                
                password_var = tk.StringVar()
                password_entry = ttk.Entry(dialog, textvariable=password_var, show="•", width=30)
                password_entry.pack(padx=20, pady=10)
                password_entry.focus_set()
                
                def submit():
                    pwd = password_var.get()
                    if pwd:
                        dialog.destroy()
                        self._do_open_user_dashboard(pwd)
                
                password_entry.bind("<Return>", lambda e: submit())
                
                btn_frame = ttk.Frame(dialog)
                btn_frame.pack(pady=10)
                ttk.Button(btn_frame, text="Войти", command=submit).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)
                
                dialog.wait_window()
            else:
                self._do_open_user_dashboard(password)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть панель: {e}")

    def _do_open_user_dashboard(self, password):
        """Открывает панель пользователя с указанным паролем"""
        try:
            from user_dashboard import open_user_dashboard
            open_user_dashboard(self.username, password)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть панель: {e}")
    
    def show_local_admin_panel(self):
        """Локальная админ-панель (резервная, если сервер недоступен)"""
        admin_window = tk.Toplevel(self.root)
        admin_window.title("👑 Админ-панель (Локальная)")
        admin_window.geometry("800x600")
        
        # Заголовок
        title_frame = ttk.Frame(admin_window)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(title_frame, text="👑 Админ-панель", 
                 font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="(Сервер недоступен)", 
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Button(title_frame, text="❌ Закрыть", 
                  command=admin_window.destroy).pack(side=tk.RIGHT)
        
        # Вкладки
        notebook = ttk.Notebook(admin_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Вкладка 1: Статистика
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Статистика")
        self.create_local_stats_tab(stats_frame)
        
        # Вкладка 2: Пользователи
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="👥 Пользователи")
        self.create_local_users_tab(users_frame)
    
    def create_local_stats_tab(self, parent):
        """Вкладка локальной статистики"""
        # Карточки
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(fill=tk.X, padx=20, pady=20)
        
        persons_count = len(self.model.get_all_persons())
        marriages_count = len(self.model.get_marriages())
        
        cards = [
            ("👤 Персон", str(persons_count)),
            ("💍 Браков", str(marriages_count)),
            ("👥 Пользователей", "2"),
            ("📁 Файлов", "2"),
        ]
        
        for i, (label, value) in enumerate(cards):
            card = ttk.LabelFrame(cards_frame, text=label, padding=20)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)
            ttk.Label(card, text=value, font=("Segoe UI", 24, "bold")).pack()
        
        # Информация
        info_frame = ttk.LabelFrame(parent, text="📁 Файлы данных", padding=20)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        files_info = [
            f"Гость: family_tree_Гость.json ({persons_count} персон)",
            f"Андрей Емельянов: family_tree_Емельянов Андрей.json ({persons_count} персон)",
        ]
        
        for info in files_info:
            ttk.Label(info_frame, text=info).pack(anchor=tk.W)
        
        # Кнопки
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="🔄 Обновить", 
                  command=lambda: self.create_local_stats_tab(parent)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 Открыть папку с данными", 
                  command=self.open_data_folder).pack(side=tk.LEFT, padx=5)
    
    def create_local_users_tab(self, parent):
        """Вкладка пользователей"""
        # Таблица
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("login", "file", "persons", "marriages")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        tree.heading("login", text="Пользователь")
        tree.heading("file", text="Файл")
        tree.heading("persons", text="Персон")
        tree.heading("marriages", text="Браков")
        
        tree.column("login", width=200)
        tree.column("file", width=300)
        tree.column("persons", width=100, anchor=tk.CENTER)
        tree.column("marriages", width=100, anchor=tk.CENTER)
        
        # Добавляем пользователей
        users_data = [
            ("Гость", "family_tree_Гость.json", "42", "14"),
            ("Емельянов Андрей", "family_tree_Емельянов Андрей.json", "42", "11"),
        ]
        
        for user in users_data:
            tree.insert("", tk.END, values=user)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📂 Открыть файл", 
                  command=self.open_user_file).pack(side=tk.LEFT, padx=5)
    
    def open_data_folder(self):
        """Открыть папку с данными"""
        import os
        os.startfile(os.getcwd())
    
    def open_user_file(self):
        """Открыть файл пользователя"""
        import os
        import subprocess
        filename = "family_tree_Емельянов Андре��������.json"
        filepath = os.path.join(os.getcwd(), filename)
        if os.path.exists(filepath):
            subprocess.run(["notepad", filepath])
        else:
            messagebox.showerror("Ошибка", f"Файл не найден:\n{filepath}")

    def auto_sync_on_startup(self):
        """Автоматическая синхронизация при запуске — загрузка дерева с сервера"""
        from sync_client import get_sync_client, USER_CREDENTIALS

        if not self.username:
            print(f"[SYNC] No username, skipping sync")
            return

        credentials = USER_CREDENTIALS.get(self.username)
        if not credentials:
            print(f"[SYNC] No credentials for user: {self.username}")
            return

        try:
            client = get_sync_client()

            # Всегда логинимся заново (токены быстро истекают)
            print(f"[SYNC] Login: {credentials['login']}")
            result = client.login(credentials['login'], credentials['password'], remember=True)

            if not result.get('token'):
                print(f"[SYNC] Login failed: {result}")
                return

            print(f"[SYNC] Login OK, token: {result.get('token', '')[:20]}...")

            # === ОБНОВЛЯЕМ last_sync НА СЕРВЕРЕ (чтобы админ-панель видела онлайн) ===
            print(f"[SYNC] Updating last_sync timestamp...")
            try:
                import urllib.request
                import json
                from sync_client import DEFAULT_SERVER_URL
                
                # Отправляем запрос на обновление last_sync
                req = urllib.request.Request(
                    f"{DEFAULT_SERVER_URL}/api/sync/upload",
                    data=json.dumps({
                        'tree': {'persons': {}, 'marriages': []},  # Пустое дерево, только для обновления last_sync
                        'tree_name': f"Дерево {self.username}"
                    }).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {result.get("token")}'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"[SYNC] last_sync updated successfully via upload")
                    else:
                        print(f"[SYNC] last_sync update returned {response.status}")
            except Exception as e:
                print(f"[SYNC] last_sync update error: {e}")
            # === /ОБНОВЛЯЕМ last_sync ===

            # Сначала пробуем загрузить дерево с сервера
            print(f"[SYNC] Downloading tree from server...")
            try:
                server_data = client.download_tree()

                if server_data and 'tree' in server_data:
                    tree_data = server_data.get('tree', {})
                    persons = tree_data.get('persons', {})

                    if persons:
                        print(f"[SYNC] Downloaded tree with {len(persons)} persons")
                        # Загружаем дерево из сервера
                        self._load_tree_from_server(server_data)
                        
                        # Принудительно обновляем интерфейс
                        self.root.update_idletasks()
                        self.refresh_view()
                        
                        print(f"[SYNC] Tree loaded from server successfully")
                        return  # Успешно загрузили с сервера
                    else:
                        print(f"[SYNC] Server tree is empty (no persons)")
                else:
                    print(f"[SYNC] No tree on server (response: {server_data})")
            except Exception as e:
                print(f"[SYNC] Download error: {e}")
                import traceback
                traceback.print_exc()
                # Если ошибка загрузки — продолжаем с локальным деревом

            # Если сервер пуст или ошибка — загружаем локальное дерево на сервер
            print(f"[SYNC] Uploading local tree...")
            result = client.upload_tree(self.model, f"Дерево {self.username}")

            if result and (result.get('success') or result.get('message')):
                print(f"[SYNC] Upload OK: {result}")
            else:
                print(f"[SYNC] Upload result: {result}")

        except Exception as e:
            print(f"[SYNC] Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_tree_from_server(self, server_data):
        """Загрузить дерево из данных сервера"""
        tree_data = server_data.get('tree', {})
        persons = tree_data.get('persons', {})
        marriages_data = tree_data.get('marriages', [])  # ����ервер возвращает список

        # Очища��м текущее дерево
        self.model.persons.clear()
        self.model.marriages.clear()

        # Добавляем персоны из сервера
        for pid, pdata in persons.items():
            from models import Person
            p = Person(
                name=pdata.get('name', ''),
                surname=pdata.get('surname', ''),
                patronymic=pdata.get('patronymic', ''),
                birth_date=pdata.get('birth_date', ''),
                gender=pdata.get('gender', ''),
                is_deceased=pdata.get('is_deceased', False),
                death_date=pdata.get('death_date', ''),
            )
            p.id = pid
            p.parents = set(pdata.get('parents', []))
            p.children = set(pdata.get('children', []))
            p.spouse_ids = set(pdata.get('spouse_ids', []))
            self.model.persons[pid] = p

        # === ЗАГРУЖАЕМ БРАКИ ИЗ СЕРВЕРА (список словарей) ===
        marriages_loaded = 0
        if marriages_data and isinstance(marriages_data, list):
            for marriage_item in marriages_data:
                # marriage_item = {'persons': [h_id, w_id], 'date': '...'}
                persons_in_marriage = marriage_item.get('persons', [])
                if len(persons_in_marriage) == 2:
                    h_id, w_id = str(persons_in_marriage[0]), str(persons_in_marriage[1])
                    marriage_date = marriage_item.get('date', '')
                    self.model.marriages[(h_id, w_id)] = {'date': marriage_date}
                    marriages_loaded += 1
            print(f"[SYNC_LOAD] Загружено {marriages_loaded} браков из сервера")
        else:
            print(f"[SYNC_LOAD] Браки не найдены в серверных данных (format: {type(marriages_data)})")
        # === /ЗАГРУЖАЕМ БРАКИ ===

        # Сохраняем загруженное дерево в локальный файл
        self.model.save_to_file()
        print(f"[SYNC_LOAD] Дерево сохранено в {self.model.data_file}")

        # Обновляем интерфейс
        self.refresh_view()

    def _view_person_by_id(self, person_id):
        """Просмотр персоны по ID."""
        old_center = self.model.current_center
        old_selected = self.last_selected_person_id
        self.model.current_center = str(person_id)
        self.last_selected_person_id = str(person_id)
        try:
            self.view_person()
        finally:
            self.model.current_center = old_center
            self.last_selected_person_id = old_selected

    def _edit_person_by_id(self, person_id, current_dialog):
        """Редактирование персоны по ID (закрывает текущий диалог)."""
        current_dialog.destroy()
        old_center = self.model.current_center
        old_selected = self.last_selected_person_id
        self.model.current_center = str(person_id)
        self.last_selected_person_id = str(person_id)
        try:
            self.edit_person()
        finally:
            self.model.current_center = old_center
            self.last_selected_person_id = old_selected

    def _quick_add_spouse(self, person_id, current_dialog):
        """Быстрое добавление супруга."""
        current_dialog.destroy()
        old_center = self.model.current_center
        self.model.current_center = str(person_id)
        try:
            self.add_spouse_dialog(person_id)
        finally:
            self.model.current_center = old_center

    def _quick_add_child(self, person_id, current_dialog):
        """Быстрое добавление ребёнка."""
        current_dialog.destroy()
        old_center = self.model.current_center
        self.model.current_center = str(person_id)
        try:
            # Спрашиваем пол ребёнка
            gender = simpledialog.askstring("Пол ребёнка", "Введите пол ребёнка (Мужской/Женский):", 
                                           initialvalue="Мужской")
            if gender:
                if gender.lower() in ["м", "мужской", "male"]:
                    self.add_child_dialog(person_id, "Мужской")
                elif gender.lower() in ["ж", "женский", "female"]:
                    self.add_child_dialog(person_id, "Женский")
                else:
                    messagebox.showerror("Ош����бка", "Неверно указ������н пол")
        finally:
            self.model.current_center = old_center

    def _quick_add_parent(self, person_id, current_dialog):
        """Быстрое добавление родите������������я."""
        current_dialog.destroy()
        old_center = self.model.current_center
        self.model.current_center = str(person_id)
        try:
            # Спрашиваем, кого добавить
            parent_type = messagebox.askquestion("Тип родителя", "Кого хотите добавить?\n\nДа - Мать\nНет - Отец",
                                                icon=messagebox.QUESTION)
            if parent_type == 'yes':
                self.add_parent_dialog(person_id, "Женский")
            else:
                self.add_parent_dialog(person_id, "Мужской")
        finally:
            self.model.current_center = old_center

    def on_exit(self):
        """Обработка закрытия приложения."""
        # Автосохранение на сервер при выходе
        self._auto_save_on_exit()
        
        # Проверяем, были ли изменения
        if self.model and self.model.modified:
            result = messagebox.askyesnocancel(
                "Сохранить изменения?",
                "Данные были изменены. Сохранить перед выходом?"
            )
            if result is None:  # Нажата Отмена
                return  # Выходим из функции, НЕ закрываем приложение
            elif result:  # Нажата Да
                self.save_file()

        # Очистка кэша изображений
        self.photo_images.clear()

        # Завершение работы Tkinter
        self.root.quit()
        self.root.destroy()

    def schedule_auto_save(self):
        """Планирует автосохранение через заданный интервал."""
        self.auto_save_timer = self.root.after(self.auto_save_interval, self._do_auto_save)

    def _do_auto_save(self):
        """Выполняет автосохранение если есть изменения."""
        if self.model and self.model.modified:
            try:
                self.model.save_to_file()
                if hasattr(self, 'statusbar'):
                    self.statusbar.config(text=f"Автосохранение выполнено ({datetime.now().strftime('%H:%M:%S')})")
            except Exception as e:
                print(f"[AUTO_SAVE] Error: {e}")
        # Планируем следующее автосохранение
        self.schedule_auto_save()

    def _auto_save_on_exit(self):
        """Автосохранение на сервер при выходе (ВСЕГДА загружаем изменения на сервер)"""
        from sync_client import get_sync_client

        if not self.username:
            return

        try:
            client = get_sync_client()
            if client.is_logged_in():
                print(f"[SYNC] Auto-save on exit...")
                # Загружаем текущее дерево на сервер (перезаписываем)
                result = client.upload_tree(self.model, f"Дерево {self.username}")
                if result and result.get('success'):
                    print(f"[SYNC] Auto-save OK")
                else:
                    print(f"[SYNC] Auto-save result: {result}")
            else:
                print(f"[SYNC] Not logged in, skipping auto-save")
        except Exception as e:
            print(f"[SYNC] Auto-save error: {e}")


    def update_adaptive_settings(self):
        """Обновляет размеры элементов в зависимости от ширины окна."""
        width = self.root.winfo_width()
        if width < constants.MIN_WINDOW_WIDTH:
            factor = 0.7
        else:
            factor = 1.0

        self.CARD_WIDTH = int(self.BASE_CARD_WIDTH * factor)
        self.CARD_HEIGHT = int(self.BASE_CARD_HEIGHT * factor)
        self.PARENT_LINE_WIDTH = int(self.BASE_PARENT_LINE_WIDTH * factor)
        self.MARRIAGE_LINE_WIDTH = int(self.BASE_MARRIAGE_LINE_WIDTH * factor)

    def zoom(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        old_scale = self.current_scale
        if event.delta > 0:
            self.current_scale *= 1.1
            self.statusbar.config(text=constants.MSG_STATUS_ZOOM_IN)
        elif event.delta < 0:
            self.current_scale /= 1.1
            self.current_scale = max(0.1, self.current_scale)
            self.statusbar.config(text=constants.MSG_STATUS_ZOOM_OUT)
        self.offset_x = canvas_x - (canvas_x - self.offset_x) * (self.current_scale / old_scale)
        self.offset_y = canvas_y - (canvas_y - self.offset_y) * (self.current_scale / old_scale)
        self.refresh_view()

    def start_pan(self, event):
        """Начало перетаскивания холста"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = False  # Флаг устанавливается только при реальном движении

    def pan(self, event):
        """Перемещение холста при удержании ЛКМ с синхронным движением карточек и курсора"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        # Определяем начало перетаскивания (только при реальном движении)
        if not self.is_dragging and (dx * dx + dy * dy > self.DRAG_THRESHOLD * self.DRAG_THRESHOLD):
            self.is_dragging = True
            self.statusbar.config(text=constants.MSG_STATUS_PAN_ACTIVE)
            self.root.focus_set()  # Снимаем фокус с элементов
            print(f"[PAN] Начало перетаскивания, units={len(self.units)}, coords={len(self.coords)}")

        if self.is_dragging:
            # ИСПРАВЛЕНО: карточки двигаются СИНХРОННО с курсором (без минуса!)

            self.offset_x += dx
            self.offset_y += dy

            # Обновляем стартовую точку для плавного продолжения
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            print(f"[PAN] Перетаскивание: offset=({self.offset_x}, {self.offset_y}), units={len(self.units)}, coords={len(self.coords)}")
            # Мгновенное обновление без задержек (skip_layout=True чтобы не пересчитывать раскладку)
            self.refresh_view(skip_layout=True)

    def stop_pan(self, event):
        """Завершение перетаскивания"""
        if self.is_dragging:
            self.is_dragging = False
            self.statusbar.config(text=constants.MSG_STATUS_PAN_INACTIVE)

    def on_canvas_click(self, event):
        if self.is_dragging:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item_ids = self.canvas.find_overlapping(x, y, x, y)
        clicked_pid = None

        for item_id in item_ids:
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("card_"):
                    clicked_pid = tag.split('_')[1]
                    break
            if clicked_pid:
                break

        if clicked_pid:
            persons = self.model.get_all_persons()
            key = next((k for k in persons if str(k) == str(clicked_pid)), clicked_pid)
            self.on_person_click(key)

    def draw_person_card(self, pid, person, x, y):
        """
        Отрисовывает карточку персоны с фото.
        Гарантирует сохранение ссылок на изображения для предотвращения удаления сборщиком мусора.
        """
        # === ЦВЕТ ФОНА КАРТОЧКИ (в единой палитре) ===
        if pid == self.model.current_center:
            bg_color = constants.CENTER_COLOR
        elif pid == self.hovered_person_id:
            bg_color = "#2563eb" if person.gender == "Мужской" else "#be185d"  # Ярче при наведении
        else:
            bg_color = constants.MALE_COLOR if person.gender == "Мужской" else constants.FEMALE_COLOR
        if person.is_deceased:
            bg_color = constants.DECEASED_COLOR

        scaled_x = x * self.current_scale + self.offset_x
        scaled_y = y * self.current_scale + self.offset_y

        # === МАСШТАБИРУЕМЫЕ РАЗМЕРЫ КАРТОЧКИ ===
        card_width_scaled = self.CARD_WIDTH * self.current_scale
        card_height_scaled = self.CARD_HEIGHT * self.current_scale
        line_width_scaled = max(1, int(2 * self.current_scale))
        is_hover = pid == self.hovered_person_id
        outline_color = constants.CARD_HOVER_BORDER if is_hover else constants.CARD_BORDER_COLOR
        outline_width = line_width_scaled * 2 if is_hover else line_width_scaled

        # === ФОН КАРТОЧКИ И РАМКИ ===
        card_tags = f"card_{pid}"
        left = scaled_x - card_width_scaled / 2
        right = scaled_x + card_width_scaled / 2
        top = scaled_y - card_height_scaled / 2
        bottom = scaled_y + card_height_scaled / 2
        inset = max(1, int(2 * self.current_scale))
        rim_inset = max(2, int(3 * self.current_scale))

        # Основной прямоугольник карточки
        self.canvas.create_rectangle(
            left, top, right, bottom,
            fill=bg_color,
            outline=outline_color,
            width=outline_width,
            tags=card_tags
        )
        # Тонкий внутренний контур (глубина, не перекрывает текст)
        self.canvas.create_rectangle(
            left + rim_inset, top + rim_inset, right - rim_inset, bottom - rim_inset,
            outline=constants.CARD_INNER_RIM,
            width=max(1, int(1 * self.current_scale)),
            tags=card_tags
        )
        # Разделитель между зоной фото и текстом
        # === ОТРИСОВКА ФОТО (с масштабированием позиции и размера) ===
        # Фото размещается в верхней трети карточки и масштабируется вместе с карточкой
        photo_y = scaled_y - card_height_scaled / 2 + card_height_scaled * 0.25
        photo_img = self.load_photo_image(person, self.current_scale)

        if photo_img:
            # Размер фото уже масштабирован в load_photo_image по current_scale
            self.canvas.create_image(
                scaled_x, photo_y,
                image=photo_img,
                anchor='center',
                tags=card_tags
            )
        else:
            # Иконка-заглушка с масштабированием
            icon_size = 20 * self.current_scale
            self.canvas.create_oval(
                scaled_x - icon_size, photo_y - icon_size,
                scaled_x + icon_size, photo_y + icon_size,
                fill=constants.CARD_PHOTO_PLACEHOLDER_FILL,
                outline=constants.CARD_PHOTO_PLACEHOLDER_OUTLINE,
                width=max(1, int(1 * self.current_scale)),
                tags=card_tags
            )
            self.canvas.create_text(
                scaled_x, photo_y,
                text="📷",
                font=("Arial", int(14 * self.current_scale)),
                fill=constants.CARD_PHOTO_PLACEHOLDER_OUTLINE,
                tags=card_tags
            )

        # === ОТРИСОВКА ТЕКСТА (все смещения масштабируются) ===
        text_y_start = scaled_y - card_height_scaled / 2 + card_height_scaled * 0.55

        # Имя
        self.canvas.create_text(
            scaled_x, text_y_start,
            text=person.name,
            font=("Arial", int(10 * self.current_scale), "bold"),
            fill=constants.CARD_TEXT_PRIMARY,
            anchor="n",
            tags=card_tags
        )

        # Отчество
        y_offset = 14 * self.current_scale
        if person.patronymic.strip():
            self.canvas.create_text(
                scaled_x, text_y_start + y_offset,
                text=person.patronymic,
                font=("Arial", int(9 * self.current_scale)),
                fill=constants.CARD_TEXT_SECONDARY,
                anchor="n",
                tags=card_tags
            )
            y_offset += 14 * self.current_scale

        # Фамилия
        self.canvas.create_text(
            scaled_x, text_y_start + y_offset,
            text=person.surname,
            font=("Arial", int(10 * self.current_scale), "bold"),
            fill=constants.CARD_TEXT_PRIMARY,
            anchor="n",
            tags=card_tags
        )

        # Даты
        y_offset += 16 * self.current_scale
        if person.birth_date.strip():
            self.canvas.create_text(
                scaled_x, text_y_start + y_offset,
                text=f"р. {person.birth_date}",
                font=("Arial", int(8 * self.current_scale), "italic"),
                fill=constants.CARD_DATE_BIRTH,
                anchor="n",
                tags=card_tags
            )
            y_offset += 12 * self.current_scale

        if person.is_deceased and person.death_date.strip():
            self.canvas.create_text(
                scaled_x, text_y_start + y_offset,
                text=f"ум. {person.death_date}",
                font=("Arial", int(8 * self.current_scale), "italic"),
                fill=constants.CARD_DATE_DEATH,
                anchor="n",
                tags=card_tags
            )
            y_offset += 12 * self.current_scale

        # === СТЕПЕНЬ РОДСТВА (под карточкой, относительно выбранной персоны) ===
        if hasattr(self, 'relationships') and pid in self.relationships:
            relationship = self.relationships[pid]
            if relationship and relationship != "Я":
                self.canvas.create_text(
                    scaled_x, text_y_start + y_offset,
                    text=relationship,
                    font=("Arial", int(7 * self.current_scale), "italic"),
                    fill="#94a3b8",
                    anchor="n",
                    tags=card_tags
                )
        # === /СТЕПЕНЬ РОДСТВА ===

        # === ПРИВЯЗКА СОБЫТИЙ ===
        self.canvas.tag_bind(card_tags, "<Enter>", lambda e, p_id=pid: self.on_person_enter(p_id))
        self.canvas.tag_bind(card_tags, "<Leave>", lambda e, p_id=pid: self.on_person_leave(p_id))
        self.canvas.tag_bind(card_tags, "<Button-1>", lambda e, p_id=pid: self.on_person_click(p_id))
        self.canvas.tag_bind(card_tags, "<Double-Button-1>", lambda e, p_id=pid: self.on_person_double_click(p_id))

    def clear_photo_cache(self):
        """Очищает кэш изображений для освобо��дения памяти."""
        self.photo_images.clear()
        print("Кэш изображений очищен.")
    
    def trim_photo_cache(self, max_size=100):
        """Очищает старые изображения при превышении лимита кэша."""
        if len(self.photo_images) > max_size:
            keys_to_remove = list(self.photo_images.keys())[:max_size // 2]
            for key in keys_to_remove:
                del self.photo_images[key]
            print(f"Кэш изображений очищен до {len(self.photo_images)} записей.")

    def load_photo_image(self, person, scale=1.0):
        """
        Единый метод загрузки фото из любого источника с учётом масштаба.
        Возвращает PhotoImage или None при ошибке.
        Гарантирует сохранение ссылки в кэше для предотвращения удаления сборщиком мусора.
        """
        # === СТРОГАЯ ПРОВЕ����КА НАЛИЧИЯ ФОТО ===
        # 1. Сначала проверяем путь к файлу (приоритетнее)
        if person.photo_path and os.path.exists(person.photo_path):
            pass  # Файл существует — продолжаем загрузку
        # 2. Проверяем base64: должно быть непустой строкой без пробелов
        elif person.photo and isinstance(person.photo, str) and person.photo.strip():
            pass  # Base64 валиден — продолжаем загрузку
        else:
            return None  # Нет валидного фото

        # Генерируем УНИКАЛЬНЫЙ ключ для кэширования (с учётом масштаба)
        photo_key = self._generate_photo_key(person, scale)

        # Проверяем глобальный кэш
        if photo_key in self.photo_images:
            return self.photo_images[photo_key]

        # Загружаем изображение
        try:
            image = None
            # Сначала пытаемся загрузить из файла
            if person.photo_path and os.path.exists(person.photo_path):
                image = Image.open(person.photo_path)
            # Затем из base64 (только если строка непустая)
            elif person.photo and isinstance(person.photo, str) and person.photo.strip():
                try:
                    photo_data = base64.b64decode(person.photo.strip())
                    image = Image.open(io.BytesIO(photo_data))
                except Exception as e:
                    print(f"Ошибка декодирования base64 фото для {person.display_name()}: {e}")
                    return None

            if image is None:
                return None

            # Обработка прозрачности
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:  # 'LA'
                    background.paste(image.convert('RGBA'), mask=image.convert('RGBA').split()[-1])
                image = background
            elif image.mode == 'P':  # Палитра (GIF)
                image = image.convert('RGBA')
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # === МАСШТАБИРУЕМЫЙ РЕСАЙЗ (пропорционально карточке: 60×50 как constants.MAX_PHOTO_SIZE) ===
            max_w = int(constants.MAX_PHOTO_SIZE[0] * scale)
            max_h = int(constants.MAX_PHOTO_SIZE[1] * scale)
            image.thumbnail((max_w, max_h), Image.LANCZOS)

            photo_img = ImageTk.PhotoImage(image)

            # СОХРАНЯЕМ В ГЛОБАЛЬНЫЙ КЭШ
            self.photo_images[photo_key] = photo_img
            return photo_img

        except Exception as e:
            print(f"Ошибка загрузки фото для {person.display_name()} (ID: {person.id}): {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_photo_key(self, person, scale=1.0):
        """Генерирует уникальный ключ для кэширования фото с учётом масштаба."""
        scale_key = f"{scale:.2f}"  # Округляем до 2 знаков для стабильности ключа
        if person.photo_path and os.path.exists(person.photo_path):
            try:
                file_stat = os.stat(person.photo_path)
                return f"photo_{person.id}_path_{hash(person.photo_path)}_{file_stat.st_size}_{file_stat.st_mtime}_scale{scale_key}"
            except:
                return f"photo_{person.id}_path_{hash(person.photo_path)}_scale{scale_key}"
        elif person.photo:
            return f"photo_{person.id}_b64_{len(person.photo)}_scale{scale_key}"
        else:
            return f"photo_{person.id}_empty_scale{scale_key}"

    def refresh_photo_cache(self):
        """Очищает кэш изображений и перезагружает все фото."""
        self.photo_images.clear()
        self.refresh_view()

    def refresh_view(self, skip_layout=False):
        print(f"[REFRESH] skip_layout={skip_layout}, units до delete={len(self.units)}, coords={len(self.coords)}")
        self.update_adaptive_settings()
        self.canvas.delete("all")
        print(f"[REFRESH] После delete all, units={len(self.units)}, coords={len(self.coords)}")

        persons = self.model.get_all_persons()
        if not persons:
            self.canvas.create_text(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2,
                                    text="Семейное древо пусто. Нажмите ПКМ → «Добавить…» для начала работы.",
                                    font=("Segoe UI", 14, "bold"),
                                    fill="#64748b",
                                    justify="center")
            return

        # === СТРОИМ КООРДИНАТЫ (при выборе персоны не пересчитываем — места на холсте не меняются) ===
        skip_centering = getattr(self, "_skip_centering_once", False)
        self._skip_centering_once = False
        if not skip_layout or not self.coords:
            self.calculate_layout(skip_centering=skip_centering)

        # === ФИЛЬТРАЦИЯ ПЕРСОН (предки, потомки, братья/сёстры, супруги) ===
        visible_after_center = {}
        if self.model.current_center:
            center_pid = self.model.current_center
            # Собираем предков
            ancestors = set()
            queue = collections.deque([center_pid])
            visited_anc = set([center_pid])
            while queue:
                pid = queue.popleft()
                person = self.model.get_person(pid)
                if not person: continue
                for parent_id in person.parents:
                    if parent_id in persons and parent_id not in visited_anc:
                        visited_anc.add(parent_id)
                        ancestors.add(parent_id)
                        queue.append(parent_id)
            # Собираем потомков
            descendants = set()
            queue = collections.deque([center_pid])
            visited_desc = set([center_pid])
            while queue:
                pid = queue.popleft()
                person = self.model.get_person(pid)
                if not person: continue
                for child_id in person.children:
                    if child_id in persons and child_id not in visited_desc:
                        visited_desc.add(child_id)
                        descendants.add(child_id)
                        queue.append(child_id)
            # Собираем братьев/сестёр
            siblings = set()
            center_person = self.model.get_person(center_pid)
            if center_person:
                for parent_id in center_person.parents:
                    parent = self.model.get_person(parent_id)
                    if parent:
                        for sibling_id in parent.children:
                            if sibling_id != center_pid and sibling_id in persons:
                                siblings.add(sibling_id)
            # Собираем всех супругов (в т.ч. второй/третий брак)
            spouses = set()
            for pid in ancestors | descendants | siblings | {center_pid}:
                person = self.model.get_person(pid)
                if person and person.spouse_ids:
                    for spouse_id in person.spouse_ids:
                        if spouse_id in persons:
                            spouses.add(spouse_id)

            visible_set = ancestors | descendants | siblings | spouses | {center_pid}
            visible_set |= set(self.coords.keys())  # все размещённые всегда видимы
            
            # === ИСПРАВЛЕНИЕ: добавляем всех супругов из self.units в visible_set ===
            # Это гарантирует, что супруги из self.units будут видимы, даже если они не были добавлены через spouses
            for unit_members in self.units.values():
                for mid in unit_members:
                    if mid in self.coords:
                        visible_set.add(mid)
            # === /ИСПРАВЛЕНИЕ ===
            
            # у кого есть супруги — супруги тоже всегда видимы, если у них есть координаты
            for pid in list(visible_set):
                person = self.model.get_person(pid)
                if person and person.spouse_ids:
                    for sid in person.spouse_ids:
                        if sid in self.coords:
                            visible_set.add(sid)
            for pid, coords in self.coords.items():
                if pid in visible_set:
                    visible_after_center[pid] = coords
        else:
            # ← КРИТИЧЕСКИ ВАЖНО: если центр не задан — показываем ВСЕХ персон
            visible_after_center = dict(self.coords)
            
            # === ИСПРАВЛЕНИЕ: добавляем супругов из self.units, если центр не задан ===
            for unit_members in self.units.values():
                for mid in unit_members:
                    if mid in self.coords:
                        visible_after_center[mid] = self.coords[mid]
            # === /ИСПРАВЛЕНИЕ ===

        # === ПРИМЕНЕНИЕ СВОРАЧИВАНИЯ ВЕТВЕЙ ===
        after_collapse = {}
        for pid, coords in visible_after_center.items():
            person = self.model.get_person(pid)
            if not person: continue
            is_hidden = False
            for parent_id in person.parents:
                parent = self.model.get_person(parent_id)
                if parent and getattr(parent, 'collapsed_branches', False):
                    is_hidden = True
                    break
            if not is_hidden:
                after_collapse[pid] = coords

        # === ПРИМЕНЕНИЕ РЕЖИМА ФОКУСА ===
        after_focus = {}
        if self.focus_mode_active and self.model.current_center:
            center_pid = self.model.current_center
            for pid, coords in after_collapse.items():
                if pid != center_pid and self._is_ancestor(pid, center_pid):
                    continue
                after_focus[pid] = coords
        else:
            after_focus = after_collapse

        # === ПРИМЕНЕНИЕ ВНЕШНИХ ФИЛЬТРОВ ===
        filtered_visible = {}
        for pid, coords in after_focus.items():
            person = self.model.get_person(pid)
            if not person: continue
            if self.active_filters.get("photos_only", False) and not person.has_photo():
                continue
            if self.active_filters.get("childless", False) and person.children:
                continue
            filter_gender = self.active_filters.get("gender", constants.FILTER_ALL)
            if filter_gender != constants.FILTER_ALL:
                if filter_gender == constants.FILTER_MALE_ONLY and person.gender != "Мужской":
                    continue
                if filter_gender == constants.FILTER_FEMALE_ONLY and person.gender != "Женский":
                    continue
            filter_status = self.active_filters.get("status", constants.FILTER_ALL)
            if filter_status == constants.FILTER_ALIVE_ONLY and person.is_deceased:
                continue
            filtered_visible[pid] = coords

        # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: добавляем всех супругов из self.units в filtered_visible ===
        # Это гарантирует, что линии супругов будут отрисованы даже при skip_layout=True (перетаскивание)
        for unit_members in self.units.values():
            for mid in unit_members:
                if mid in self.coords and mid not in filtered_visible:
                    filtered_visible[mid] = self.coords[mid]
                    print(f"[MARRIAGE_FIX] Добавлен супруг {mid} в filtered_visible")
        # === /КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ===

        self.visible_persons_in_coords = filtered_visible

        # === ВЫЧИСЛЕНИЕ СТЕПЕНИ РОДСТВА (если есть центральная персона) ===
        self.relationships = {}
        if self.model.current_center and KINSHIP_AVAILABLE:
            try:
                self.relationships = calculate_kinship(self.model, str(self.model.current_center))
            except Exception as e:
                print(f"[KINSHIP] Ошибка вычисления родства: {e}")
                self.relationships = {}
        # === /ВЫЧИСЛЕНИЕ СТЕПЕНИ РОДСТВА ===

        # === ОТРИСОВКА СВЯЗЕЙ РОДИТЕЛИ → ДЕТИ (середина линии родителей → общая линия детей → верх карточки ребёнка, скругления) ===
        def _key_in_vis(pid):
            if pid is None:
                return None
            s = str(pid)
            return next((k for k in self.visible_persons_in_coords if str(k) == s), None)

        parent_set_to_children = {}
        for pid, (sx, sy) in self.visible_persons_in_coords.items():
            person = self.model.get_person(pid)
            if not person or not person.parents:
                continue
            visible_parent_keys = []
            for p_id in person.parents:
                k = _key_in_vis(p_id)
                if k is not None:
                    visible_parent_keys.append(k)
            if not visible_parent_keys:
                continue
            key = frozenset(visible_parent_keys)
            parent_set_to_children.setdefault(key, []).append(pid)

        def scale_pt(x, y):
            return (x * self.current_scale + self.offset_x, y * self.current_scale + self.offset_y)

        line_w = max(1, self.PARENT_LINE_WIDTH * self.current_scale)
        child_top_offset = self.CARD_HEIGHT / 2

        for parent_keys, child_pids in parent_set_to_children.items():
            if not child_pids:
                continue
            parent_keys = list(parent_keys)
            if len(parent_keys) == 2:
                k1, k2 = parent_keys[0], parent_keys[1]
                if k1 not in self.visible_persons_in_coords or k2 not in self.visible_persons_in_coords:
                    continue
                px1, py1 = self.visible_persons_in_coords[k1]
                px2, py2 = self.visible_persons_in_coords[k2]
                mid_x = (px1 + px2) / 2
                mid_y = (py1 + py2) / 2
            else:
                k1 = parent_keys[0]
                if k1 not in self.visible_persons_in_coords:
                    continue
                mid_x, mid_y = self.visible_persons_in_coords[k1]

            children_coords = []
            for cid in child_pids:
                if cid not in self.visible_persons_in_coords:
                    continue
                cx, cy = self.visible_persons_in_coords[cid]
                child_top_y = cy - child_top_offset
                children_coords.append((cx, cy, child_top_y))
            if not children_coords:
                continue
            children_coords.sort(key=lambda t: t[0])
            min_child_top_y = min(t[2] for t in children_coords)
            # Общая горизонтальная линия — по высоте между родителями и детьми
            line_y = (mid_y + min_child_top_y) / 2

            # Полилиния: прямые отрезки (острые углы)
            points = [(mid_x, mid_y), (mid_x, line_y)]
            for (cx, cy, top_y) in children_coords:
                points.append((cx, line_y))
                points.append((cx, top_y))
                points.append((cx, line_y))
            flat = []
            for x, y in points:
                sx, sy = scale_pt(x, y)
                flat.extend([sx, sy])
            if len(flat) >= 4:
                self.canvas.create_line(
                    *flat,
                                                fill=constants.PARENT_LINE_COLOR,
                    width=line_w,
                    capstyle="round",
                    joinstyle="round",
                    smooth=False,
                    tags="parent_line"
                )

        # === 🔴 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ВОССТАНОВЛЕНА ОТРИСОВКА КАРТОЧЕК ===
        for pid, (sx, sy) in self.visible_persons_in_coords.items():
            person = self.model.get_person(pid)
            if not person: continue
            self.draw_person_card(pid, person, sx, sy)  # ← Без параметра photo_cache!
        # === /КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ===

        # === ОТРИСОВКА СВЯЗЕЙ МЕЖДУ СУПРУГАМИ (ПОСЛЕ КАРТОЧЕК) ===
        marriage_lines_drawn = 0
        CARD_HALF_W = self.CARD_WIDTH / 2
        CARD_HALF_H = self.CARD_HEIGHT / 2

        print(f"[MARRIAGE] Отрисовка линий: units={len(self.units)}, visible={len(self.visible_persons_in_coords)}, coords={len(self.coords)}")
        print(f"[MARRIAGE] skip_layout={skip_layout}, current_center={self.model.current_center}")
        
        # Проверка: выводим все units и их видимость
        for unit_key, members in self.units.items():
            members_in_coords = [mid for mid in members if mid in self.coords]
            members_in_visible = [mid for mid in members if mid in self.visible_persons_in_coords]
            print(f"[MARRIAGE] Unit {unit_key}: members={members}, in_coords={members_in_coords}, in_visible={members_in_visible}")

        for unit_key, members in self.units.items():
            if len(members) < 2:
                print(f"[MARRIAGE] Пропущен {unit_key}: меньше 2 членов ({len(members)})")
                continue

            # Проверка видимости супругов
            missing_spouses = [mid for mid in members if mid not in self.visible_persons_in_coords]
            if missing_spouses:
                print(f"[MARRIAGE] WARNING: супруги {missing_spouses} из unit {unit_key} НЕ в visible_persons_in_coords!")
                print(f"[MARRIAGE] visible_persons_in_coords ключи: {list(self.visible_persons_in_coords.keys())[:10]}")

            xs, ys = [], []
            all_visible = True
            for mid in members:
                vis_key = _key_in_vis(mid)
                if vis_key is not None:
                    x, y = self.visible_persons_in_coords[vis_key]
                    xs.append(x)
                    ys.append(y)
                else:
                    all_visible = False
                    print(f"[MARRIAGE] Супруг {mid} не найден в visible_persons_in_coords через _key_in_vis")
                    break
            if not all_visible:
                print(f"[MARRIAGE] Пропущен брак {unit_key}: не все супруги видимы (all_visible=False)")
                continue
            if len(xs) == 2:
                # Координаты центров карточек
                cx1, cy1 = xs[0], ys[0]
                cx2, cy2 = xs[1], ys[1]
                
                # Вычисляем угол между супругами
                dx = cx2 - cx1
                dy = cy2 - cy1
                if dx == 0 and dy == 0:
                    continue  # Одна и та же персона
                angle = math.atan2(dy, dx)
                
                # Смещаем точки на край карточки
                # Для упрощения используем прямоугольную аппроксимацию
                margin_x = CARD_HALF_W
                margin_y = CARD_HALF_H
                
                # Точка выхода из первой карточки
                x1 = cx1 + margin_x * math.cos(angle)
                y1 = cy1 + margin_y * math.sin(angle)
                
                # Точка входа во вторую карточку
                x2 = cx2 - margin_x * math.cos(angle)
                y2 = cy2 - margin_y * math.sin(angle)
                
                scaled_x1 = x1 * self.current_scale + self.offset_x
                scaled_y1 = y1 * self.current_scale + self.offset_y
                scaled_x2 = x2 * self.current_scale + self.offset_x
                scaled_y2 = y2 * self.current_scale + self.offset_y
                # Отладка: проверяем цвет линии
                print(f"[MARRIAGE_LINE] Цвет: {constants.MARRIAGE_LINE_COLOR}, Ширина: {self.MARRIAGE_LINE_WIDTH * self.current_scale}")
                self.canvas.create_line(scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                                        fill=constants.MARRIAGE_LINE_COLOR,
                                        width=self.MARRIAGE_LINE_WIDTH * self.current_scale,
                                        dash=constants.DEFAULT_MARRIAGE_LINE_DASH,
                                        tags="marriage_line")
                marriage_lines_drawn += 1
        print(f"[DEBUG] Нарисовано линий супругов: {marriage_lines_drawn}")

        # === ОБНОВЛЕНИЕ СЧЁТЧИКА ПЕРСОН ===
        total_persons = len(self.model.persons)
        visible_persons = len(self.visible_persons_in_coords)
        if hasattr(self, 'counter_label'):
            if visible_persons == total_persons:
                self.counter_label.config(text=f"Персон: {total_persons}")
            else:
                self.counter_label.config(text=f"Персон: {total_persons} (видимо: {visible_persons})")

    def calculate_layout(self, skip_centering=False):
        """
        Компоновка дерева, включающего:
        - current_center
        - его родителей
        - его братьев/сёстёр (через общих родителей)
        - его супругов
        - его детей
        skip_centering: при True не сдвигать дерево в центр экрана (при выборе персоны кликом).
        """
        persons = self.model.get_all_persons()
        if not persons:
            self.coords.clear()
            self.units.clear()
            self.level_structure.clear()
            return

        marriages = self.model.get_marriages()
        print(f"[DEBUG] marriages из модели: {marriages}")
        print(f"[DEBUG] model.persons count: {len(self.model.persons)}")
        print(f"[DEBUG] model.marriages count: {len(self.model.marriages)}")
        # Проверка spouse_ids у ВСЕХ персон
        persons_with_spouse = 0
        for pid, p in self.model.persons.items():
            if p.spouse_ids:
                print(f"[DEBUG] {pid} ({p.display_name()}): spouse_ids={p.spouse_ids}")
                persons_with_spouse += 1
        print(f"[DEBUG] Персон с супругами: {persons_with_spouse}")

        # === ШАГ 1: ОПРЕДЕЛЕНИЕ ЦЕНТРА (поиск по нормализованному id из‑за возможного int/str) ===
        center_pid = self.model.current_center
        if center_pid is not None:
            center_key = next((k for k in persons if str(k) == str(center_pid)), None)
            if center_key is not None:
                center_pid = center_key
            else:
                center_pid = None
        center_person_exists = center_pid is not None

        if not center_person_exists:
            self.model.current_center = None
            candidates = [(pid, len(p.parents)) for pid, p in persons.items()]
            if not candidates:
                self.coords.clear()
                self.units.clear()
                self.level_structure.clear()
                return
            center_pid = min(candidates, key=lambda x: x[1])[0]
            if self.model.current_center is None:
                self.model.current_center = center_pid

        # === ШАГ 2: ОДИН СУПРУГ ДЛЯ ОТОБРАЖЕНИЯ НА ХОЛСТЕ (первый по id при нескольких браках) ===
        spouse_of = {}
        for pid, person in persons.items():
            if person.spouse_ids:
                spouse_of[pid] = min(person.spouse_ids, key=lambda x: (str(x),))

        # === ШАГ 3: СБОР ВСЕХ СВЯЗАННЫХ С CENTER_PID ПЕРСОН (включая всех супругов) ===
        related_pids = set()
        visited = set()

        def _key_in_persons(pid):
            if pid is None:
                return None
            pid_str = str(pid)
            return next((k for k in persons if str(k) == pid_str), None)

        # ИТЕРАТИВНЫЙ BFS (вместо рекурсии — для больших деревьев)
        queue = collections.deque([center_pid])
        
        while queue:
            current_pid = queue.popleft()
            key = _key_in_persons(current_pid)
            
            if key is None or key in visited:
                continue
            if key not in persons:
                continue
            
            visited.add(key)
            related_pids.add(key)
            person = persons[key]

            # Добавляем всех связанных в очередь
            for parent_id in (person.parents or []):
                queue.append(parent_id)
            for child_id in (person.children or []):
                queue.append(child_id)
            for spouse_id in (person.spouse_ids or []):
                queue.append(spouse_id)
            
            # Добавляем siblings (через родителей)
            for parent_id in (person.parents or []):
                parent = persons.get(_key_in_persons(parent_id))
                if parent:
                    for sibling_id in (parent.children or []):
                        sk = _key_in_persons(sibling_id)
                        if sk and sk != key and sk not in visited:
                            queue.append(sibling_id)

        # === ШАГ 4: ОСТАВЛЯЕМ ТОЛЬКО СВЯЗАННЫХ ПЕРСОН ===
        # Если найдена только 1 персона (нет связей), но в дереве их больше — показываем ВСЕХ
        if len(related_pids) == 1 and len(persons) > 1:
            # Нет связей между персонами — показываем всех
            related_pids = set(persons.keys())

        # === ИСПРАВЛЕНИЕ: добавляем всех супругов из marriages в related_pids ===
        # Это гарантирует, что супруги будут отрисованы даже если не были найдены через BFS
        for marriage_key in marriages.keys():
            h_id, w_id = marriage_key
            h_str, w_str = str(h_id), str(w_id)
            # Ищем совпадения в persons
            h_key = next((k for k in persons if str(k) == h_str), None)
            w_key = next((k for k in persons if str(k) == w_str), None)
            if h_key and h_key in related_pids and w_key and w_key not in related_pids:
                related_pids.add(w_key)
                print(f"[MARRIAGE_FIX] Добавлен супруг {w_key} в related_pids (из marriages)")
            if w_key and w_key in related_pids and h_key and h_key not in related_pids:
                related_pids.add(h_key)
                print(f"[MARRIAGE_FIX] Добавлен супруг {h_key} в related_pids (из marriages)")
        # === /ИСПРАВЛЕНИЕ ===

        filtered_persons = {pid: persons[pid] for pid in related_pids}

        # Сохраняем позицию центральной персоны: при перерисовке ветви останутся вокруг неё на месте
        old_center_coord = None
        center_key_for_pin = next((k for k in self.coords if str(k) == str(center_pid)), None)
        if center_key_for_pin is not None:
            old_center_coord = self.coords[center_key_for_pin]

        # === ШАГ 5: ПОВТОРНАЯ ЛОГИКА РАЗМЕЩЕНИЯ (ОТНОСИТЕЛЬНО СВЯЗАННЫХ ПЕРСОН) ===
        canvas_width = max(self.canvas.winfo_width(), 800)
        LEVEL_HEIGHT = self.CARD_HEIGHT * 2.8   # вертикальное расстояние между рядами (родители ↔ дети)
        SPOUSE_SPACING = 0.3                    # зазор между супругами: 30% от ширины карточки
        SIBLING_SPACING_FULL = 1.0              # родные братья/сёстры: 100% от ширины карточки
        SIBLING_SPACING_COUSINS = 2.0           # двоюродные и далее: 200% от ширины карточки

        self.coords = {}
        self.level_structure = {}

        def _norm_id(pid):
            """Нормализация id для сравнения (str)."""
            return str(pid) if pid is not None else None

        def _key_in_filtered(pid):
            """Возвращает ключ из filtered_persons, совпадающий с pid (любой тип). Иначе None."""
            if pid is None:
                return None
            s = _norm_id(pid)
            return next((k for k in filtered_persons if _norm_id(k) == s), None)

        def _display_spouse_ids(person):
            """Список супругов персоны, отображаемых на этом уровне (не свёрнутых)."""
            result = []
            for sid in (person.spouse_ids or []):
                sid_str = _norm_id(sid)
                key = next((k for k in filtered_persons if _norm_id(k) == sid_str), None)
                if key and not getattr(filtered_persons.get(key), 'collapsed_branches', False):
                    result.append(key)
            return result

        def _gap_between_siblings(cid1, cid2):
            """Зазор между двумя детьми: 100% если одни родители, 200% если разные (двоюродные и далее).
            Учитываются супруги: ширина блока каждого ребёнка (get_subtree_width) уже включает супругов,
            поэтому зазор считается от правого края блока (в т.ч. от супруга, если он есть) до следующего.
            """
            p1 = filtered_persons.get(cid1)
            p2 = filtered_persons.get(cid2)
            if not p1 or not p2:
                return self.CARD_WIDTH * SIBLING_SPACING_COUSINS
            set1 = frozenset(str(x) for x in (p1.parents or []))
            set2 = frozenset(str(x) for x in (p2.parents or []))
            if set1 == set2:
                return self.CARD_WIDTH * SIBLING_SPACING_FULL
            return self.CARD_WIDTH * SIBLING_SPACING_COUSINS

        def _block_width_only(person):
            """Ширина только блока персоны + супруги (без детей). Зазор перед первым супругом и между супругами."""
            display_spouses = _display_spouse_ids(person)
            if display_spouses:
                gap = self.CARD_WIDTH * SPOUSE_SPACING
                step = self.CARD_WIDTH + gap
                return self.CARD_WIDTH + gap + len(display_spouses) * step
            return self.CARD_WIDTH

        def get_subtree_width(pid):
            """Возвращает ширину, необходимую для поддерева (персона + все потомки)."""
            key = _key_in_filtered(pid)
            if key is None:
                return self.CARD_WIDTH
            person = filtered_persons[key]
            block_width = _block_width_only(person)

            child_keys = [k for cid in (person.children or []) if (k := _key_in_filtered(cid)) is not None
                         and not getattr(filtered_persons.get(k), 'collapsed_branches', False)]
            children = sorted(
                child_keys,
                key=lambda k: (
                    filtered_persons[k].birth_date or "9999.99.99",
                    int(k) if str(k).isdigit() else 0
                )
            )
            if not children:
                return block_width
            child_widths = []
            for ck in children:
                w = get_subtree_width(ck)
                min_w = _block_width_only(filtered_persons[ck])
                child_widths.append(max(w, min_w))
            total_gaps = sum(_gap_between_siblings(children[i], children[i + 1]) for i in range(len(children) - 1))
            total_children = sum(child_widths) + total_gaps
            return max(block_width, total_children)

        def place_subtree(pid, place_x, y_pos, allocated_width):
            """
            Размещает персону и поддерево. place_x — левый край выделенной зоны,
            allocated_width — ширина зоны. Персона и все супруги в ряд, затем дети симметрично ни��е.
            """
            key = _key_in_filtered(pid)
            if key is None:
                return place_x, place_x + self.CARD_WIDTH
            person = filtered_persons[key]
            display_spouses = _display_spouse_ids(person)
            block_width = _block_width_only(person)
            allocated_width = max(allocated_width, block_width)

            block_x = place_x + (allocated_width - block_width) / 2

            # В паре муж всегда слева: сортируем блок по полу (сначала мужчины)
            gap = self.CARD_WIDTH * SPOUSE_SPACING
            all_in_block = [key] + list(display_spouses)
            all_in_block.sort(key=lambda k: (0 if filtered_persons[k].gender == "Мужской" else 1))
            for i, pid in enumerate(all_in_block):
                sx = block_x + i * (self.CARD_WIDTH + gap) + self.CARD_WIDTH / 2
                self.coords[pid] = (sx, y_pos)
                self.level_structure.setdefault(int((y_pos - 50) / LEVEL_HEIGHT), []).append(pid)

            # === РАЗМЕЩЕНИЕ РОДИТЕЛЕЙ (выше текущей персоны) ===
            parent_y = y_pos - LEVEL_HEIGHT
            visible_parents = []
            for parent_id in (person.parents or []):
                pk = _key_in_filtered(parent_id)
                if pk is not None and pk not in self.coords:
                    visible_parents.append(pk)
            
            if visible_parents:
                parent_widths = []
                for pk in visible_parents:
                    w = get_subtree_width(pk)
                    min_w = _block_width_only(filtered_persons[pk])
                    parent_widths.append(max(w, min_w))
                
                total_parent_w = sum(parent_widths)
                for i in range(len(visible_parents) - 1):
                    total_parent_w += _gap_between_siblings(visible_parents[i], visible_parents[i + 1])
                
                parent_x = block_x + (block_width - total_parent_w) / 2
                for i, pk in enumerate(visible_parents):
                    pw = parent_widths[i]
                    place_subtree(pk, parent_x, parent_y, pw)
                    parent_x += pw
                    if i < len(visible_parents) - 1:
                        parent_x += _gap_between_siblings(visible_parents[i], visible_parents[i + 1])
            # === /РАЗМЕЩЕНИЕ РОДИТЕЛЕЙ ===

            child_y = y_pos + LEVEL_HEIGHT
            child_keys = [k for cid in (person.children or []) if (k := _key_in_filtered(cid)) is not None
                         and not getattr(filtered_persons.get(k), 'collapsed_branches', False)]
            children = sorted(
                child_keys,
                key=lambda k: (
                    filtered_persons[k].birth_date or "9999.99.99",
                    int(k) if str(k).isdigit() else 0
                )
            )

            if children:
                # Центр между родителями: всегда по фактическим координатам всех родителей (чтобы ребёнок был по середине между отцом и матерью)
                parent_keys_of_children = set()
                for ck in children:
                    for p_id in (filtered_persons[ck].parents or []):
                        pk = _key_in_filtered(p_id)
                        if pk is not None and pk in filtered_persons:
                            parent_keys_of_children.add(pk)
                seen_norm = set()
                parent_xs = []
                for pk in parent_keys_of_children:
                    n = _norm_id(pk)
                    if n in seen_norm:
                        continue
                    coord_key = next((k for k in self.coords if _norm_id(k) == n), None)
                    if coord_key is not None:
                        seen_norm.add(n)
                        parent_xs.append(self.coords[coord_key][0])
                parent_center_x = (sum(parent_xs) / len(parent_xs)) if parent_xs else (block_x + block_width / 2)

                child_widths = []
                for ck in children:
                    w = get_subtree_width(ck)
                    min_w = _block_width_only(filtered_persons[ck])
                    child_widths.append(max(w, min_w))
                total_gaps = sum(_gap_between_siblings(children[i], children[i + 1]) for i in range(len(children) - 1))
                total_children_width = sum(child_widths) + total_gaps

                if len(children) == 1:
                    # Один ребёнок — размещаем, затем сдвигаем весь блок так, чтобы центр карточки ребёнка был строго под центром родителей
                    cw = child_widths[0]
                    child_bw = _block_width_only(filtered_persons[children[0]])
                    place_subtree(children[0], parent_center_x - child_bw / 2, child_y, child_bw)
                    one_child_key = children[0]
                    if one_child_key in self.coords:
                        child_x_now = self.coords[one_child_key][0]
                        delta = parent_center_x - child_x_now
                        if abs(delta) > 0.01:
                            block_keys = [one_child_key] + list(_display_spouse_ids(filtered_persons[one_child_key]))
                            for k in block_keys:
                                if k in self.coords:
                                    ox, oy = self.coords[k]
                                    self.coords[k] = (ox + delta, oy)
                    children_start_x = parent_center_x - cw / 2
                    subtree_left = min(block_x, children_start_x)
                    subtree_right = max(block_x + block_width, parent_center_x + cw / 2)
                    return subtree_left, subtree_right
                else:
                    # Несколько детей — симметрично относительно центра, с зазорами между братьями/сёстрами
                    children_start_x = parent_center_x - total_children_width / 2
                    current_x = float(children_start_x)
                    for i, child_id in enumerate(children):
                        cw = child_widths[i]
                        place_subtree(child_id, current_x, child_y, cw)
                        current_x += cw
                        if i < len(children) - 1:
                            current_x += _gap_between_siblings(children[i], children[i + 1])
                    subtree_left = min(block_x, children_start_x)
                    subtree_right = max(block_x + block_width, children_start_x + total_children_width)
                    return subtree_left, subtree_right
            return block_x, block_x + block_width

        # === ШАГ 6: НАХОЖДЕНИЕ КОРНЯ ДЕРЕВА ===
        # ИСПРАВЛЕНО: дерево строится ОТ выбранной персоны, а не от старшего предка
        root_key = _key_in_filtered(center_pid)
        if root_key is None:
            root_key = next(iter(filtered_persons), None)
        if root_key is None:
            return
        
        # === ШАГ 7: ЗАПУСК РАЗМЕЩЕНИЯ ОТ КОРНЯ (выбранная персона) ===
        root_y = 50
        root_width = max(canvas_width, get_subtree_width(root_key))
        place_subtree(root_key, 0, root_y, root_width)

        # === ШАГ 7.5: ДОРАЗМЕЩЕНИЕ ВСЕХ БЕЗ КООРДИНАТ по списку браков и spouse_ids ===
        gap_fill = self.CARD_WIDTH * SPOUSE_SPACING
        step_fill = self.CARD_WIDTH + gap_fill

        def place_next_to_spouse(pid, partner_key):
            if pid in self.coords or partner_key not in self.coords:
                return False
            if pid not in filtered_persons:
                return False
            sx, sy = self.coords[partner_key]
            self.coords[pid] = (sx + step_fill, sy)
            self.level_structure.setdefault(int((sy - 50) / LEVEL_HEIGHT), []).append(pid)
            return True

        while True:
            added = 0
            for h_id, w_id in marriages:
                h_key = next((k for k in filtered_persons if _norm_id(k) == _norm_id(h_id)), None)
                w_key = next((k for k in filtered_persons if _norm_id(k) == _norm_id(w_id)), None)
                if not h_key or not w_key:
                    continue
                if place_next_to_spouse(h_key, w_key):
                    added += 1
                if place_next_to_spouse(w_key, h_key):
                    added += 1
            for pid in list(filtered_persons):
                if pid in self.coords:
                    continue
                person = filtered_persons.get(pid)
                if not person or not person.spouse_ids:
                    continue
                for spouse_id in person.spouse_ids:
                    partner_key = next((k for k in filtered_persons if _norm_id(k) == _norm_id(spouse_id)), None)
                    if place_next_to_spouse(pid, partner_key):
                        added += 1
                        break
            if added == 0:
                break

        # === ШАГ 8: ЦЕНТРИРОВАНИЕ (пропускаем при выборе персоны клик��м, чтобы не сдвигать вид) ===
        if not skip_centering and self.coords:
            all_x = [x for x, y in self.coords.values()]
            if all_x:
                min_x = min(all_x)
                max_x = max(all_x)
                tree_width = max_x - min_x
                shift_x = (canvas_width - tree_width) / 2 - min_x

                for pid in list(self.coords.keys()):
                    x, y = self.coords[pid]
                    self.coords[pid] = (x + shift_x, y)

        # === ШАГ 8.5: ПРИВЯЗКА ЦЕНТРА — персона остаётся на месте, ветви перерисовываются вокруг неё ===
        if old_center_coord is not None:
            pin_key = next((k for k in self.coords if str(k) == str(center_pid)), None)
            if pin_key is not None:
                new_x, new_y = self.coords[pin_key]
                dx = old_center_coord[0] - new_x
                dy = old_center_coord[1] - new_y
                for pid in list(self.coords.keys()):
                    x, y = self.coords[pid]
                    self.coords[pid] = (x + dx, y + dy)

        # === ШАГ 9: ФОРМИРОВАНИЕ СУПРУЖЕСКИХ ПАР ===
        # ИСПРАВЛЕНО: сохраняем units, если skip_centering=True (не пересчитываем при выборе персоны или перетаскивании)
        if skip_centering:
            print(f"[DEBUG] skip_centering=True, сохраняем units={len(self.units)}")
        else:
            print(f"[DEBUG] skip_centering=False, очищаем units перед пересчётом")
            self.units = {}
        print(f"[DEBUG] Загружено браков из модели: {len(marriages)}")
        print(f"[DEBUG] filtered_persons: {len(filtered_persons)}")
        print(f"[DEBUG] units перед циклом: {len(self.units)}")
        
        # Проверка spouse_ids у персон в filtered_persons
        persons_with_spouse_in_filtered = 0
        for pid, p in filtered_persons.items():
            if p.spouse_ids:
                print(f"[DEBUG] filtered_persons {pid} ({p.display_name()}): spouse_ids={p.spouse_ids}")
                persons_with_spouse_in_filtered += 1
        print(f"[DEBUG] Персон с супругами в filtered_persons: {persons_with_spouse_in_filtered}")
        
        # marriages — это dict {(id1, id2): {"date": "..."}}, итерируем по ключам
        for marriage_key in sorted(marriages.keys()):
            h_id, w_id = marriage_key  # Распаковываем кортеж
            
            # === ИСПРАВЛЕНИЕ: добавляем супругов в filtered_persons, если они есть в coords ===
            # Это гарантирует, что супруги будут отрисованы даже если не были найдены через связи
            if h_id not in filtered_persons and h_id in self.coords:
                h_obj = persons.get(h_id) or persons.get(str(h_id))
                if h_obj:
                    filtered_persons[h_id] = h_obj
                    print(f"[MARRIAGE_FIX] Добавлен супруг {h_id} в filtered_persons (из coords)")
            if w_id not in filtered_persons and w_id in self.coords:
                w_obj = persons.get(w_id) or persons.get(str(w_id))
                if w_obj:
                    filtered_persons[w_id] = w_obj
                    print(f"[MARRIAGE_FIX] Добавлен супруг {w_id} в filtered_persons (из coords)")
            # === /ИСПРАВЛЕНИЕ ===
            
            if h_id not in filtered_persons or w_id not in filtered_persons:
                print(f"[DEBUG] Пропущен брак {h_id}-{w_id} (нет в filtered_persons): h_id in filtered={h_id in filtered_persons}, w_id in filtered={w_id in filtered_persons}")
                continue
            p1, p2 = h_id, w_id
            p1_obj = filtered_persons.get(p1)
            p2_obj = filtered_persons.get(p2)

            if p1_obj and p2_obj:
                if p1_obj.gender == "Женский" and p2_obj.gender == "Мужской":
                    p1, p2 = w_id, h_id

            unit_key = f"{min(p1, p2)}_{max(p1, p2)}"
            self.units[unit_key] = [p1, p2]
            print(f"[DEBUG] Добавлен брак {unit_key}: {self.units[unit_key]}")
        print(f"[DEBUG] units после цикла: {len(self.units)}")
        print(f"[DEBUG] Сформировано units: {len(self.units)}")
        for uk, uv in list(self.units.items())[:5]:
            print(f"[DEBUG]   {uk}: {uv}")

    def _is_ancestor(self, ancestor_id, descendant_id):
        """
        Проверяет, является ли ancestor_id предком descendant_id.
        Использует BFS для обхода дерева по родительским связям.
        """
        if ancestor_id == descendant_id:
            return False  # Сама персона не является своим предком

        visited = set()
        queue = collections.deque([descendant_id])

        while queue:
            current_id = queue.popleft()

            if current_id == ancestor_id:
                return True

            if current_id in visited:
                continue

            visited.add(current_id)
            person = self.model.get_person(current_id)

            if person:
                # Добавляем всех родителей в очередь для проверки
                queue.extend(person.parents)

        return False

    def toggle_focus_mode(self):
        """
        Переключает режим фокуса: при включении скрываются предки центра,
        при выключении — все предки становятся видимыми.
        """
        if not self.model.current_center:
            messagebox.showinfo("Режим фокуса", "Сначала выберите центральную персону (кликните по карточке).")
            return

        self.focus_mode_active = not self.focus_mode_active

        # Обновляем метку центра с индикацией режима
        center_person = self.model.get_person(self.model.current_center)
        if self.focus_mode_active:
            self.center_label.config(text=f"Центр: {center_person.display_name()} 🔍")
            self.statusbar.config(text="Режим фокуса ВКЛЮЧЁН: предки скрыты")
        else:
            self.center_label.config(text=f"Центр: {center_person.display_name()}")
            self.statusbar.config(text="Режим фокуса ВЫКЛЮЧЕН: все предки видимы")

        self.refresh_view()

    def collapse_all_branches(self):
        """Сворачивает ветви ВСЕХ персон (кроме центра)."""
        for person in self.model.get_all_persons().values():
            person.collapsed_branches = True

        self.refresh_view()

    def expand_all_branches(self):
        """Разворачивает ветви ВСЕХ персон."""
        for person in self.model.get_all_persons().values():
            person.collapsed_branches = False

        self.refresh_view()

    def reset_scale(self):
        self.current_scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.refresh_view()

    # --- МЕТОДЫ ДИАЛОГОВ ---
    def add_person_dialog(self, parent_id=None, relation_type=None):
        """
        Диалог добавления новой персоны.
        parent_id и relation_type используются для автоматического связывания с родителем/супругом.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить персону")
        dialog.geometry("450x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Создаём контейнер для скроллируемой области
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, bg=constants.WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0

        # Имя
        ttk.Label(scrollable_frame, text="Имя*").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        name_var = tk.StringVar()
        name_entry = ttk.Entry(scrollable_frame, textvariable=name_var, width=30)
        name_entry.grid(row=row, column=1, padx=10, pady=8, sticky='w')
        self._enable_copy_paste(name_entry)
        row += 1

        # Фамилия
        ttk.Label(scrollable_frame, text="Фамилия*").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        surname_var = tk.StringVar()
        surname_entry = ttk.Entry(scrollable_frame, textvariable=surname_var, width=30)
        surname_entry.grid(row=row, column=1, padx=10, pady=8, sticky='w')
        self._enable_copy_paste(surname_entry)
        row += 1

        # Отчество
        ttk.Label(scrollable_frame, text="Отчество").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        patronymic_var = tk.StringVar()
        patronymic_entry = ttk.Entry(scrollable_frame, textvariable=patronymic_var, width=30)
        patronymic_entry.grid(row=row, column=1, padx=10, pady=8, sticky='w')
        self._enable_copy_paste(patronymic_entry)
        row += 1

        # Дата рождения
        ttk.Label(scrollable_frame, text="Дата рождения").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        birth_date_var = tk.StringVar()
        birth_entry = ttk.Entry(scrollable_frame, textvariable=birth_date_var, width=30)
        birth_entry.grid(row=row, column=1, padx=10, pady=8, sticky='w')
        birth_entry.bind("<KeyPress>", self._date_entry_keypress)
        birth_entry.bind("<<Paste>>", lambda e, ent=birth_entry: self._date_entry_on_paste(ent))
        birth_entry.bind("<FocusOut>", self.normalize_date_on_focusout)
        row += 1

        # Пол
        ttk.Label(scrollable_frame, text="Пол*").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        gender_var = tk.StringVar(value="Мужской")
        gender_frame = ttk.Frame(scrollable_frame)
        gender_frame.grid(row=row, column=1, padx=10, pady=8, sticky='w')
        ttk.Radiobutton(gender_frame, text="Мужской", variable=gender_var, value="Мужской").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(gender_frame, text="Женский", variable=gender_var, value="Женский").pack(side=tk.LEFT, padx=5)
        row += 1

        # Стат��с смерт��
        ttk.Label(scrollable_frame, text="Ум��р(ла)").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        deceased_var = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, variable=deceased_var).grid(row=row, column=1, padx=10, pady=8, sticky='w')
        row += 1

        # Дата смерти (пок��зывается при выборе "Умер(ла)")
        death_date_frame = ttk.Frame(scrollable_frame)
        death_date_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=0, sticky='ew')
        ttk.Label(death_date_frame, text="Дата смерти").pack(side=tk.LEFT, padx=(0, 10))
        death_date_var = tk.StringVar()
        death_entry = ttk.Entry(death_date_frame, textvariable=death_date_var, width=25)
        death_entry.pack(side=tk.LEFT)
        death_entry.bind("<KeyPress>", self._date_entry_keypress)
        death_entry.bind("<<Paste>>", lambda e, ent=death_entry: self._date_entry_on_paste(ent))
        death_entry.bind("<FocusOut>", self.normalize_date_on_focusout)
        death_date_frame.grid_remove()  # Скрыто по умолчан��ю

        def toggle_death_date():
            if deceased_var.get():
                death_date_frame.grid()
            else:
                death_date_frame.grid_remove()

        deceased_var.trace_add("write", lambda *args: toggle_death_date())
        row += 1

        # Девичья фамилия (только для женщин)
        maiden_name_frame = ttk.Frame(scrollable_frame)
        maiden_name_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=0, sticky='ew')
        ttk.Label(maiden_name_frame, text="Девичья фамилия").pack(side=tk.LEFT, padx=(0, 10))
        maiden_name_var = tk.StringVar()
        ttk.Entry(maiden_name_frame, textvariable=maiden_name_var, width=25).pack(side=tk.LEFT)
        maiden_name_frame.grid_remove()  # Скрыто по умолчанию

        def toggle_maiden_name(*args):
            if gender_var.get() == "Женский":
                maiden_name_frame.grid()
            else:
                maiden_name_frame.grid_remove()
                maiden_name_var.set("")

        gender_var.trace_add("write", toggle_maiden_name)
        toggle_maiden_name()  # Инициализация
        row += 1

        # Фото
        ttk.Label(scrollable_frame, text="Фото").grid(row=row, column=0, padx=10, pady=8, sticky='e')
        photo_path_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=photo_path_var, width=30).grid(row=row, column=1, padx=10, pady=8,
                                                                                sticky='w')
        ttk.Button(scrollable_frame, text="Обзор...", command=lambda: self.browse_photo(photo_path_var)).grid(row=row,
                                                                                                              column=1,
                                                                                                              padx=(240,
                                                                                                                    10),
                                                                                                              pady=8,
                                                                                                              sticky='w')
        row += 1

        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        def submit():
            name = name_var.get().strip()
            surname = surname_var.get().strip()
            patronymic = patronymic_var.get().strip()
            birth_date = birth_date_var.get().strip()
            gender = gender_var.get()
            is_deceased = deceased_var.get()
            death_date = death_date_var.get().strip() if is_deceased else ""
            maiden_name = maiden_name_var.get().strip() if gender == "Женский" else ""
            photo_path = photo_path_var.get().strip()

            if not name or not surname:
                messagebox.showerror("Ошибка", "Имя и фамилия обязательны для заполнения.")
                return

            # Обработка фото: если указан путь к файлу и он существует - сохраняем путь
            photo_data = None
            actual_photo_path = ""
            if photo_path and os.path.exists(photo_path):
                actual_photo_path = photo_path
            elif photo_path:
                # Попытка загрузить как файл (возможно, относительный путь)
                try:
                    with open(photo_path, "rb") as img_file:
                        photo_data = base64.b64encode(img_file.read()).decode('utf-8')
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить фото: {e}")
                    return

            new_id, error = self.model.add_person(
                name=name,
                surname=surname,
                patronymic=patronymic,
                birth_date=birth_date,
                gender=gender,
                photo=photo_data,
                is_deceased=is_deceased,
                death_date=death_date,
                maiden_name=maiden_name,
                photo_path=actual_photo_path
            )

            if error:
                messagebox.showerror("Ошибка", error)
                return

            # Автоматическое связывание с родителем/супругом
            if parent_id and relation_type == "parent":
                # ← ИСПРАВЛЕНО: используем существующий метод add_parent
                self.model.add_parent(new_id, parent_id)  # ВНИМАНИЕ: порядок аргументов (родитель, ребёнок)
            elif parent_id and relation_type == "spouse":
                self.model.add_marriage(parent_id, new_id)

            dialog.destroy()
            self.refresh_view()
            messagebox.showinfo("Успех", f"Персона добавлена с ID: {new_id}")

        ttk.Button(btn_frame, text="Сохранить", command=submit, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Фокус на поле имени
        name_var.trace_add("write", lambda *args: None)  # Хак для фок��са
        dialog.after(100, lambda: name_var.set(name_var.get()))  # Обновление для фокуса
        
        # Автоподстройка размера под содержимое (после создания всех виджетов)
        dialog.update_idletasks()
        fit_dialog_to_content(dialog, min_width=400, min_height=500, max_width=600, max_height=800)


    def view_person(self):
        pid = self.last_selected_person_id
        if not pid or pid not in self.model.get_all_persons():
            messagebox.showerror("Ошибка", "Персона не выбрана или не существует.")
            return
        person = self.model.get_person(pid)
        info = f"Имя: {person.name}\nФамилия: {person.surname}\nОтчество: {person.patronymic}\n" \
               f"Дата рождения: {person.birth_date}\nПол: {person.gender}\n" \
               f"Умер: {'Да' if person.is_deceased else 'Нет'}\n" \
               f"Дата смерти: {person.death_date if person.is_deceased else '—'}\n" \
               f"Девичья фамилия: {person.maiden_name if person.maiden_name else '—'}\n" \
               f"Родители: {len(person.parents)}\nДети: {len(person.children)}"
        spouse_ids = self.model.get_spouses(pid)
        if spouse_ids:
            spouse_names = [self.model.get_person(sid).display_name() for sid in spouse_ids if self.model.get_person(sid)]
            info += "\nСупруг(а): " + ", ".join(spouse_names)
        messagebox.showinfo("И��формация о персоне", info)

    def edit_person(self):
        """Личная страница персоны: вкладки Основное, Семья, История и захоронение, Фотоальбом, Ссылки, Дополнительно."""
        if not self.model.current_center:
            messagebox.showinfo("Информация", "Сначала выберите персону (кликните по карточке).")
            return

        pid = self.model.current_center
        person = self.model.get_person(pid)
        if not person:
            messagebox.showerror("Ошибка", "Персона не найдена.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Личная страница: {person.display_name()}")
        dialog.geometry("560x720")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Применяем цвета темы ко всему диалогу
        is_dark_theme = constants.WINDOW_BG.lower() in ['#1e293b', '#0f172a', '#1a1a2e', '#16213e', '#2d3748', '#1a202c', '#2c3e50']
        
        if is_dark_theme:
            # Тёмная тема: красим ВСЁ окно
            dialog.configure(bg='#1e293b')
            
            # Создаём стили для тёмной темы
            style = ttk.Style()
            
            # Notebook (вкладки)
            style.configure('Dark.TNotebook', background='#1e293b', foreground='#f1f5f9')
            style.configure('Dark.TNotebook.Tab', background='#334155', foreground='#f1f5f9', padding=(12, 8), font=('Arial', 10))
            style.map('Dark.TNotebook.Tab',
                     background=[('selected', '#475569'), ('active', '#475569')],
                     foreground=[('selected', '#ffffff'), ('active', '#ffffff')])
            
            # Фреймы
            style.configure('Dark.TFrame', background='#1e293b')
            
            # Метки
            style.configure('Dark.TLabel', background='#1e293b', foreground='#f1f5f9', font=('Arial', 10))
            style.configure('Dark.TLabel', font=('Arial', 10, 'bold'))
            
            # Кнопки - КОНТРАСТНЫЕ
            style.configure('Dark.TButton', background='#3b82f6', foreground='#ffffff', font=('Arial', 10, 'bold'))
            style.map('Dark.TButton',
                     background=[('active', '#2563eb'), ('pressed', '#1d4ed8')])
            
            # Поля ввода
            style.configure('Dark.TEntry', fieldbackground='#334155', foreground='#ffffff', insertcolor='#ffffff', font=('Arial', 10))
            style.configure('Dark.TCombobox', fieldbackground='#334155', foreground='#ffffff', font=('Arial', 10))
            
            # Чекбоксы и радиокнопки
            style.configure('Dark.TCheckbutton', background='#1e293b', foreground='#f1f5f9', font=('Arial', 10))
            style.configure('Dark.TRadiobutton', background='#1e293b', foreground='#f1f5f9', font=('Arial', 10))
            
            # Разделители
            style.configure('Dark.TSeparator', background='#475569')
            
            # Текстовые поля
            style.configure('Dark.TText', background='#1e293b', foreground='#f1f5f9', font=('Arial', 10))
        
        # Переменные формы (общие для всех вкладок)
        form_vars = {}
        is_deceased = getattr(person, "is_deceased", False)
        if is_deceased in (None, "", "0", "false", "False"):
            is_deceased = False
        else:
            is_deceased = bool(is_deceased)

        def make_scrollable_tab(parent):
            """Фрейм с прокруткой для вкладки."""
            canvas = tk.Canvas(parent, bg=constants.WINDOW_BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            frame = ttk.Frame(canvas)
            frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            return frame

        notebook = ttk.Notebook(dialog)
        if is_dark_theme:
            notebook.configure(style='Dark.TNotebook')
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Вкладка 1: Основное ---
        tab_main = ttk.Frame(notebook, style='Dark.TFrame' if is_dark_theme else 'TFrame')
        notebook.add(tab_main, text="👤 Основное")
        f_main = make_scrollable_tab(tab_main)
        row = 0

        # Применяем стили для тёмной темы
        if is_dark_theme:
            style = ttk.Style()
            style.configure('TLabel', background='#1e293b', foreground='#ffffff')
            style.configure('TEntry', fieldbackground='#2d3748', foreground='#ffffff', insertcolor='#ffffff')
            style.configure('TButton', background='#2d3748', foreground='#ffffff', font=('Arial', 10, 'bold'))
            style.map('TButton',
                     background=[('active', '#4a5568'), ('pressed', '#1a202c')])
            style.configure('TCombobox', fieldbackground='#2d3748', foreground='#ffffff')
            style.configure('TCheckbutton', background='#1e293b', foreground='#ffffff')
            style.configure('TRadiobutton', background='#1e293b', foreground='#ffffff')
            style.configure('TSeparator', background='#718096')

        ttk.Label(f_main, text="Имя*", font=("Arial", 10, "bold")).grid(row=row, column=0, padx=10, pady=6, sticky='e')
        name_var = tk.StringVar(value=person.name)
        name_entry = ttk.Entry(f_main, textvariable=name_var, width=32)
        name_entry.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(name_entry)
        form_vars['name'] = name_var
        row += 1

        ttk.Label(f_main, text="Фамилия*", font=("Arial", 10, "bold")).grid(row=row, column=0, padx=10, pady=6, sticky='e')
        surname_var = tk.StringVar(value=person.surname)
        surname_entry = ttk.Entry(f_main, textvariable=surname_var, width=32)
        surname_entry.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(surname_entry)
        form_vars['surname'] = surname_var
        row += 1

        ttk.Label(f_main, text="Отчество").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        patronymic_var = tk.StringVar(value=person.patronymic or "")
        patronymic_entry = ttk.Entry(f_main, textvariable=patronymic_var, width=32)
        patronymic_entry.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(patronymic_entry)
        form_vars['patronymic'] = patronymic_var
        row += 1

        ttk.Label(f_main, text="Дата рождения").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        birth_date_var = tk.StringVar(value=person.birth_date or "")
        birth_entry = ttk.Entry(f_main, textvariable=birth_date_var, width=32)
        birth_entry.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        birth_entry.bind("<KeyPress>", self._date_entry_keypress)
        birth_entry.bind("<<Paste>>", lambda e, ent=birth_entry: self._date_entry_on_paste(ent))
        birth_entry.bind("<FocusOut>", self.normalize_date_on_focusout)
        form_vars['birth_date'] = birth_date_var
        row += 1

        ttk.Label(f_main, text="Место рождения").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        birth_place_var = tk.StringVar(value=getattr(person, "birth_place", "") or "")
        ttk.Entry(f_main, textvariable=birth_place_var, width=32).grid(row=row, column=1, padx=10, pady=6, sticky='w')
        form_vars['birth_place'] = birth_place_var
        row += 1

        ttk.Label(f_main, text="Пол").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        gender_var = tk.StringVar(value=person.gender)
        gender_frame = ttk.Frame(f_main)
        gender_frame.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        ttk.Radiobutton(gender_frame, text="Мужской", variable=gender_var, value="Мужской",
                       command=lambda: toggle_maiden_name()).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(gender_frame, text="Женский", variable=gender_var, value="Женский",
                       command=lambda: toggle_maiden_name()).pack(side=tk.LEFT)
        form_vars['gender'] = gender_var
        row += 1

        ttk.Label(f_main, text="Умер(ла)").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        deceased_var = tk.BooleanVar(value=is_deceased)
        ttk.Checkbutton(f_main, variable=deceased_var).grid(row=row, column=1, padx=10, pady=6, sticky='w')
        form_vars['is_deceased'] = deceased_var
        row += 1

        death_date_frame = ttk.Frame(f_main)
        death_date_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=0, sticky='w')
        ttk.Label(death_date_frame, text="Дата смерти", width=18).pack(side=tk.LEFT, padx=(0, 5))
        death_date_var = tk.StringVar(value=person.death_date or "")
        death_entry = ttk.Entry(death_date_frame, textvariable=death_date_var, width=32)
        death_entry.pack(side=tk.LEFT, padx=(0, 10))
        death_entry.bind("<KeyPress>", self._date_entry_keypress)
        death_entry.bind("<<Paste>>", lambda e, ent=death_entry: self._date_entry_on_paste(ent))
        death_entry.bind("<FocusOut>", self.normalize_date_on_focusout)
        form_vars['death_date'] = death_date_var
        death_date_stored = ""  # Для хранения даты при снятии галочки

        def toggle_death_ui(*a):
            nonlocal death_date_stored
            if deceased_var.get():
                death_date_frame.grid()
            else:
                # Сохраняем дату перед очисткой
                current_date = death_date_var.get().strip()
                if current_date:
                    death_date_stored = current_date
                    if not messagebox.askyesno("Подтверждение", "Дата смерти будет очищена. Сохранить её в буфере обмена для возможного восстановления?"):
                        death_date_stored = ""
                death_date_frame.grid_remove()
                death_date_var.set("")
        deceased_var.trace_add("write", toggle_death_ui)
        if is_deceased:
            death_date_frame.grid()
        else:
            death_date_frame.grid_remove()
        row += 1

        # Расчёт возраста и знака зодиака (отдельная строка)
        age_info_frame = ttk.Frame(f_main)
        age_info_frame.grid(row=row, column=1, padx=10, pady=2, sticky='w')

        def update_age_info(*args):
            """Обновляет информацию о возрасте и знаке зодиака."""
            for widget in age_info_frame.winfo_children():
                widget.destroy()

            birth_date_str = birth_date_var.get().strip()
            death_date_str = death_date_var.get().strip() if deceased_var.get() else ""

            if birth_date_str:
                age, zodiac = self._calculate_age_and_zodiac(birth_date_str, death_date_str)
                info_text = f"({age} лет"
                if zodiac:
                    info_text += f", {zodiac}"
                info_text += ")"
                ttk.Label(age_info_frame, text=info_text,
                         font=("Segoe UI", 9), foreground="#64748b").pack(side=tk.LEFT)

        # Привязка обновления к изменению дат
        birth_date_var.trace_add("write", update_age_info)
        death_date_var.trace_add("write", update_age_info)
        # Первоначальное обновление
        age_info_frame.after(100, lambda: update_age_info())

        row += 1

        maiden_name_frame = ttk.Frame(f_main)
        maiden_name_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=0, sticky='w')
        ttk.Label(maiden_name_frame, text="Девичья фамилия").pack(side=tk.LEFT, padx=(0, 10))
        maiden_name_var = tk.StringVar(value=person.maiden_name or "")
        ttk.Entry(maiden_name_frame, textvariable=maiden_name_var, width=28).pack(side=tk.LEFT)
        form_vars['maiden_name'] = maiden_name_var

        def toggle_maiden_name(*args):
            """Показывает/скрывает поле девичьей фамилии при смене пола."""
            if gender_var.get() == "Женский":
                maiden_name_frame.grid()
            else:
                current_maiden_name = maiden_name_var.get().strip()
                if current_maiden_name:
                    if not messagebox.askyesno("Подтверждение", "Очистить девичью фамилию?"):
                        gender_var.set("Женский")  # Вернуть пол обратно
                        return
                maiden_name_frame.grid_remove()
                maiden_name_var.set("")

        # Привязка к изменению пола
        gender_var.trace_add("write", toggle_maiden_name)

        if person.gender == "Женский":
            maiden_name_frame.grid()
        else:
            maiden_name_frame.grid_remove()
        row += 1

        # Основное фото (на основной вкладке — одно поле)
        ttk.Label(f_main, text="Главное фото").grid(row=row, column=0, padx=10, pady=6, sticky='e')
        photo_path_var = tk.StringVar(value=person.photo_path or "")
        photo_f = ttk.Frame(f_main)
        photo_f.grid(row=row, column=1, padx=10, pady=6, sticky='w')
        photo_entry = ttk.Entry(photo_f, textvariable=photo_path_var, width=24)
        photo_entry.pack(side=tk.LEFT, padx=(0, 5))
        self._enable_copy_paste(photo_entry)
        ttk.Button(photo_f, text="Обзор...", command=lambda: self.browse_photo(photo_path_var)).pack(side=tk.LEFT)
        form_vars['photo_path'] = photo_path_var
        row += 1

        preview_label = None
        if person.photo_path and os.path.exists(person.photo_path):
            try:
                img = Image.open(person.photo_path)
                img.thumbnail((100, 100), Image.LANCZOS)
                photo_img = ImageTk.PhotoImage(img)
                preview_label = ttk.Label(f_main, image=photo_img)
                preview_label.image = photo_img
                preview_label.grid(row=row, column=1, padx=10, pady=4, sticky='w')
                row += 1
            except Exception:
                pass

        # --- Вкладка 2: Семья (родители, супруги, дети + быстрые действия) ---
        tab_family = ttk.Frame(notebook)
        notebook.add(tab_family, text="👨‍👩‍👧‍👦 Семья")
        f_fam = make_scrollable_tab(tab_family)
        row_f = 0

        ttk.Label(f_fam, text="Родители", font=("Arial", 10, "bold")).grid(row=row_f, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_f += 1
        parents_list = list(person.parents) if person.parents else []
        mother_id = None
        father_id = None
        for p_id in parents_list:
            p_obj = self.model.get_person(p_id)
            if p_obj:
                if p_obj.gender == constants.GENDER_FEMALE:
                    mother_id = p_id
                else:
                    father_id = p_id
        for label, p_id in [("Мать:", mother_id), ("Отец:", father_id)]:
            ttk.Label(f_fam, text=label).grid(row=row_f, column=0, padx=10, pady=4, sticky='e')
            if p_id:
                p_obj = self.model.get_person(p_id)
                # Фрейм для родителя с кнопками действий
                parent_frame = ttk.Frame(f_fam)
                parent_frame.grid(row=row_f, column=1, padx=10, pady=4, sticky='w')

                # Расчёт возраста родителя
                age_text = ""
                if p_obj and p_obj.birth_date:
                    age, _ = self._calculate_age_and_zodiac(p_obj.birth_date, p_obj.death_date if p_obj.is_deceased else "")
                    if age and age != "?":
                        age_text = f" ({age} л.)"

                ttk.Label(parent_frame, text=f"{p_obj.display_name() if p_obj else str(p_id)}{age_text}",
                         font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))

                # Кнопки действий (используем p_id как default argument для замыкания)
                ttk.Button(parent_frame, text="👁", width=3,
                          command=lambda pid=p_id: self._view_person_by_id(pid)).pack(side=tk.LEFT, padx=2)
                ttk.Button(parent_frame, text="✏", width=3,
                          command=lambda pid=p_id: self._edit_person_by_id(pid, dialog)).pack(side=tk.LEFT, padx=2)
            else:
                ttk.Button(f_fam, text="Добавить из существующих",
                           command=lambda pid=pid, is_mother=(label == "Мать:"): self._add_parent_from_list_and_close(dialog, pid, is_mother)).grid(row=row_f, column=1, padx=10, pady=4, sticky='w')
            row_f += 1
        
        # Кнопка добавления родителя
        add_parent_btn = ttk.Button(f_fam, text="➕ Добавить родителя", 
                                   command=lambda: self._quick_add_parent(pid, dialog))
        add_parent_btn.grid(row=row_f, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        row_f += 1

        ttk.Label(f_fam, text="Супруг(и) / Партнёры", font=("Arial", 10, "bold")).grid(row=row_f, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_f += 1
        marriage_date_vars = {}  # Сохраняем переменные для дат брака
        for s_id in (person.spouse_ids or []):
            s = self.model.get_person(s_id)
            if s:
                # Получаем дату брака
                marriage_date = self.model.get_marriage_date(pid, s_id)
                # Имя супруга (с кнопками действий)
                spouse_frame = ttk.Frame(f_fam)
                spouse_frame.grid(row=row_f, column=0, columnspan=2, padx=10, pady=2, sticky='w')
                
                ttk.Label(spouse_frame, text=s.display_name(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))

                # Расчёт возраста супруга
                age_text = ""
                if s.birth_date:
                    age, _ = self._calculate_age_and_zodiac(s.birth_date, s.death_date if s.is_deceased else "")
                    if age and age != "?":
                        age_text = f" ({age} л.)"
                
                # Добавляем возраст к имени, если есть
                if age_text:
                    for widget in spouse_frame.winfo_children():
                        if isinstance(widget, ttk.Label) and widget.cget('text') == s.display_name():
                            widget.config(text=f"{s.display_name()}{age_text}")
                            break

                # Кнопка просмотра (используем s_id=s_id для замыкания)
                ttk.Button(spouse_frame, text="👁", width=3,
                          command=lambda s_id=s_id: self._view_person_by_id(s_id)).pack(side=tk.LEFT, padx=2)

                # Кнопка редактирования
                ttk.Button(spouse_frame, text="✏", width=3,
                          command=lambda s_id=s_id: self._edit_person_by_id(s_id, dialog)).pack(side=tk.LEFT, padx=2)

                # Поле для даты брака с расчётом лет вместе
                date_var = tk.StringVar(value=marriage_date or "")
                date_entry = ttk.Entry(spouse_frame, textvariable=date_var, width=12)
                date_entry.pack(side=tk.RIGHT, padx=5)
                ttk.Label(spouse_frame, text="Дата брака:").pack(side=tk.RIGHT, padx=(0, 5))
                
                # Метка для отображения лет вместе
                years_together_label = ttk.Label(spouse_frame, text="", font=("Segoe UI", 9), foreground="#64748b")
                years_together_label.pack(side=tk.RIGHT, padx=(5, 0))
                
                # Функция для обновления расчёта лет вместе
                def update_years_together(*args, dv=date_var, lbl=years_together_label):
                    marriage_date_str = dv.get().strip()
                    if marriage_date_str:
                        years = self._calculate_years_together(marriage_date_str)
                        if years:
                            lbl.config(text=f"({years} лет вместе)")
                    else:
                        lbl.config(text="")
                
                # Привязка обновления к изменению даты брака
                date_var.trace_add("write", update_years_together)
                # Первоначальное обновление
                years_together_label.after(100, lambda: update_years_together())

                # Сохраняем ссылку на переменную
                marriage_date_vars[(pid, s_id)] = date_var
                row_f += 1
        if not person.spouse_ids:
            ttk.Label(f_fam, text="— Нет", foreground="gray").grid(row=row_f, column=0, columnspan=2, padx=10, pady=2, sticky='w')
            row_f += 1
        
        # Кнопка добавления супруга
        add_spouse_btn = ttk.Button(f_fam, text="➕ Добавить супруга", 
                                   command=lambda: self._quick_add_spouse(pid, dialog))
        add_spouse_btn.grid(row=row_f, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        row_f += 1

        ttk.Label(f_fam, text="Дети", font=("Arial", 10, "bold")).grid(row=row_f, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_f += 1
        def _child_sort_key(cid):
            p = self.model.get_person(cid)
            birth_date = getattr(p, "birth_date", None) or ""
            # Преобразуем дату в формат YYYYMMDD для правильной сортировки
            if birth_date and len(birth_date) == 10:  # "ДД.ММ.ГГГГ"
                parts = birth_date.split('.')
                if len(parts) == 3:
                    sortable_date = f"{parts[2]}{parts[1]}{parts[0]}"  # "ГГГГММДД"
                else:
                    sortable_date = "99999999"
            else:
                sortable_date = "99999999"
            return (sortable_date, str(cid))
        for c_id in sorted(person.children or [], key=_child_sort_key):
            c = self.model.get_person(c_id)
            if c:
                # Фрейм для ребёнка с кнопками действий
                child_frame = ttk.Frame(f_fam)
                child_frame.grid(row=row_f, column=0, columnspan=2, padx=10, pady=2, sticky='w')
                
                # Расчёт возраста ребёнка
                age_text = ""
                if c.birth_date:
                    age, _ = self._calculate_age_and_zodiac(c.birth_date, c.death_date if c.is_deceased else "")
                    if age and age != "?":
                        age_text = f" ({age} л.)"
                
                ttk.Label(child_frame, text=f"{c.display_name()}{age_text}", 
                         font=("Arial", 10)).pack(side=tk.LEFT)
                
                # Кнопки действий (используем c_id=c_id для замыкания)
                ttk.Button(child_frame, text="👁", width=3,
                          command=lambda c_id=c_id: self._view_person_by_id(c_id)).pack(side=tk.LEFT, padx=5)
                ttk.Button(child_frame, text="✏", width=3,
                          command=lambda c_id=c_id: self._edit_person_by_id(c_id, dialog)).pack(side=tk.LEFT, padx=2)
                
                row_f += 1
        if not person.children:
            ttk.Label(f_fam, text="— Нет", foreground="gray").grid(row=row_f, column=0, columnspan=2, padx=10, pady=2, sticky='w')
            row_f += 1
        
        # Кнопка добавления ребёнка
        add_child_btn = ttk.Button(f_fam, text="➕ Добавить ребёнка", 
                                  command=lambda: self._quick_add_child(pid, dialog))
        add_child_btn.grid(row=row_f, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        row_f += 1

        # --- Вкладка 3: История ---
        tab_history = ttk.Frame(notebook)
        notebook.add(tab_history, text="📜 История")
        f_hist = make_scrollable_tab(tab_history)
        row_h = 0

        ttk.Label(f_hist, text="Биография, история жизни", font=("Arial", 10, "bold")).grid(row=row_h, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_h += 1
        biography_var = tk.StringVar(value=getattr(person, "biography", "") or "")
        bio_text = tk.Text(f_hist, width=48, height=8, wrap=tk.WORD, font=("Arial", 10))
        bio_text.grid(row=row_h, column=0, columnspan=2, padx=10, pady=6, sticky='ew')
        bio_text.insert("1.0", biography_var.get())
        self._enable_copy_paste(bio_text)
        form_vars['biography'] = (biography_var, bio_text)
        row_h += 1

        ttk.Label(f_hist, text="Захоронение (если умер(ла))", font=("Arial", 10, "bold")).grid(row=row_h, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_h += 1
        ttk.Label(f_hist, text="Место захоронения").grid(row=row_h, column=0, padx=10, pady=4, sticky='e')
        burial_place_var = tk.StringVar(value=getattr(person, "burial_place", "") or "")
        bp_entry = ttk.Entry(f_hist, textvariable=burial_place_var, width=36)
        bp_entry.grid(row=row_h, column=1, padx=10, pady=4, sticky='w')
        self._enable_copy_paste(bp_entry)
        form_vars['burial_place'] = burial_place_var
        row_h += 1
        ttk.Label(f_hist, text="Дата / год захоронения").grid(row=row_h, column=0, padx=10, pady=4, sticky='e')
        burial_date_var = tk.StringVar(value=getattr(person, "burial_date", "") or "")
        bd_entry = ttk.Entry(f_hist, textvariable=burial_date_var, width=36)
        bd_entry.grid(row=row_h, column=1, padx=10, pady=4, sticky='w')
        self._enable_copy_paste(bd_entry)
        form_vars['burial_date'] = burial_date_var
        row_h += 1

        # --- Вкладка 4: Фотоальбом (доп. фото) — показываем превью фотографий ---
        tab_photos = ttk.Frame(notebook)
        notebook.add(tab_photos, text="📷 Фотоальбом")
        f_ph = make_scrollable_tab(tab_photos)
        row_p = 0
        ttk.Label(f_ph, text="Дополнительные фото", font=("Arial", 10, "bold")).grid(row=row_p, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_p += 1
        photo_album_list = getattr(person, "photo_album", None) or []
        album_vars = [tk.StringVar(value=p) for p in photo_album_list]
        list_frame = ttk.Frame(f_ph)
        list_frame.grid(row=row_p, column=0, columnspan=2, padx=10, pady=6, sticky='nw')
        list_frame._photo_refs = []

        def _load_album_thumbnail(path_or_b64):
            """Загружает превью из пути к файлу или base64. Возвращает (PhotoImage или None, ширина, высота)."""
            if not path_or_b64 or not path_or_b64.strip():
                return None, 100, 80
            path_or_b64 = path_or_b64.strip()
            try:
                if os.path.isfile(path_or_b64):
                    image = Image.open(path_or_b64).convert("RGB")
                else:
                    raw = base64.b64decode(path_or_b64)
                    image = Image.open(io.BytesIO(raw)).convert("RGB")
                image.thumbnail((120, 100), Image.LANCZOS)
                photo_img = ImageTk.PhotoImage(image)
                return photo_img, photo_img.width(), photo_img.height()
            except Exception:
                return None, 100, 80

        def add_album_row():
            v = tk.StringVar()
            album_vars.append(v)
            _refresh_album_list()

        def _remove_album_row(idx):
            if 0 <= idx < len(album_vars):
                album_vars.pop(idx)
                _refresh_album_list()

        def _refresh_album_list():
            list_frame._photo_refs.clear()
            for w in list_frame.winfo_children():
                w.destroy()
            for r, v in enumerate(album_vars):
                thumb_img, tw, th = _load_album_thumbnail(v.get())
                if thumb_img:
                    list_frame._photo_refs.append(thumb_img)
                    lbl = tk.Label(list_frame, image=thumb_img, bd=1, relief=tk.SOLID)
                else:
                    lbl = tk.Label(list_frame, text="Нет превью", width=14, height=5, bd=1, relief=tk.SOLID)
                lbl.grid(row=r, column=0, padx=(0, 8), pady=4, sticky='nw')
                e = ttk.Entry(list_frame, textvariable=v, width=36)
                e.grid(row=r, column=1, padx=(0, 6), pady=4, sticky='w')
                self._enable_copy_paste(e)
                def browse_and_refresh(ev):
                    self._browse_and_set(ev)
                    _refresh_album_list()
                ttk.Button(list_frame, text="Обзор", width=8, command=lambda ev=v: browse_and_refresh(ev)).grid(row=r, column=2, pady=4)
                ttk.Button(list_frame, text="✕", width=2, command=lambda i=r: _remove_album_row(i)).grid(row=r, column=3, padx=2, pady=4)
                e.bind("<FocusOut>", lambda event: _refresh_album_list())
            ttk.Button(list_frame, text="+ Добавить фото", command=add_album_row).grid(row=len(album_vars), column=0, columnspan=3, pady=8, sticky='w')
            form_vars['photo_album_vars'] = album_vars

        def _browse_and_refresh(ev):
            self._browse_and_set(ev)
            _refresh_album_list()

        for r, v in enumerate(album_vars):
            thumb_img, tw, th = _load_album_thumbnail(v.get())
            if thumb_img:
                list_frame._photo_refs.append(thumb_img)
                lbl = tk.Label(list_frame, image=thumb_img, bd=1, relief=tk.SOLID)
            else:
                lbl = tk.Label(list_frame, text="Нет превью", width=14, height=5, bd=1, relief=tk.SOLID)
            lbl.grid(row=r, column=0, padx=(0, 8), pady=4, sticky='nw')
            e = ttk.Entry(list_frame, textvariable=v, width=36)
            e.grid(row=r, column=1, padx=(0, 6), pady=4, sticky='w')
            self._enable_copy_paste(e)
            ttk.Button(list_frame, text="Обзор", width=8, command=lambda ev=v: _browse_and_refresh(ev)).grid(row=r, column=2, pady=4)
            ttk.Button(list_frame, text="✕", width=2, command=lambda i=r: _remove_album_row(i)).grid(row=r, column=3, padx=2, pady=4)
        ttk.Button(list_frame, text="+ Добавить фото", command=add_album_row).grid(row=len(album_vars), column=0, columnspan=3, pady=8, sticky='w')
        form_vars['photo_album_vars'] = album_vars

        # --- Вкладка 5: Контакты (объединено со ссылками) ---
        tab_contacts = ttk.Frame(notebook)
        notebook.add(tab_contacts, text="📞 Контакты")
        f_cont = make_scrollable_tab(tab_contacts)
        row_c = 0

        # Телефон
        ttk.Label(f_cont, text="📞 Телефон").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        phone_var = tk.StringVar(value=getattr(person, "phone", "") or "")
        phone_entry = ttk.Entry(f_cont, textvariable=phone_var, width=36)
        phone_entry.grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(phone_entry)
        form_vars['phone'] = phone_var
        row_c += 1

        # Email
        ttk.Label(f_cont, text="✉ Email").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        email_var = tk.StringVar(value=getattr(person, "email", "") or "")
        email_entry = ttk.Entry(f_cont, textvariable=email_var, width=36)
        email_entry.grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(email_entry)
        form_vars['email'] = email_var
        row_c += 1

        # Адрес
        ttk.Label(f_cont, text="🏠 Адрес").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        address_var = tk.StringVar(value=getattr(person, "address", "") or "")
        address_entry = ttk.Entry(f_cont, textvariable=address_var, width=36)
        address_entry.grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(address_entry)
        form_vars['address'] = address_var
        row_c += 1

        # Разделитель
        ttk.Separator(f_cont, orient='horizontal').grid(row=row_c, column=0, columnspan=2, padx=10, pady=15, sticky='ew')
        row_c += 1

        # Социальные сети
        ttk.Label(f_cont, text="Социальные сети", font=("Arial", 10, "bold")).grid(row=row_c, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        row_c += 1

        # VK
        ttk.Label(f_cont, text="🔵 VK").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        vk_var = tk.StringVar(value=getattr(person, "vk", "") or "")
        vk_entry = ttk.Entry(f_cont, textvariable=vk_var, width=36)
        vk_entry.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['vk'] = vk_var
        row_c += 1

        # Telegram
        ttk.Label(f_cont, text="✈ Telegram").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        telegram_var = tk.StringVar(value=getattr(person, "telegram", "") or "")
        telegram_entry = ttk.Entry(f_cont, textvariable=telegram_var, width=36)
        telegram_entry.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['telegram'] = telegram_var
        row_c += 1

        # WhatsApp
        ttk.Label(f_cont, text="💬 WhatsApp").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        whatsapp_var = tk.StringVar(value=getattr(person, "whatsapp", "") or "")
        whatsapp_entry = ttk.Entry(f_cont, textvariable=whatsapp_var, width=36)
        whatsapp_entry.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['whatsapp'] = whatsapp_var
        row_c += 1

        # Разделитель
        ttk.Separator(f_cont, orient='horizontal').grid(row=row_c, column=0, columnspan=2, padx=10, pady=15, sticky='ew')
        row_c += 1

        # Медицинска���� информация
        ttk.Label(f_cont, text="🏥 Медиц����������нская информация", font=("Arial", 10, "bold")).grid(row=row_c, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        row_c += 1

        # Группа крови
        ttk.Label(f_cont, text="Группа крови").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        blood_type_var = tk.StringVar(value=getattr(person, "blood_type", "") or "")
        blood_type_combo = ttk.Combobox(f_cont, textvariable=blood_type_var, width=33, state="readonly")
        blood_type_combo['values'] = ("I (0)", "II (A)", "III (B)", "IV (AB)", "Неизвестно")
        blood_type_combo.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['blood_type'] = blood_type_var
        row_c += 1

        # Резус-фактор
        ttk.Label(f_cont, text="Резус-фактор").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        rh_var = tk.StringVar(value=getattr(person, "rh_factor", "") or "")
        rh_combo = ttk.Combobox(f_cont, textvariable=rh_var, width=33, state="readonly")
        rh_combo['values'] = ("Rh+", "Rh-", "Неизвестно")
        rh_combo.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['rh_factor'] = rh_var
        row_c += 1

        # Аллергии
        ttk.Label(f_cont, text="Аллергии").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        allergies_var = tk.StringVar(value=getattr(person, "allergies", "") or "")
        allergies_entry = ttk.Entry(f_cont, textvariable=allergies_var, width=36)
        allergies_entry.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['allergies'] = allergies_var
        row_c += 1

        # Хронические заболевания
        ttk.Label(f_cont, text="Хронические заболевания").grid(row=row_c, column=0, padx=10, pady=4, sticky='e')
        chronic_var = tk.StringVar(value=getattr(person, "chronic_conditions", "") or "")
        chronic_entry = ttk.Entry(f_cont, textvariable=chronic_var, width=36)
        chronic_entry.grid(row=row_c, column=1, padx=10, pady=4, sticky='w')
        form_vars['chronic_conditions'] = chronic_var
        row_c += 1

        # Разделитель
        ttk.Separator(f_cont, orient='horizontal').grid(row=row_c, column=0, columnspan=2, padx=10, pady=15, sticky='ew')
        row_c += 1

        # --- Вкладка: Ссылки (объединено с Контактами) ---
        ttk.Label(f_cont, text="🔗 Ссылки на информацию в интернете", font=("Arial", 10, "bold")).grid(row=row_c, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_c += 1
        links_data = getattr(person, "links", None) or []
        links_vars = []  # list of (title_var, url_var)
        links_frame = ttk.Frame(f_cont)
        links_frame.grid(row=row_c, column=0, columnspan=2, padx=10, pady=6, sticky='nw')

        def add_link_row(title="", url=""):
            tv = tk.StringVar(value=title)
            uv = tk.StringVar(value=url)
            links_vars.append((tv, uv))
            _refresh_links_list()

        def _remove_link_row(idx):
            if 0 <= idx < len(links_vars):
                links_vars.pop(idx)
                _refresh_links_list()

        def _refresh_links_list():
            for w in links_frame.winfo_children():
                w.destroy()
            for r, (tv, uv) in enumerate(links_vars):
                e_title = ttk.Entry(links_frame, textvariable=tv, width=18)
                e_title.grid(row=r, column=0, padx=(0, 4), pady=2, sticky='w')
                self._enable_copy_paste(e_title)
                e_url = ttk.Entry(links_frame, textvariable=uv, width=28)
                e_url.grid(row=r, column=1, padx=(0, 4), pady=2, sticky='w')
                self._enable_copy_paste(e_url)
                ttk.Button(links_frame, text="✕", width=2, command=lambda i=r: _remove_link_row(i)).grid(row=r, column=2, pady=2)
                ttk.Button(links_frame, text="Открыть", width=6, command=lambda u=uv: self._open_url(u.get())).grid(row=r, column=3, padx=2, pady=2)
            ttk.Button(links_frame, text="+ Добавить ссылку", command=lambda: add_link_row()).grid(row=len(links_vars), column=0, columnspan=2, pady=8, sticky='w')

        for item in links_data:
            add_link_row(item.get("title", ""), item.get("url", ""))
        if not links_vars:
            add_link_row("", "")
        form_vars['links_vars'] = links_vars

        # --- Вкладка 6: Дополнительно ---
        tab_extra = ttk.Frame(notebook)
        notebook.add(tab_extra, text="⚙️ Дополнительно")
        f_extra = make_scrollable_tab(tab_extra)
        row_e = 0

        ttk.Label(f_extra, text="Профессия / род занятий").grid(row=row_e, column=0, padx=10, pady=6, sticky='e')
        occupation_var = tk.StringVar(value=getattr(person, "occupation", "") or "")
        occ_entry = ttk.Entry(f_extra, textvariable=occupation_var, width=36)
        occ_entry.grid(row=row_e, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(occ_entry)
        form_vars['occupation'] = occupation_var
        row_e += 1

        ttk.Label(f_extra, text="Образование").grid(row=row_e, column=0, padx=10, pady=6, sticky='e')
        education_var = tk.StringVar(value=getattr(person, "education", "") or "")
        edu_entry = ttk.Entry(f_extra, textvariable=education_var, width=36)
        edu_entry.grid(row=row_e, column=1, padx=10, pady=6, sticky='w')
        self._enable_copy_paste(edu_entry)
        form_vars['education'] = education_var
        row_e += 1

        ttk.Label(f_extra, text="Заметки", font=("Arial", 10, "bold")).grid(row=row_e, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_e += 1
        notes_var = tk.StringVar(value=getattr(person, "notes", "") or "")
        notes_text = tk.Text(f_extra, width=48, height=6, wrap=tk.WORD, font=("Arial", 10))
        notes_text.grid(row=row_e, column=0, columnspan=2, padx=10, pady=6, sticky='ew')
        notes_text.insert("1.0", notes_var.get())
        self._enable_copy_paste(notes_text)
        form_vars['notes'] = (notes_var, notes_text)
        row_e += 1

        # --- Кнопки внизу ---
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=15)

        def submit_edit():
            name = name_var.get().strip()
            surname = surname_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Имя обязательно.")
                return
            if not surname:
                messagebox.showerror("Ошибка", "Фамилия обязательна.")
                return

            # Валидация дат
            birth_date_val = birth_date_var.get().strip()
            death_date_val = death_date_var.get().strip() if deceased_var.get() else ""
            burial_date_val = burial_date_var.get().strip()

            if birth_date_val and not self.model._validate_date(birth_date_val):
                messagebox.showerror("Ошибка", "Неверный формат даты рождения. Используйте ДД.ММ.ГГГГ.")
                return
            if death_date_val and not self.model._validate_date(death_date_val):
                messagebox.showerror("Ошибка", "Неверный формат даты смерти. Используйте ДД.ММ.ГГГГ.")
                return
            if burial_date_val and not self.model._validate_date(burial_date_val):
                messagebox.showerror("Ошибка", "Неверный формат даты захо��онения. Используйте ДД.ММ.ГГГГ.")
                return

            # Валидация email
            email_val = email_var.get().strip()
            if email_val and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_val):
                messagebox.showerror("Ошибка", "Некорректный email адрес.")
                return

            # Валидация URL в ссылках
            for t, u in links_vars:
                url = u.get().strip()
                if url and not url.startswith(('http://', 'https://', 'ftp://')):
                    messagebox.showerror("Ошибка", f"URL должен начинаться с http:// или https://: {url}")
                    return

            person.name = name
            person.surname = surname
            person.patronymic = patronymic_var.get().strip()
            person.birth_date = birth_date_val
            person.birth_place = birth_place_var.get().strip()
            person.is_deceased = deceased_var.get()
            person.death_date = death_date_val
            person.gender = gender_var.get()
            person.maiden_name = maiden_name_var.get().strip() if gender_var.get() == "Женский" else ""

            photo_path = photo_path_var.get().strip()
            if photo_path and os.path.exists(photo_path):
                person.photo_path = photo_path
                person.photo = None
            elif not photo_path:
                person.photo_path = ""
                person.photo = None

            person.biography = bio_text.get("1.0", tk.END).strip()
            person.burial_place = burial_place_var.get().strip()
            person.burial_date = burial_date_var.get().strip()
            person.photo_album = [v.get().strip() for v in album_vars if v.get().strip()]
            person.links = [{"title": t.get().strip(), "url": u.get().strip()} for t, u in links_vars if u.get().strip()]
            person.occupation = occupation_var.get().strip()
            person.education = education_var.get().strip()
            person.address = address_var.get().strip()
            person.notes = notes_text.get("1.0", tk.END).strip()

            # Социальные сети
            person.vk = vk_var.get().strip()
            person.telegram = telegram_var.get().strip()
            person.whatsapp = whatsapp_var.get().strip()

            # Медицинская информация
            person.blood_type = blood_type_var.get().strip()
            person.rh_factor = rh_var.get().strip()
            person.allergies = allergies_var.get().strip()
            person.chronic_conditions = chronic_var.get().strip()

            # Сохраняем даты браков
            for (p1_id, p2_id), date_var in marriage_date_vars.items():
                self.model.set_marriage_date(p1_id, p2_id, date_var.get().strip())

            self.model.mark_modified()
            dialog.destroy()
            self.refresh_view()
            messagebox.showinfo("Успех", f"Данные персоны «{person.display_name()}» сохранены.")

        ttk.Button(btn_frame, text="Сохранить", command=submit_edit, style="Success.TButton").pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="О��мена", command=dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        dialog.after(100, lambda: name_var.set(name_var.get()))
        
        # Автоподстройка размера под содержимое (после создания всех виджетов)
        dialog.update_idletasks()
        fit_dialog_to_content(dialog, min_width=500, min_height=600, max_width=800, max_height=900)

    def remove_person_photo(self, person, preview_label, photo_path_var):
        """
        Удаляет фото у персоны.
        """
        if messagebox.askyesno("Удалить фото", "Вы уверены, что хотите удалить фото эт��й персоны?"):
            person.photo_path = ""
            person.photo = None
            self.model.mark_modified()

            # Обновляем интерфейс
            if preview_label:
                preview_label.grid_remove()
            photo_path_var.set("")

            messagebox.showinfo("Успех", "Фото удалено.")


    def browse_photo(self, var):
        """
        Диалог выбора файла фото.
        var - StringVar для сохранения пути к файлу.
        """
        filename = filedialog.askopenfilename(
            title="Выберите фото",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if filename:
            var.set(filename)

    def _browse_and_set(self, string_var):
        """Выбор файла (фото) и запись пути в StringVar."""
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        )
        if path:
            string_var.set(path)

    def _open_url(self, url):
        """Открыть ссылку в браузере."""
        url = (url or "").strip()
        if not url:
            return
        try:
            import webbrowser
            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
        except Exception:
            messagebox.showerror("Ошибка", "Не удалось открыть ссылку.")

    def _add_parent_from_list_and_close(self, edit_dialog, child_id, is_mother):
        """Добавить родителя из списка существующих персон, затем закрыть ��кно редактирования."""
        child = self.model.get_person(child_id)
        if not child:
            return
        need_gender = constants.GENDER_FEMALE if is_mother else constants.GENDER_MALE
        all_persons = self.model.get_all_persons()
        candidates = [pid for pid, p in all_persons.items() if p.gender == need_gender and pid != child_id and pid not in (child.parents or set())]
        if not candidates:
            messagebox.showinfo("Добавить родителя", "Нет подходящих персон в древе (нуж��н пол: " + ("женский" if is_mother else "мужской") + "). Создайте персону через меню «Добавить» → «Родителя».")
            return
        parent_id = self.select_person_from_list(candidates, "Выберите " + ("мать" if is_mother else "отца") + ":")
        if not parent_id:
            return
        self.model.add_parent(child_id, parent_id)
        child_after = self.model.get_person(child_id)
        if child_after and child_after.parents:
            for other_id in child_after.parents:
                if str(other_id) != str(parent_id):
                    self.model.add_marriage(parent_id, other_id)
                    break
        self.model.mark_modified()
        edit_dialog.destroy()
        self.refresh_view()
        messagebox.showinfo("Успех", "Родитель добавлен.")

    def delete_person(self):
        """Метод для удалени�� персоны, вызываемый из контекстного меню."""
        # Получаем ID последней выбранной персоны
        pid = self.last_selected_person_id

        # Проверяем, что персона была выбрана
        if not pid or pid not in self.model.get_all_persons():
            messagebox.showerror("Ошибка", "Персона не выбрана или не существует.")
            return

        person = self.model.get_person(pid)

        # Запр��шиваем подтверждение на удаление
        if not messagebox.askyesno("Подтверждение удаления",
                                   f"Вы уверены, что хотите удалить персону '{person.display_name()}' и все связанные с ней данные (родители, дети, браки)?"):
            return  # Пользователь отменил удаление

        # Вызываем метод удаления из модели
        success, message = self.model.delete_person(pid)

        if success:
            messagebox.showinfo("Успех", message)
            # Обновляем интерфейс
            self.refresh_view()
            # Сбрасываем выделение, так как персона удалена
            self.last_selected_person_id = None
        else:
            messagebox.showerror("Ошибка", message)


    def _confirm_and_remove_spouse_link(self, person1_id, person2_id, dialog_window):
        """Запрашивает подтверждение и удаляет супружескую связь."""
        p1 = self.model.get_person(person1_id)
        p2 = self.model.get_person(person2_id)
        if not p1 or not p2:
            messagebox.showerror("Ошибка", "Не удалось получ��ть данные супругов.")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить брак меж��у '{p1.display_name()}' и '{p2.display_name()}'?"):
            # Вызываем метод модели для двустороннего удаления
            success = self.model.remove_spouse_link(person1_id, person2_id)
            if success:
                messagebox.showinfo("Успех", f"Связь между {p1.display_name()} и {p2.display_name()} удалена.")
                # Пересоздаём окно редактирования, чтобы обновить список супругов
                dialog_window.destroy()
                self.edit_person()  # Перезапускаем диалог для обновления
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить связь.")

    def _submit_edit_person(self, person, form_data):
        # Обновляем данные персоны
        person.name = form_data.get("name", "").strip()
        person.surname = form_data.get("surname", "").strip()
        person.patronymic = form_data.get("patronymic", "").strip()
        person.birth_date = form_data.get("birth_date", "").strip()
        person.death_date = form_data.get("death_date", "").strip()
        person.is_deceased = form_data.get("is_deceased", False)
        person.photo_path = form_data.get("photo_path", "")
        person.maiden_name = form_data.get("maiden_name", "")

        # Контакты
        person.phone = form_data.get("phone", "").strip()
        person.email = form_data.get("email", "").strip()
        person.address = form_data.get("address", "").strip()

        # Социальные сети
        person.vk = form_data.get("vk", "").strip()
        person.telegram = form_data.get("telegram", "").strip()
        person.whatsapp = form_data.get("whatsapp", "").strip()

        # Медицинская информация
        person.blood_type = form_data.get("blood_type", "").strip()
        person.rh_factor = form_data.get("rh_factor", "").strip()
        person.allergies = form_data.get("allergies", "").strip()
        person.chronic_conditions = form_data.get("chronic_conditions", "").strip()

        # Устанавливаем флаг изменений
        self.mark_modified()

        return True, constants.MSG_SUCCESS_PERSON_EDITED


    def add_parent_dialog(self, child_id, parent_gender):
        """Диалог добавления родителя для выбранного ребёнка с автозаполнением имени из отчества."""
        # Если child_id не передан (например, клик на пустом месте), спрашиваем
        if not child_id:
            all_persons = self.model.get_all_persons()
            if not all_persons:
                messagebox.showerror("Ошибка", "Нет персон дл�� выбора ребёнка.")
                return
            options = [p.display_name() for p in all_persons.values()]
            selected_name = simpledialog.askstring("Выбор ребёнка", "Введите имя ребёнка (или часть):", initialvalue="")
            if not selected_name:
                return
            found_persons = [pid for pid, p in all_persons.items() if selected_name.lower() in p.display_name().lower()]
            if not found_persons:
                messagebox.showerror("Ошибка", "Персона не найдена.")
                return
            if len(found_persons) > 1:
                # Показать список и попросить выбрать
                selected_pid = self.select_person_from_list(found_persons, "Выберите ребёнка:")
                if not selected_pid:
                    return
                child_id = selected_pid
            else:
                child_id = found_persons[0]
        child = self.model.get_person(child_id)
        if not child:
            messagebox.showerror("Ошибка", "Ребёнок не найден")
            return
        parent_type = "отца" if parent_gender == "Мужской" else "мать"
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Добавить {parent_type} для {child.display_name()}")
        dialog.geometry("500x450")
        dialog.resizable(True, True)
        
        # Создаём контейнер для скроллируемой области
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_container, bg=constants.WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Автогенерация имени из отчества ребёнка (для отца)
        auto_name = ""
        if parent_gender == "Мужской" and child.patronymic:
            auto_name = self.model.generate_name_from_patronymic(child.patronymic, "Мужской")
        # Автогенерация фамилии (берём фамилию ребёнка или отца)
        auto_surname = child.get_current_surname()
        # Конфигурация формы
        fields_config = [
            ("Имя:", "Entry", auto_name, {}),
            ("Фамилия:", "Entry", auto_surname, {}),
            ("Отчество:", "Entry", "", {}),
        ]
        entries, _, row = create_form_fields(scrollable_frame, fields_config)
        for key in ("Имя:", "Фамилия:", "Отчество:"):
            if key in entries:
                self._enable_copy_paste(entries[key])
        # Подсказка об автозаполнении
        if auto_name:
            ttk.Label(scrollable_frame, text=f"Автоопределено из отчества '{child.patronymic}'",
                      font=("Arial", 8, "italic"), foreground="#7f8c8d").grid(
                row=row - 3, column=1, padx=10, pady=(0, 2), sticky='w')

        def submit():
            name = entries["Имя:"].get().strip()
            surname = entries["Фамилия:"].get().strip()
            patronymic = entries["Отчество:"].get().strip()
            if not name or not surname:
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_NAME_SURNAME_REQUIRED)
                return
            parent_id, error = self.model.add_or_link_parent(child_id, name, surname, patronymic, parent_gender)
            if error:
                messagebox.showerror("Ошибка", error)
                return
            # Связываем нового родителя браком с остальными родителями ребёнка, чтобы пара отображалась на холсте
            child_after = self.model.get_person(child_id)
            if child_after and child_after.parents:
                for other_id in child_after.parents:
                    if str(other_id) != str(parent_id):
                        self.model.add_marriage(parent_id, other_id)
            messagebox.showinfo("Успех", f"{parent_type.capitalize()} успешно добавлен(а)!")
            dialog.destroy()
            # Центр оставляем на ребёнке (для кого добавляли родителя), чтобы персона не пропадала с холста
            persons = self.model.get_all_persons()
            center_key = next((k for k in persons if str(k) == str(child_id)), None)
            self.model.current_center = center_key if center_key is not None else child_id
            self.refresh_view()

        # Кнопки — фиксируем внизу окна (вне прокручиваемой области)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(button_frame, text="Сохранить", command=submit).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10, pady=10)

    def add_child_dialog(self, parent_id, child_gender):
        # Если parent_id не передан, спрашиваем
        if not parent_id:
            all_persons = self.model.get_all_persons()
            if not all_persons:
                messagebox.showerror("Ошибка", "Нет персон для выбора родителя.")
                return
            options = [p.display_name() for p in all_persons.values()]
            selected_name = simpledialog.askstring("Выбор родителя", "Введите имя родителя (ил�� часть):",
                                                   initialvalue="")
            if not selected_name:
                return
            found_persons = [pid for pid, p in all_persons.items() if selected_name.lower() in p.display_name().lower()]
            if not found_persons:
                messagebox.showerror("Ошибка", "Персона не найдена.")
                return
            if len(found_persons) > 1:
                selected_pid = self.select_person_from_list(found_persons, "Выберите родителя:")
                if not selected_pid:
                    return
                parent_id = selected_pid
            else:
                parent_id = found_persons[0]
        parent = self.model.get_person(parent_id)
        if not parent:
            messagebox.showerror("Ошибка", "Родитель не найден")
            return
        parent_spouse_ids = self.model.get_spouses(parent_id)
        parent_spouses = [self.model.get_person(sid) for sid in parent_spouse_ids]
        parent_spouses = [p for p in parent_spouses if p]
        dialog = tk.Toplevel(self.root)
        title_suffix = f" и {parent_spouses[0].display_name()}" if len(parent_spouses) == 1 else ""
        if len(parent_spouses) > 1:
            title_suffix = " (выберите второго родителя при сохранении)"
        dialog.title(f"Добавить ребёнка для {parent.display_name()}{title_suffix}")
        dialog.geometry("550x650")
        dialog.resizable(True, True)
        
        # Создаём контейнер для скроллируемой области
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_container, bg=constants.WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Конфигурация формы
        fields_config = [
            ("Имя ребёнка:", "Entry", "", {}),
            ("Фамилия ребёнка:", "Entry", parent.get_current_surname(), {}),  # Автофамилия от родителя
            ("Отчество ребёнка:", "Entry",
             self.model.generate_patronymic(parent.name) if parent.gender == constants.GENDER_MALE else "", {}),
            # Автоотчество от отца
            ("Дата рождения (ДД.ММ.ГГГГ):", "Entry", "", {}),
            ("Дат�� смерти (ДД.ММ.ГГГГ):", "Entry", "", {}),
            ("Пол ребёнка:", "Label", "", {}),
        ]
        entries, _, row = create_form_fields(scrollable_frame, fields_config)
        for key in ("Имя ребёнка:", "Фамилия ребёнка:", "Отчество р��бёнка:"):
            if key in entries:
                self._enable_copy_paste(entries[key])
        # Привязываем ввод дат (только цифры + автоточки)
        for key in ["Дата рождения (ДД.ММ.ГГГГ):", "Дата смерти (ДД.ММ.ГГГГ):"]:
            entries[key].bind("<KeyPress>", self._date_entry_keypress)
            entries[key].bind("<<Paste>>", lambda e, k=key: self._date_entry_on_paste(entries[k]))
            entries[key].bind("<FocusOut>", self.normalize_date_on_focusout)

        # Пол ребёнка (Radiobuttons)
        child_gender_var = tk.StringVar(value=child_gender)
        ttk.Radiobutton(scrollable_frame, text="Мужской", variable=child_gender_var, value="Мужской").grid(row=row,
                                                                                                           column=1,
                                                                                                           sticky='w')
        ttk.Radiobutton(scrollable_frame, text="Женский", variable=child_gender_var, value="Женский").grid(row=row,
                                                                                                           column=1,
                                                                                                           sticky='e')
        row += 1
        # Умер (Checkbutton)
        is_deceased_var = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text="Умер", variable=is_deceased_var).grid(row=row, column=0, columnspan=2,
                                                                                      padx=10, pady=8, sticky='w')
        row += 1
        # Второй родитель (если супруг не выбран)
        ttk.Label(scrollable_frame, text="Второй родитель (необязательно):", font=("Arial", 10, "bold")).grid(row=row,
                                                                                                              column=0,
                                                                                                              columnspan=2,
                                                                                                              sticky='w',
                                                                                                              pady=(
                                                                                                                  10,
                                                                                                                  5))
        row += 1
        second_parent_options = tk.StringVar(value="Нет")
        ttk.Radiobutton(scrollable_frame, text="Не добавлять второго родителя", variable=second_parent_options,
                        value="Нет").grid(row=row, column=0, columnspan=2, sticky='w', padx=10)
        row += 1
        for sp in parent_spouses:
            ttk.Radiobutton(scrollable_frame, text=f"Добавить как {sp.display_name()} (супруг)",
                            variable=second_parent_options, value=sp.id).grid(row=row, column=0, columnspan=2,
                                                                                  sticky='w', padx=10)
            row += 1
        ttk.Radiobutton(scrollable_frame, text="Выбрать из ��уществующих", variable=second_parent_options,
                        value="Select").grid(row=row, column=0, columnspan=2, sticky='w', padx=10)
        row += 1
        ttk.Radiobutton(scrollable_frame, text="Создать нового", variable=second_parent_options, value="Create").grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10)
        row += 1

        def submit():
            name = entries["Имя ребёнка:"].get().strip()
            surname = entries["Фамилия ребёнка:"].get().strip()
            patronymic = entries["Отчество ребёнка:"].get().strip()
            birth_date = entries["Дата рождения (ДД.ММ.ГГГГ):"].get().strip()
            death_date = entries["Дата смерти (ДД.ММ.ГГГГ):"].get().strip()
            gender = child_gender_var.get()
            is_deceased = is_deceased_var.get()
            second_parent_mode = second_parent_options.get()
            if not name or not surname:
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_NAME_SURNAME_REQUIRED)
                return
            # УДАЛЯЕМ проверку на обязательность birth_date
            # if not birth_date:
            #     messagebox.showerror("Ошибка", "Поле 'Дата рождения' обязательно для заполнения")
            #     return
            if not self.model._validate_date(birth_date):
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_BIRTH_DATE_INVALID)
                return
            if is_deceased and death_date and not self.model._validate_date(death_date):
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_DEATH_DATE_INVALID)
                return
            # УДАЛЯ��М проверку на обязательность death_date если is_deceased
            # if is_deceased and not death_date:
            #     messagebox.showerror("Ошибка", constants.VALIDATION_MSG_DEATH_DATE_NEEDED)
            #     return
            # Добавляем ребёнка
            child_id, error = self.model.add_person(name, surname, patronymic, birth_date, gender, "", is_deceased,
                                                    death_date, "")
            if error:
                messagebox.showerror("Ошибка", error)
                return
            # Связываем с первым родителем
            self.model.add_parent(child_id, parent_id)
            # Обработка второго родителя
            if second_parent_mode != "Нет":
                if second_parent_mode in parent_spouse_ids:
                    # Выбран один из супругов родителя (в т.ч. второй/третий супруг)
                    self.model.add_parent(child_id, second_parent_mode)
                elif second_parent_mode == "Select":
                    available = []
                    all_persons = self.model.get_all_persons()
                    opposite_gender = constants.GENDER_FEMALE if parent.gender == constants.GENDER_MALE else constants.GENDER_MALE
                    for p in all_persons.values():
                        if p.gender == opposite_gender and p.id != parent_id:
                            available.append(p)
                    if not available:
                        messagebox.showwarning("Предупреждение", "Нет подходящих персон для второго родителя.")
                    else:
                        selected_spouse = self.select_person_from_list([p.id for p in available],
                                                                       "Выберите второго родителя:")
                        if selected_spouse:
                            self.model.add_parent(child_id, selected_spouse)
                elif second_parent_mode == "Create":
                    # Открываем диалог создания второго родителя
                    dialog.destroy()
                    second_gender = constants.GENDER_FEMALE if parent.gender == constants.GENDER_MALE else constants.GENDER_MALE
                    self.add_parent_dialog(child_id,
                                           second_gender)  # Вызовется рекурсивно, но child_id уже будет существовать
                    return  # Выходим, чтобы не закрывать диалог дважды
            messagebox.showinfo("Успех", "Ребёнок успешно добавлен!")
            dialog.destroy()
            self.refresh_view()

        # Кнопки — фиксируем внизу окна (вне прокручиваемой области)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(button_frame, text="Сохранить", command=submit).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10, pady=10)

    def add_sibling_dialog(self, person_id, sibling_gender):
        """Диалог добавления брата/сестры с автозаполнением отчества от имени отца.
        После добавления **не меняет** центр, а обновл��ет отображение."""
        person = self.model.get_person(person_id)
        if not person:
            messagebox.showerror("Ошибка", "Персона не найдена")
            return

        sibling_type = "брата" if sibling_gender == "Мужской" else "сестру"
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Добавить {sibling_type} для {person.display_name()}")
        dialog.geometry("500x450")
        dialog.resizable(True, True)

        # СНАЧАЛА создаем фрейм для кнопок
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Создаем функцию submit заранее (чтобы передать её в кнопки)
        def submit():
            name = entries["Имя:"].get().strip()
            surname = entries["Фамилия:"].get().strip()
            patronymic = patronymic_var.get().strip()
            birth_date = entries["Дата рождения (ДД.ММ.ГГГГ):"].get().strip()
            death_date = entries["Дата смерти (ДД.ММ.ГГГГ):"].get().strip() if deceased_var.get() else ""
            is_deceased = deceased_var.get()
            gender = sibling_gender
            photo_path = photo_path_var.get().strip()

            if not name or not surname:
                messagebox.showerror("Ошибка", "Имя и фамилия обязательны для заполнения.")
                return

            # === Добавляем персону ===
            sibling_id, error = self.model.add_person(
                name=name,
                surname=surname,
                patronymic=patronymic,
                birth_date=birth_date,
                death_date=death_date if is_deceased else "",
                is_deceased=is_deceased,
                gender=gender,
                photo_path=photo_path
            )
            if error:
                messagebox.showerror("Ошибка", error)
                return

            # === Устанавливаем связи с родителями текущей персоны ===
            for parent_id in person.parents:
                sibling_obj = self.model.get_person(sibling_id)
                parent_obj = self.model.get_person(parent_id)
                if sibling_obj and parent_obj:
                    # Убеждаемся, что связи двусторонние
                    sibling_obj.parents.add(parent_id)
                    parent_obj.children.add(sibling_id)
                    # Также добавляем нового ребёнка к другому родителю, если он есть
                    other_parents = [p_id for p_id in person.parents if p_id != parent_id]
                    for other_pid in other_parents:
                        other_parent_obj = self.model.get_person(other_pid)
                        if other_parent_obj:
                            other_parent_obj.children.add(sibling_id)
                            sibling_obj.parents.add(other_pid)

            # Помечаем модель как изменённую
            self.model.mark_modified()

            # === Сообщение об успехе ===
            messagebox.showinfo("Успех", f"{sibling_type.capitalize()} успешно добавлен(а)!")

            # === Критическое исправление 2: Явно сохраняем и восстанавливаем current_center ===
            # Сохраняем текущий центр до обновления
            original_center = self.model.current_center
            # Устанавливаем центр на персону, для которой добавляли родственника (person_id)
            # Это защитит от внутренних изменений в refresh_view, если current_center был None
            self.model.current_center = person_id

            # === Обновляем отображение ===
            dialog.destroy()
            # Явно вызываем refresh_view, которое теперь будет использовать person_id как центр
            self.refresh_view()

        # СРАЗУ добавляем кнопки (пока scroll_container ещё не занял место)
        ttk.Button(btn_frame, text="Сохранить", command=submit).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10, pady=10)

        # === Фрейм для прокрутки (после кнопок, чтобы не перекрывать их) ===
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, bg=constants.WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        # === /Фрейм для прокрутки ===

        # Принудительно обновляем геометрию, чтобы кнопки были видны
        dialog.update_idletasks()

        # --- Форма ---
        frame = ttk.Frame(scrollable_frame, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Автозаполнение отчества для брата/сестры
        auto_patronymic = ""
        father_id = None
        # Находим отца среди родителей текущей персоны
        if person.parents:
            all_parents = [self.model.get_person(pid) for pid in person.parents]
            father = next((p for p in all_parents if p and p.gender == "Мужской"), None)
            if father and father.name:
                clean_name = father.name.strip()
                if clean_name.endswith(('а', 'я')) and clean_name.lower() not in ['лев', 'павел']:
                    auto_patronymic = clean_name + "ична"
                elif clean_name.endswith('ь'):
                    auto_patronymic = clean_name[:-1] + "евич" if sibling_gender == "Муж��кой" else clean_name[
                                                                                                       :-1] + "евна"
                elif clean_name.endswith('й'):
                    auto_patronymic = clean_name[:-1] + "евич" if sibling_gender == "Мужской" else clean_name[
                                                                                                       :-1] + "евна"
                else:
                    auto_patronymic = clean_name + "ович" if sibling_gender == "Мужской" else clean_name + "овна"
                father_id = father.id  # Сохраняем ID найденного отца для подсказки

        # Поля формы
        entries = {}
        patronymic_var = tk.StringVar(value=auto_patronymic)
        name_var = tk.StringVar()
        surname_var = tk.StringVar(value=person.surname)  # Автозаполнение фамилии
        birth_date_var = tk.StringVar()
        death_date_var = tk.StringVar()
        deceased_var = tk.BooleanVar(value=False)
        photo_path_var = tk.StringVar()

        fields = [
            ("Имя:", name_var),
            ("Фамилия:", surname_var),
            ("Отчество:", patronymic_var),
            ("Дата рождения (ДД.ММ.ГГГГ):", birth_date_var),
            ("Дата смерти (ДД.ММ.ГГГГ):", death_date_var),
        ]

        for i, (label_text, var) in enumerate(fields):
            row = i
            ttk.Label(frame, text=label_text).grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            if label_text in ["Дата рождения (ДД.ММ.ГГГГ):", "Дата смерти (ДД.ММ.ГГГГ):"]:
                entry = ttk.Entry(frame, textvariable=var)
                entry.grid(row=row, column=1, sticky=tk.EW, padx=(0, 0), pady=2)
                entry.bind("<KeyPress>", self._date_entry_keypress)
                entry.bind("<<Paste>>", lambda e, ent=entry: self._date_entry_on_paste(ent))
                entry.bind("<FocusOut>", self.normalize_date_on_focusout)
                entries[label_text] = entry
            else:
                entry = ttk.Entry(frame, textvariable=var)
                entry.grid(row=row, column=1, sticky=tk.EW, padx=(0, 0), pady=2)
                entries[label_text] = entry
                self._enable_copy_paste(entry)

        # Пол (только для отображения)
        ttk.Label(frame, text="Пол:").grid(row=len(fields), column=0, sticky=tk.W, padx=(0, 5), pady=2)
        ttk.Label(frame, text=sibling_gender, font=("Arial", 9, "bold")).grid(row=len(fields), column=1, sticky=tk.W,
                                                                              pady=2)

        # Чекбокс "Умер"
        chk_deceased = ttk.Checkbutton(frame, text="Умер", variable=deceased_var,
                                       command=lambda: entries["Дата смерти (ДД.ММ.ГГГГ):"].config(
                                           state='normal' if deceased_var.get() else 'disabled'))
        chk_deceased.grid(row=len(fields) + 1, column=0, columnspan=2, sticky=tk.W, padx=(0, 5), pady=2)
        entries["Дата с����������������ерти (ДД.ММ.ГГГГ):"].config(state='disabled')

        # Кнопка выбора фото
        ttk.Button(frame, text="Выбрать фото", command=lambda: self.browse_photo(photo_path_var)).grid(
            row=len(fields) + 2, column=0, columnspan=2, sticky=tk.W, padx=(0, 5), pady=5)

        # Подсказка об автозаполнении отчества
        used_father_id = father_id if father_id else 'N/A'
        ttk.Label(frame, text=f"Автоопределено от отца (ID: {used_father_id}):",
                  font=("Arial", 8, "italic"), foreground="#7f8c8d").grid(row=len(fields) + 3, column=0, columnspan=2, padx=10,
                                                                          pady=(0, 2), sticky='w')

        # --- Функция сохранения ---
        def submit():
            name = entries["Имя:"].get().strip()
            surname = entries["Фамилия:"].get().strip()
            patronymic = patronymic_var.get().strip()
            birth_date = entries["Дата рождения (ДД.ММ.ГГГГ):"].get().strip()
            death_date = entries["Дата смерти (ДД.ММ.ГГГГ):"].get().strip() if deceased_var.get() else ""
            is_deceased = deceased_var.get()
            gender = sibling_gender
            photo_path = photo_path_var.get().strip()

            if not name or not surname:
                messagebox.showerror("Ошибка", "Имя и фамилия обязательны для заполнения.")
                return

            # === Добавляем персону ===
            sibling_id, error = self.model.add_person(
                name=name,
                surname=surname,
                patronymic=patronymic,
                birth_date=birth_date,
                death_date=death_date if is_deceased else "",
                is_deceased=is_deceased,
                gender=gender,
                photo_path=photo_path
            )
            if error:
                messagebox.showerror("Ошибка", error)
                return

            # === Устанавливаем связи с родителями текущей персоны ===
            for parent_id in person.parents:
                sibling_obj = self.model.get_person(sibling_id)
                parent_obj = self.model.get_person(parent_id)
                if sibling_obj and parent_obj:
                    # Убеждаемся, что связи двусторонние
                    sibling_obj.parents.add(parent_id)
                    parent_obj.children.add(sibling_id)
                    # Также добавляем нового ребёнка к другому родителю, если он есть
                    other_parents = [p_id for p_id in person.parents if p_id != parent_id]
                    for other_pid in other_parents:
                        other_parent_obj = self.model.get_person(other_pid)
                        if other_parent_obj:
                            other_parent_obj.children.add(sibling_id)
                            sibling_obj.parents.add(other_pid)

            # Помечаем модель как изменённую
            self.model.mark_modified()

            # === Сообщение об успехе ===
            messagebox.showinfo("Успех", f"{sibling_type.capitalize()} успешно добавлен(а)!")

            # === Критическое исправление 2: Явно сохраняем и восстанавливаем current_center ===
            # Сохраняем текущий центр до обновления
            original_center = self.model.current_center
            # Устанавливаем центр на персону, для которой добавляли родственника (person_id)
            # Это защитит от внутренних изменений в refresh_view, если current_center был None
            self.model.current_center = person_id

            # === Обновляем отображение ===
            dialog.destroy()
            # Явно вызываем refresh_view, которое теперь будет использовать person_id как центр
            self.refresh_view()
            # Восстанавливаем original_center после обновления, если это необходимо
            # (например, если в другом месте программы планировалось сменить центр независимо)
            # self.model.current_center = original_center # Обычно не требуется, если логика центра строго следует person_id

            # Оставляем центр на той персоне, для которой добавляли родственника
            # self.model.current_center = person_id # Уже установлен выше, можно оставить или убрать

        # Кнопки уже созданы выше (сразу после создания btn_frame)
        # Принудительно обновляем геометрию
        dialog.update_idletasks()

        # Фокус на поле имени
        try:
            entries["Имя:"].focus_set()
        except KeyError:
            pass  # Если поле "Имя:" не найдено, просто продолжить
        dialog.transient(self.root)
        dialog.grab_set()


    def add_spouse_dialog(self, person_id):
        # Если person_id не передан, спрашиваем
        if not person_id:
            all_persons = self.model.get_all_persons()
            if not all_persons:
                messagebox.showerror("Ошибка", "Нет персон для выбора.")
                return
            options = [p.display_name() for p in all_persons.values()]
            selected_name = simpledialog.askstring("Выбор персоны", "Введите имя персоны (или часть):", initialvalue="")
            if not selected_name:
                return
            found_persons = [pid for pid, p in all_persons.items() if selected_name.lower() in p.display_name().lower()]
            if not found_persons:
                messagebox.showerror("Ошибка", "Персона не найдена.")
                return
            if len(found_persons) > 1:
                selected_pid = self.select_person_from_list(found_persons, "Выберите персону:")
                if not selected_pid:
                    return
                person_id = selected_pid
            else:
                person_id = found_persons[0]
        target_person = self.model.get_person(person_id)
        if not target_person:
            messagebox.showerror("Ошибка", "Персона не найдена")
            return
        opposite_gender = constants.GENDER_FEMALE if target_person.gender == constants.GENDER_MALE else constants.GENDER_MALE
        # Кандидаты: противоположный пол, не эта персона, не уже супруг(и) этой персоны (разрешаем второй/третий брак)
        current_spouse_ids = set(target_person.spouse_ids or [])
        all_persons = self.model.get_all_persons()
        available_spouses = []
        for p in all_persons.values():
            if p.gender == opposite_gender and p.id != person_id and p.id not in current_spouse_ids:
                available_spouses.append(p)
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Добавить супруга для {target_person.display_name()}")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        
        # Создаём контейнер для скроллируемой области
        scroll_container = ttk.Frame(dialog)
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_container, bg=constants.WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Выбор режима: существующий или новый
        mode_var = tk.StringVar(value="Select" if available_spouses else "Create")
        ttk.Radiobutton(scrollable_frame, text="Выбрать из существующих", variable=mode_var, value="Select",
                        command=lambda: [existing_frame.lift(), new_frame.lower()]).grid(row=0, column=0, columnspan=2,
                                                                                         sticky='w', padx=10, pady=5)
        ttk.Radiobutton(scrollable_frame, text="Создать нового", variable=mode_var, value="Create",
                        command=lambda: [new_frame.lift(), existing_frame.lower()]).grid(row=1, column=0, columnspan=2,
                                                                                         sticky='w', padx=10, pady=5)
        # Фрейм для выбора существующего
        existing_frame = ttk.Frame(scrollable_frame)
        existing_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        if available_spouses:
            spouse_listbox = tk.Listbox(existing_frame)
            spouse_listbox.pack(fill=tk.BOTH, expand=True)
            for spouse in available_spouses:
                spouse_listbox.insert(tk.END, spouse.display_name())

            def select_existing_spouse():
                selection = spouse_listbox.curselection()
                if selection:
                    selected_idx = selection[0]
                    selected_spouse = available_spouses[selected_idx]
                    success, msg = self.model.add_marriage(person_id, selected_spouse.id)
                    if success:
                        messagebox.showinfo("Успех", msg)
                    else:
                        messagebox.showerror("Ошибка", msg)
                    dialog.destroy()
                    self.refresh_view()
                else:
                    messagebox.showwarning("Предупреждение", "Выберите супруга из списка.")

            ttk.Button(existing_frame, text="Выбрать", command=select_existing_spouse).pack(pady=5)
        else:
            ttk.Label(existing_frame, text="Нет подходящих персон.").pack()
        # Фрейм для создания нового (из add_person_dialog)
        new_frame = ttk.Frame(scrollable_frame)
        new_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        new_frame.lower()  # Скрыть по умолчанию
        # Конфигурация формы для нового супруга
        fields_config_new = [
            ("Имя:", "Entry", "", {}),
            ("Фамилия:", "Entry", "", {}),
            ("Отчество:", "Entry", "", {}),
            ("Дата рождения (ДД.ММ.ГГГГ):", "Entry", "", {}),
            ("Дата смерти (ДД.ММ.ГГГГ):", "Entry", "", {}),
        ]
        new_entries, _, new_row = create_form_fields(new_frame, fields_config_new)
        for key in ("Имя:", "Фамилия:", "Отчество:"):
            if key in new_entries:
                self._enable_copy_paste(new_entries[key])
        # Привязываем ввод дат (только цифры + автоточки)
        for key in ["Дата рождения (ДД.ММ.ГГГГ):", "Дата смерти (ДД.ММ.ГГГГ):"]:
            new_entries[key].bind("<KeyPress>", self._date_entry_keypress)
            new_entries[key].bind("<<Paste>>", lambda e, k=key: self._date_entry_on_paste(new_entries[k]))
            new_entries[key].bind("<FocusOut>", self.normalize_date_on_focusout)

        # Пол (автоматически определяется)
        new_gender_var = tk.StringVar(value=opposite_gender)  # Автозаполнение пола
        new_gender_label = ttk.Label(new_frame, text="Пол:")
        new_gender_label.grid(row=new_row, column=0, padx=10, pady=8, sticky='e')
        ttk.Radiobutton(new_frame, text=opposite_gender, variable=new_gender_var, value=opposite_gender).grid(
            row=new_row, column=1, sticky='w')
        new_row += 1
        new_is_deceased_var = tk.BooleanVar()
        ttk.Checkbutton(new_frame, text="Умер", variable=new_is_deceased_var).grid(row=new_row, column=0, columnspan=2,
                                                                                   padx=10, pady=8, sticky='w')
        new_row += 1

        def create_new_spouse_and_marriage():
            name = new_entries["Имя:"].get().strip()
            surname = new_entries["Фамилия:"].get().strip()
            patronymic = new_entries["Отчество:"].get().strip()
            birth_date = new_entries["Дата рождения (ДД.ММ.ГГГГ):"].get().strip()
            death_date = new_entries["Дата смерти (ДД.ММ.��ГГГ):"].get().strip()
            gender = new_gender_var.get()
            is_deceased = new_is_deceased_var.get()
            if not name or not surname:
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_NAME_SURNAME_REQUIRED)
                return
            # УДАЛЯЕМ проверку на обязательность birth_date
            # if not birth_date:
            #     messagebox.showerror("Ошибка", "Поле 'Дата рождения' обязательно для заполнения")
            #     new_entries["Дата рождения (ДД.ММ.ГГГГ):"].focus_set()
            #     return
            if not self.model._validate_date(birth_date):
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_BIRTH_DATE_INVALID)
                new_entries["Дата рождения (ДД.ММ.ГГГГ):"].focus_set()
                return
            if is_deceased and death_date and not self.model._validate_date(death_date):
                messagebox.showerror("Ошибка", constants.VALIDATION_MSG_DEATH_DATE_INVALID)
                new_entries["Дата смерт�� (ДД.ММ.ГГГГ):"].focus_set()
                return
            # УДАЛЯЕМ проверку ��а обязательность death_date если is_deceased
            # if is_deceased and not death_date:
            #     messagebox.showerror("Ошибка", constants.VALIDATION_MSG_DEATH_DATE_NEEDED)
            #     return
            new_spouse_id, error = self.model.add_person(name, surname, patronymic, birth_date, gender, "", is_deceased,
                                                         death_date, "")
            if error:
                messagebox.showerror("Ошибка", error)
                return
            success, msg = self.model.add_marriage(person_id, new_spouse_id)
            if success:
                messagebox.showinfo("Успех", msg)
            else:
                # Если брак не удался, удаляем созданного супруга
                self.model.delete_person(new_spouse_id)
                messagebox.showerror("Ошибка", msg)
                return
            dialog.destroy()
            self.refresh_view()

        # ИСПРАВЛЕНО: используем grid() вместо pack() для кнопки (устранение конфликта геометрии)
        ttk.Button(new_frame, text="Создать и добавить в брак", command=create_new_spouse_and_marriage).grid(
            row=new_row, column=0, columnspan=2, pady=10)

        # Кнопки OK/Cancel
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def on_ok():
            if mode_var.get() == "Select":
                selection = spouse_listbox.curselection()
                if selection:
                    selected_idx = selection[0]
                    selected_spouse = available_spouses[selected_idx]
                    success, msg = self.model.add_marriage(person_id, selected_spouse.id)
                    if success:
                        messagebox.showinfo("Успех", msg)
                    else:
                        messagebox.showerror("Ошибка", msg)
                    dialog.destroy()
                    self.refresh_view()
                else:
                    messagebox.showwarning("Предупреждение", "Выберите супруга из списка.")
            elif mode_var.get() == "Create":
                create_new_spouse_and_marriage()

        ttk.Button(button_frame, text="Сохранить", command=on_ok).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(button_frame, text="��тм��на", command=dialog.destroy).pack(side=tk.LEFT, padx=10, pady=10)

    def remove_marriage_from_edit(self, pid, dialog_window):
        """Удаляет один из браков персоны. При нескольких супругах — выбор, какой брак удалить."""
        spouse_ids = self.model.get_spouses(pid)
        if not spouse_ids:
            messagebox.showinfo("Информация", "У данной персоны нет зарегистрированных супругов.")
            return
        person = self.model.get_person(pid)
        if not person:
            return
        if len(spouse_ids) == 1:
            spouse_id = spouse_ids[0]
        spouse = self.model.get_person(spouse_id)
        if not spouse:
            messagebox.showerror("Ошибка", "Супруг не найден в базе данных.")
            return
        if messagebox.askyesno("Подтверждение",
                                   f"Удалить брак между '{person.display_name()}' и '{spouse.display_name()}'?"):
            success, msg = self.model.remove_marriage(pid, spouse_id)
            if success:
                messagebox.showinfo("Успех", msg)
                dialog_window.destroy()
                self.refresh_view()
            else:
                messagebox.showerror("Ошибка", msg)
            return
        # Несколько супругов: диалог выбора
        choice = tk.Toplevel(self.root)
        choice.title("Удалить брак")
        choice.transient(dialog_window)
        choice.grab_set()
        ttk.Label(choice, text="Выберите брак для удаления:", font=("Arial", 10, "bold")).pack(pady=10, padx=10)
        for spouse_id in spouse_ids:
            spouse = self.model.get_person(spouse_id)
            if not spouse:
                continue
            btn = ttk.Button(
                choice,
                text=f"Удалить брак с {spouse.display_name()}",
                command=lambda sid=spouse_id: self._do_remove_one_marriage(pid, sid, choice, dialog_window)
            )
            btn.pack(pady=2, padx=10, fill=tk.X)
        ttk.Button(choice, text="Отмена", command=choice.destroy).pack(pady=10)

    def _do_remove_one_marriage(self, pid, spouse_id, choice_window, edit_dialog_window):
        """Удаляет один брак и закрывает окно выбора."""
        success, msg = self.model.remove_marriage(pid, spouse_id)
        choice_window.destroy()
        if success:
            messagebox.showinfo("Успех", msg)
            edit_dialog_window.destroy()
            self.refresh_view()
        else:
            messagebox.showerror("Ошибка", msg)


    def select_person_from_list(self, pid_list, title):
        if not pid_list:
            return None
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x300")
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        persons = self.model.get_all_persons()
        for pid in pid_list:
            if pid in persons:
                listbox.insert(tk.END, persons[pid].display_name())
        selected_pid = None

        def on_select():
            nonlocal selected_pid
            selection = listbox.curselection()
            if selection:
                selected_pid = pid_list[selection[0]]  # Получаем оригинальный PID из списка
            dialog.destroy()

        ttk.Button(dialog, text="Выбрать", command=on_select).pack(pady=5)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return selected_pid

    # --- МЕТОДЫ ФАЙЛОВОЙ СИСТЕМЫ ---
    def new_file(self):
        if messagebox.askyesno("Подтверждение",
                               "Создать новое семейное древо? Все несохранённые изменения будут потеряны."):
            self.model = FamilyTreeModel()
            self.model.current_center = None
            self.center_label.config(text="Центр: Не выбран")
            self.last_selected_person_id = None
            self.refresh_view()

    def save_file(self):
        success = self.model.save_to_file()
        if success:
            self.statusbar.config(text=constants.MSG_STATUS_DATA_SAVED)
        else:
            self.statusbar.config(text=constants.MSG_STATUS_ERROR_GENERIC)

    # --- Экспорт/Импорт CSV: таблица колонок соответствует модели Person и связям ---
    CSV_FIELDS = [
        'id', 'name', 'surname', 'patronymic', 'birth_date', 'birth_place', 'gender',
        'is_deceased', 'death_date', 'maiden_name', 'photo_path',
        'parents', 'children', 'spouse_ids',
        'biography', 'burial_place', 'burial_date',
        'photo_album', 'link_titles', 'link_urls',
        'occupation', 'education', 'address', 'notes', 'collapsed_branches'
    ]

    def export_to_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return False
        try:
            import csv
            persons = self.model.get_all_persons()
            if not persons:
                messagebox.showwarning("Предупреждение", "Нет персон для экспорта!")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.CSV_FIELDS, delimiter=';')
                writer.writeheader()
                
                count = 0
                for pid, person in persons.items():
                    links = getattr(person, 'links', None) or []
                    titles = '|'.join((x.get('title') or '') for x in links)
                    urls = '|'.join((x.get('url') or '') for x in links)
                    writer.writerow({
                        'id': pid,
                        'name': person.name,
                        'surname': person.surname,
                        'patronymic': getattr(person, 'patronymic', '') or '',
                        'birth_date': person.birth_date,
                        'birth_place': getattr(person, 'birth_place', '') or '',
                        'gender': person.gender,
                        'is_deceased': person.is_deceased,
                        'death_date': person.death_date,
                        'maiden_name': person.maiden_name,
                        'photo_path': person.photo_path,
                        'biography': getattr(person, 'biography', '') or '',
                        'burial_place': getattr(person, 'burial_place', '') or '',
                        'burial_date': getattr(person, 'burial_date', '') or '',
                        'occupation': getattr(person, 'occupation', '') or '',
                        'education': getattr(person, 'education', '') or '',
                        'address': getattr(person, 'address', '') or '',
                        'notes': getattr(person, 'notes', '') or '',
                        'links_titles': titles,
                        'links_urls': urls,
                        'parents': '|'.join(str(p) for p in person.parents),
                        'children': '|'.join(str(c) for c in person.children),
                        'spouse_ids': '|'.join(str(s) for s in person.spouse_ids),
                    })
                    count += 1
            
            self.model.logger.info(f"Экспорт в CSV: {filename} ({count} персон)")
            messagebox.showinfo("Успех", f"Экспортировано {count} персон в {filename}")
            return True
        except Exception as e:
            self.model.logger.error(f"Ошибка экспорта в CSV: {e}")
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
            return False

    # Продолжение метода export_to_csv
    CSV_FIELDS = [
        'id', 'name', 'surname', 'patronymic', 'birth_date', 'birth_place',
        'gender', 'is_deceased', 'death_date', 'maiden_name', 'photo_path',
        'biography', 'burial_place', 'burial_date', 'occupation', 'education',
        'address', 'notes', 'links_titles', 'links_urls',
        'parents', 'children', 'spouse_ids'  # Связи
    ]

    def import_from_csv(self, filename=None):
        if not filename:
            filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return False
        try:
            import csv
            new_persons = {}
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    pid = row.get('id', '').strip()
                    if not pid:
                        continue

                    # Читаем связи из CSV
                    parents_str = row.get('parents', '').strip()
                    children_str = row.get('children', '').strip()
                    spouse_ids_str = row.get('spouse_ids', '').strip()

                    is_deceased = (row.get('is_deceased') or '').strip() in ('True', '1', 'true', 'yes', 'Да', 'да')

                    p = Person(
                        name=row.get('name', '').strip(),
                        surname=row.get('surname', '').strip(),
                        patronymic=row.get('patronymic', '').strip(),
                        birth_date=row.get('birth_date', '').strip(),
                        gender=row.get('gender', '').strip() or constants.GENDER_MALE,
                        is_deceased=is_deceased,
                        death_date=row.get('death_date', '').strip(),
                        maiden_name=row.get('maiden_name', '').strip(),
                        birth_place=row.get('birth_place', '').strip(),
                        biography=row.get('biography', '').strip(),
                        burial_place=row.get('burial_place', '').strip(),
                        burial_date=row.get('burial_date', '').strip(),
                        occupation=row.get('occupation', '').strip(),
                        education=row.get('education', '').strip(),
                        address=row.get('address', '').strip(),
                        notes=row.get('notes', '').strip(),
                        photo_path=row.get('photo_path', '').strip(),
                    )
                    p.id = pid
                    # Восстанавливаем связи
                    p.parents = set(pid.strip() for pid in parents_str.split('|') if pid.strip())
                    p.children = set(pid.strip() for pid in children_str.split('|') if pid.strip())
                    p.spouse_ids = set(pid.strip() for pid in spouse_ids_str.split('|') if pid.strip())
                    p.collapsed_branches = False
                    new_persons[pid] = p

            # Проверяем совпадения ID
            common_ids = set(new_persons.keys()) & set(self.model.get_all_persons().keys())
            if common_ids:
                overwrite = messagebox.askyesno("Предупреждение",
                                                f"Найдены персоны с совпадающими ID: {list(common_ids)[:10]}{'...' if len(common_ids) > 10 else ''}. Перезаписать?")
                if not overwrite:
                    for cid in common_ids:
                        new_persons.pop(cid, None)

            imported_count = len(new_persons)
            self.model.persons.update(new_persons)
            self.model.mark_modified()

            # Восстанавливаем связи в модели (брак и spouse_ids)
            for pid, person in new_persons.items():
                # Обновляем spouse_ids у супругов
                for spouse_id in person.spouse_ids:
                    if spouse_id in self.model.persons:
                        self.model.persons[spouse_id].spouse_ids.add(pid)
                # Добавляем браки в модель
                for spouse_id in person.spouse_ids:
                    if spouse_id in self.model.persons:
                        self.model.add_marriage(pid, spouse_id)

            # Устанавливаем current_center на первую персону если не установлен
            if not self.model.current_center and new_persons:
                first_pid = list(new_persons.keys())[0]
                self.model.current_center = first_pid

            self.model.logger.info(f"Данные импортированы из CSV: {filename} ({imported_count} персон)")
            messagebox.showinfo("Успех", f"Импортировано {imported_count} персон из {filename}\n\nВсе связи (родители, дети, супруги) восстановлены!")
            
            # Сбрасываем координаты чтобы пересчитать layout для всех персон
            self.coords.clear()
            self.units.clear()
            self.level_structure.clear()
            
            self.refresh_view()
            return True
        except Exception as e:
            self.model.logger.error(f"Ошибка импорта из CSV {filename}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка импорта: {e}")
            return False

    # --- МЕТОДЫ ОТМЕНЫ/ПОВТОРА И ��ЕМ ---
    def undo(self):
        """Отмена последней операции."""
        if not UNDO_AVAILABLE or not self.undo_manager:
            messagebox.showinfo("Отмена", "Функция отмены действий недоступна.")
            return

        if self.undo_manager.undo():
            self.refresh_view()
            self.update_title()
            action_name = self.undo_manager.get_last_action_name()
            if hasattr(self, 'statusbar'):
                self.statusbar.config(text=f"Отменено: {action_name}")
        else:
            messagebox.showinfo("��тмена", "Нечего отменять.")

    def redo(self):
        """Повтор отменённой операции."""
        if not UNDO_AVAILABLE or not self.undo_manager:
            messagebox.showinfo("Повтор", "Функция повтора действий недоступна.")
            return

        if self.undo_manager.redo():
            self.refresh_view()
            self.update_title()
            action_name = self.undo_manager.get_last_action_name()
            if hasattr(self, 'statusbar'):
                self.statusbar.config(text=f"Повторено: {action_name}")
        else:
            messagebox.showinfo("Повтор", "Нечего повторять.")

    def toggle_theme_menu(self):
        """Переключает тему оформления."""
        if not THEME_AVAILABLE:
            messagebox.showinfo("Темы", "Модуль управления темами недоступен.")
            return

        new_theme = toggle_theme(self)
        theme_name = get_theme_name(new_theme)
        self._save_window_settings()
        messagebox.showinfo("Тема", f"Применена {theme_name.lower()} тема")
        self.refresh_view()

    def open_timeline(self):
        """Открывает окно временной шкалы жизней персон."""
        try:
            from timeline import open_timeline as open_timeline_window
            open_timeline_window(self, self.model)
        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модуль временной шкалы: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при открытии временной шкалы: {e}")

    def open_backup_dialog(self):
        """Диалог управления резервными копиями."""
        if not BACKUP_AVAILABLE:
            messagebox.showinfo("Резервные копии", "Модуль резервного копирования недоступен.")
            return
        
        try:
            from backup import BackupDialog
            BackupDialog(self.root, self)
        except ImportError:
            messagebox.showerror("Ошибка", "Диалог резервного копирования недоступен")

    def _save_window_settings(self):
        """Сохраняет настройки окна."""
        settings = {
            "width": self.root.winfo_width(),
            "height": self.root.winfo_height(),
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y()
        }
        try:
            with open("window_settings.json", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Ошибка сохранения настроек окна: {e}")

    def update_title(self):
        """Обновляет заголовок окна с индикатором изменений."""
        title = self.base_title
        if self.model and self.model.modified:
            title += self.modified_indicator
        self.root.title(title)

    # --- МЕТОДЫ ПОИСКА И ФИЛЬТРАЦИИ ---
    def open_search_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Поиск")
        dialog.geometry("400x100")
        ttk.Label(dialog, text="Поиск:").pack(pady=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(dialog, textvariable=search_var)
        search_entry.pack(pady=5, padx=10, fill=tk.X)
        search_entry.focus()

        def on_search(*args):  # *args для работы с bind
            self.perform_search(search_var.get())

        search_var.trace_add("write", on_search)  # Автопоиск при вводе
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Пред.", command=self.previous_search_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="След.", command=self.next_search_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Закрыть", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def perform_search(self, query):
        query = query.strip().lower()
        if not query:
            self.search_results = []
            self.search_index = -1
            return
        all_persons = self.model.get_all_persons()
        # - РАСШИРЕННЫЙ ПОИСК -
        self.search_results = []
        for pid, person in all_persons.items():
            # Ищем в имени, фамилии, отчестве, дате рож��ения, дате смерти
            searchable_text = f"{person.name} {person.surname} {person.patronymic} {person.birth_date} {person.death_date}".lower()
            if query in searchable_text:
                self.search_results.append(pid)
        # - /РАСШИРЕННЫЙ ПОИСК -
        self.search_index = 0 if self.search_results else -1
        if self.search_results:
            self.highlight_search_result()
        else:
            self.statusbar.config(text="Поиск: ничего не найдено")

    def highlight_search_result(self):
        if 0 <= self.search_index < len(self.search_results):
            pid = self.search_results[self.search_index]
            # Прокрутка к карточке (простая реализация)
            if pid in self.coords:
                target_x, target_y = self.coords[pid]
                # Центрируем Canvas на координатах персоны
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                self.offset_x = (canvas_width / 2) - (target_x * self.current_scale)
                self.offset_y = (canvas_height / 2) - (target_y * self.current_scale)
                self.refresh_view()
                self.statusbar.config(text=f"Поиск: найдено {self.search_index + 1} из {len(self.search_results)}")
        else:
            self.statusbar.config(text="Поиск: нет результатов")

    def next_search_result(self):
        if self.search_results:
            self.search_index = (self.search_index + 1) % len(self.search_results)
            self.highlight_search_result()

    def previous_search_result(self):
        if self.search_results:
            self.search_index = (self.search_index - 1) % len(self.search_results)
            self.highlight_search_result()

    def open_filter_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Фильтры")
        dialog.geometry("300x300")
        # - ПОЛЕ ДЛЯ ФИЛЬТРАЦИИ ПО ПОЛУ -
        gender_var = tk.StringVar(value=self.active_filters.get('gender', constants.FILTER_ALL))
        ttk.Label(dialog, text="Пол:").pack(anchor='w', padx=10, pady=5)
        gender_combo = ttk.Combobox(dialog, textvariable=gender_var,
                                    values=[constants.FILTER_ALL, constants.FILTER_MALE_ONLY, constants.FILTER_FEMALE_ONLY], state="readonly")
        gender_combo.pack(fill=tk.X, padx=10, pady=5)
        gender_combo.set(self.active_filters.get('gender', constants.FILTER_ALL))
        # - /ПОЛЕ ДЛЯ ФИЛЬТРАЦИИ ПО ПОЛУ -
        # - ПОЛЕ ДЛЯ ФИЛЬТРАЦИИ ПО СТАТУСУ -
        status_var = tk.StringVar(value=self.active_filters.get('status', constants.FILTER_ALL))
        ttk.Label(dialog, text="Статус:").pack(anchor='w', padx=10, pady=5)
        status_combo = ttk.Combobox(dialog, textvariable=status_var,
                                    values=[constants.FILTER_ALL, constants.FILTER_ALIVE_ONLY], state="readonly")
        status_combo.pack(fill=tk.X, padx=10, pady=5)
        status_combo.set(self.active_filters.get('status', constants.FILTER_ALL))
        # - /ПОЛЕ ДЛЯ ФИЛЬТРАЦИИ ПО СТАТУСУ -
        # - ЧЕКБОКС ДЛЯ ФИЛЬТРАЦИИ ПО НАЛИЧИЮ ФОТО -
        photos_var = tk.BooleanVar(value=self.active_filters.get('photos_only', False))
        ttk.Checkbutton(dialog, text="Только с фото", variable=photos_var).pack(anchor='w', padx=10, pady=5)
        # - /ЧЕКБОКС ДЛЯ ФИЛЬТРАЦИИ ПО НАЛИЧИЮ ФОТО -
        # - ЧЕКБОКС ДЛЯ ФИЛЬТРАЦИИ ПО ОТСУТСТВИЮ ДЕТЕЙ -
        childless_var = tk.BooleanVar(value=self.active_filters.get('childless', False))
        ttk.Checkbutton(dialog, text="Только бездетные", variable=childless_var).pack(anchor='w', padx=10, pady=5)

        # - /ЧЕКБОКС ДЛЯ ФИЛЬТРАЦИИ ПО ОТСТУТСТВИЮ ДЕТЕЙ -

        def apply_filters():
            self.active_filters['gender'] = gender_var.get()
            self.active_filters['status'] = status_var.get()
            self.active_filters['photos_only'] = photos_var.get()
            self.active_filters['childless'] = childless_var.get()
            self.refresh_view()
            dialog.destroy()

        def reset_filters():
            gender_var.set(constants.FILTER_ALL)
            status_var.set(constants.FILTER_ALL)
            photos_var.set(False)
            childless_var.set(False)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10, fill=tk.X, padx=10)
        ttk.Button(btn_frame, text="Сбросить", command=reset_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Применить", command=apply_filters).pack(side=tk.RIGHT, padx=5)

    def toggle_theme(self, dark=True):
        """Переключает тему оформления (тёмная/светлая)."""
        if dark:
            constants.apply_dark_theme()
        else:
            constants.apply_palette(constants.PALETTE_DEFAULTS)
        constants.save_palette_to_file()
        
        # Применяем цвета ко всему интерфейсу
        self.apply_ui_colors_from_palette()
        
        # Применяем стили для всех виджетов
        style = ttk.Style()
        text_color = get_contrast_text_color(constants.WINDOW_BG)
        button_text_color = get_contrast_text_color(constants.MENUBAR_BG)
        button_bg = constants.MENUBAR_BG
        entry_bg = '#ffffff' if text_color == '#000000' else '#334155'
        is_dark_theme = text_color == '#ffffff'

        style.theme_use('clam')
        style.configure('.', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TButton', background=button_bg, foreground=button_text_color, font=('Arial', 10, 'bold'))
        style.configure('TEntry', fieldbackground=entry_bg, foreground=text_color)
        style.configure('TCombobox', fieldbackground=entry_bg, foreground=text_color)
        style.configure('TLabel', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TFrame', background=constants.WINDOW_BG)
        style.configure('TCheckbutton', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TRadiobutton', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('Treeview', background=entry_bg, foreground=text_color, fieldbackground=entry_bg)
        style.configure('Treeview.Heading', background=button_bg, foreground=button_text_color)
        style.configure('TNotebook', background=constants.WINDOW_BG)
        style.configure('TNotebook.Tab', background=button_bg, foreground=button_text_color)
        style.map('TButton', background=[('active', '#475569' if is_dark_theme else '#e0e0e0')])
        style.map('TNotebook.Tab', background=[('selected', '#475569' if is_dark_theme else constants.MENUBAR_BG)])
        # Кнопки "Сохранить" (Accent/Success) - всегда с белым текстом на цветном фоне
        style.configure('Accent.TButton', background='#e74c3c', foreground='#ffffff', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#27ae60', foreground='#ffffff', font=('Arial', 10, 'bold'))
        
        # Обновляем меню
        self.menu_bar.configure(bg=constants.MENUBAR_BG, fg=text_color)
        self.file_menu.configure(bg=constants.MENUBAR_BG, fg=text_color, activebackground=constants.WINDOW_BG, activeforeground=text_color)
        self.view_menu.configure(bg=constants.MENUBAR_BG, fg=text_color, activebackground=constants.WINDOW_BG, activeforeground=text_color)
        self.edit_menu.configure(bg=constants.MENUBAR_BG, fg=text_color, activebackground=constants.WINDOW_BG, activeforeground=text_color)
        self.help_menu.configure(bg=constants.MENUBAR_BG, fg=text_color, activebackground=constants.WINDOW_BG, activeforeground=text_color)
        
        self.refresh_view()
        theme_name = "Тёмная" if dark else "Светлая"
        messagebox.showinfo("Тема оформления", f"{theme_name} тема применена!")

    def apply_ui_colors_from_palette(self):
        """Применяет цвета из сохранённой палитры к эле��������ентам интерфейса."""
        print(f"[APPLY_UI_COLORS] MARRIAGE_LINE_COLOR = {constants.MARRIAGE_LINE_COLOR}")
        print(f"[APPLY_UI_COLORS] PARENT_LINE_COLOR = {constants.PARENT_LINE_COLOR}")
        print(f"[APPLY_UI_COLORS] CANVAS_BG = {constants.CANVAS_BG}")
        style = ttk.Style()
        self.root.configure(bg=constants.WINDOW_BG)
        
        # Определяем контрастный цвет текста автоматически
        text_color = get_contrast_text_color(constants.WINDOW_BG)
        button_text_color = get_contrast_text_color(constants.MENUBAR_BG)
        button_bg = constants.MENUBAR_BG
        entry_bg = '#ffffff' if text_color == '#000000' else '#334155'
        is_dark_theme = text_color == '#ffffff'
        
        try:
            self.menu_bar.configure(bg=constants.MENUBAR_BG)
            self.file_menu.configure(bg=constants.MENUBAR_BG)
            self.view_menu.configure(bg=constants.MENUBAR_BG)
            self.edit_menu.configure(bg=constants.MENUBAR_BG)
            self.help_menu.configure(bg=constants.MENUBAR_BG)
            # Сервисное меню (если есть)
            if hasattr(self, 'service_menu'):
                self.service_menu.configure(bg=constants.MENUBAR_BG)
        except Exception:
            pass
        self.canvas.config(bg=constants.CANVAS_BG)
        
        # Глобальные стили для ВСЕГО приложения
        style.configure('.', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TFrame', background=constants.WINDOW_BG)
        style.configure('TLabel', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TButton', background=button_bg, foreground=button_text_color, font=('Arial', 10, 'bold'))
        style.map('TButton',
                 background=[('active', '#4a5568' if is_dark_theme else button_bg),
                           ('pressed', '#1a202c' if is_dark_theme else button_bg)])
        style.configure('TEntry', fieldbackground=entry_bg, foreground=text_color, insertcolor=text_color)
        style.configure('TCombobox', fieldbackground=entry_bg, foreground=text_color)
        style.configure('TMenubutton', background=constants.MENUBAR_BG, foreground=text_color)
        style.configure('TCheckbutton', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TRadiobutton', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('TSeparator', background='#718096' if is_dark_theme else '#cbd5e1')
        style.configure('TText', background=constants.WINDOW_BG, foreground=text_color)
        style.configure('Treeview', background=entry_bg, foreground=text_color, fieldbackground=entry_bg)
        style.configure('Treeview.Heading', background=button_bg, foreground=button_text_color)
        style.configure('TNotebook', background=constants.WINDOW_BG)
        style.configure('TNotebook.Tab', background=button_bg, foreground=button_text_color)
        style.map('TNotebook.Tab',
                 background=[('selected', '#4a5568' if is_dark_theme else constants.MENUBAR_BG)])
        # Кнопки "Сохранить" (Accent/Success) - всегда с белым текстом на цветном фоне
        style.configure('Accent.TButton', background='#e74c3c', foreground='#ffffff', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#27ae60', foreground='#ffffff', font=('Arial', 10, 'bold'))
        
        # Применяем цвета к статусбару и center_label
        if hasattr(self, 'statusbar'):
            self.statusbar.configure(bg=constants.WINDOW_BG, fg=text_color)
        if hasattr(self, 'center_label'):
            self.center_label.configure(bg=constants.MENUBAR_BG, fg=text_color)
        if hasattr(self, 'counter_label'):
            self.counter_label.configure(bg=constants.MENUBAR_BG, fg=text_color)

    def open_color_palette_dialog(self):
        """Диалог выбора цветов интерфейса: иконки персон, линии, фон холста и т.д."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Цвет интерфейса")
        dialog.geometry("520x520")
        dialog.transient(self.root)
        dialog.grab_set()

        # Загружаем ТЕКУЩИЕ значения из constants (а не из PALETTE_DEFAULTS)
        current = {k: getattr(constants, k, constants.PALETTE_DEFAULTS[k]) for k in constants.PALETTE_DEFAULTS}
        print(f"[PALETTE_DIALOG] Загружены цвета: MARRIAGE_LINE_COLOR={current.get('MARRIAGE_LINE_COLOR')}")
        swatches = {}

        main_f = ttk.Frame(dialog, padding=10)
        main_f.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(main_f, highlightthickness=0, bg=constants.WINDOW_BG)
        scrollbar = ttk.Scrollbar(main_f)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def pick_color(key):
            result = colorchooser.askcolor(initialcolor=current.get(key, "#000000"), title=constants.PALETTE_LABELS.get(key, key))
            if result and result[1]:
                current[key] = result[1]
                if key in swatches:
                    swatches[key].config(bg=current[key])

        for key in constants.PALETTE_DEFAULTS:
            row = ttk.Frame(inner)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=constants.PALETTE_LABELS.get(key, key), width=32).pack(side=tk.LEFT, padx=(0, 8))
            swatch = tk.Frame(row, width=44, height=24, bg=current[key], relief=tk.SOLID, bd=1)
            swatch.pack(side=tk.LEFT, padx=2)
            swatch.pack_propagate(False)
            swatches[key] = swatch
            ttk.Button(row, text="Выбрать", width=10, command=lambda k=key: pick_color(k)).pack(side=tk.LEFT, padx=4)

        def reset_defaults():
            for k in constants.PALETTE_DEFAULTS:
                current[k] = constants.PALETTE_DEFAULTS[k]
                if k in swatches:
                    swatches[k].config(bg=current[k])

        def apply_palette():
            constants.apply_palette(current)
            constants.save_palette_to_file()
            # Применяем цвета ко всему интерфейсу
            self.apply_ui_colors_from_palette()
            self.canvas.config(bg=constants.CANVAS_BG)
            self.refresh_view()
            dialog.destroy()

        btn_f = ttk.Frame(dialog, padding=10)
        btn_f.pack(fill=tk.X)
        ttk.Button(btn_f, text="По умолчанию", command=reset_defaults).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="Применить", command=apply_palette).pack(side=tk.RIGHT, padx=4)

    # --- ДИАЛОГИ О ПРОГРАММЕ И ОБНОВЛЕНИЯХ ---
    def _show_about_dialog(self):
        """Показать диалог 'О программе' с проверкой обновлений."""
        dialog = tk.Toplevel(self.root)
        dialog.title("О программе")
        dialog.geometry("450x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() - 450) // 2
        y = (self.root.winfo_screenheight() - 420) // 2
        dialog.geometry(f"+{x}+{y}")

        # Иконка
        tk.Label(dialog, text="🌳", font=("Segoe UI", 48)).pack(pady=10)

        # Те��ст
        about_text = (
            f"Семейное древо\n\n"
            f"Версия {self._get_app_version()}\n\n"
            "Пр��ложение для построения и редактирования\n"
            "семейного генеалогического дерева.\n\n"
            "© 2024-2026 Все права защищены."
        )
        tk.Label(dialog, text=about_text, font=("Segoe UI", 10),
                justify="center").pack(pady=5)

        # Статус обновления
        self.update_status_label = tk.Label(dialog, text="", font=("Segoe UI", 9),
                                           fg="#666666", wraplength=400)
        self.update_status_label.pack(pady=5)

        # Кнопки
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        def check_updates():
            self._check_for_updates(dialog)

        tk.Button(btn_frame, text="🔄 Проверить обновл��ния",
                 command=check_updates,
                 bg="#4CAF50", fg="white",
                 font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Закрыть",
                 command=dialog.destroy,
                 font=("Segoe UI", 10),
                 padx=20, pady=8).pack(side=tk.LEFT, padx=5)

    def _get_app_version(self):
        """Получает текущую версию приложения."""
        try:
            import version
            return version.__version__
        except:
            return "1.0.0"

    def _check_for_updates(self, dialog=None):
        """Проверяет наличие обновлений."""
        if dialog:
            self.update_status_label.config(text="⏳ Проверка обновлений...", fg="#FF9800")
            dialog.update()

        try:
            import urllib.request
            import json

            # GitHub Releases API
            api_url = "https://api.github.com/repos/Andrey1803/family-tree/releases/latest"

            req = urllib.request.Request(api_url, headers={'User-Agent': 'FamilyTree'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', 'v0.0.0').lstrip('v')
                release_notes = data.get('body', '')

            current_version = self._get_app_version()

            if self._compare_versions(latest_version, current_version) > 0:
                # Есть новая версия
                self._show_update_dialog(dialog, latest_version, release_notes)
            else:
                if dialog:
                    self.update_status_label.config(text="✅ Установлена актуальная версия", fg="#4CAF50")
                else:
                    messagebox.showinfo("Обновления", "Установлена актуальная версия!")

        except Exception as e:
            if dialog:
                self.update_status_label.config(text="❌ Ошибка п��оверки обновлений", fg="#F44336")
            print(f"Update check error: {e}")

    def _compare_versions(self, v1, v2):
        """Сравнивает версии: возвращает -1, 0, 1."""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        try:
            parts1 = normalize(v1)
            parts2 = normalize(v2)
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                if p1 < p2:
                    return -1
                if p1 > p2:
                    return 1
            return 0
        except:
            return 0

    def _show_update_dialog(self, parent_dialog, new_version, release_notes):
        """Показывает диалог обновления."""
        msg = (f"Доступна новая версия: {new_version}\n\n"
               f"Текущая версия: {self._get_app_version()}\n\n"
               f"Изменения:\n{release_notes[:500]}...\n\n"
               "Перейти на страницу загрузок?")
        if messagebox.askyesno("Доступно обновление", msg):
            import webbrowser
            webbrowser.open("https://github.com/Andrey1803/family-tree/releases")

    def _show_developer_dialog(self):
        """Показать диалог 'О разработчике'."""
        dialog = tk.Toplevel(self.root)
        dialog.title("О разработчике")
        dialog.geometry("500x450")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 450) // 2
        dialog.geometry(f"+{x}+{y}")

        # Заголовок с иконкой
        header_frame = tk.Frame(dialog, bg="#2563eb")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="👨‍💻", font=("Segoe UI Emoji", 56),
                bg="#2563eb").pack(pady=15)

        # Основной контент
        content_frame = tk.Frame(dialog, bg="#ffffff")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ФИО
        tk.Label(content_frame, text="Емельянов Андрей Николаевич",
                font=("Segoe UI", 14, "bold"),
                bg="#ffffff", fg="#1e293b").pack(pady=8)

        # Разделитель
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Описание
        tk.Label(content_frame,
                text="Приложение создано для ведения\nсемейного генеалогического древа,\nсохранения истории семьи\nи пер��дачи знаний будущим поколениям.",
                font=("Segoe UI", 11),
                bg="#ffffff", fg="#475569",
                justify="center").pack(pady=10)

        # Разделитель
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Контакты
        contacts_frame = tk.Frame(content_frame, bg="#f8fafc", relief=tk.SOLID, bd=1)
        contacts_frame.pack(fill=tk.X, pady=10, ipady=10)

        tk.Label(contacts_frame, text="���� К��нтакты ��ля связи:",
                font=("Segoe UI", 11, "bold"),
                bg="#f8fafc", fg="#1e293b").pack(pady=5)

        tk.Label(contacts_frame, text="+375 (29) 147-21-08",
                font=("Segoe UI", 12),
                bg="#f8fafc", fg="#dc2626").pack(pady=3)

        tk.Label(contacts_frame, text="📍 Республика Беларусь",
                font=("Segoe UI", 10),
                bg="#f8fafc", fg="#64748b").pack(pady=3)

        # Кнопка
        tk.Button(dialog, text="Закрыть", command=dialog.destroy,
                 font=("Segoe UI", 11, "bold"),
                 bg="#2563eb", fg="#ffffff",
                 activebackground="#1d4ed8", activeforeground="#ffffff",
                 padx=30, pady=8, relief=tk.FLAT,
                 cursor="hand2").pack(pady=15)

    def _sync_with_server(self):
        """Синхронизация с сервером (если доступна)."""
        if not SYNC_AVAILABLE:
            return
        try:
            if self.username:
                sync_to_server(f"family_tree_{self.username}.json", self.username)
        except Exception as e:
            print(f"Sync error: {e}")

    def _calculate_age_and_zodiac(self, birth_date_str, death_date_str=""):
        """
        Рассчитывает возраст и знак зодиака по дате рождения.
        Возвращает кортеж (возраст, знак_зодиака).
        """
        def parse_date(date_str):
            """Парсит дату в формате dd.mm.yyyy."""
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str.strip(), "%d.%m.%Y")
            except ValueError:
                try:
                    return datetime.strptime(date_str.strip(), "%d.%m.%y")
                except ValueError:
                    return None
        
        def get_zodiac_sign(date):
            """Определяет знак зодиака по дате."""
            if not date:
                return None

            day = date.day
            month = date.month

            # Знаки зодиака по датам
            if (month == 12 and day >= 22) or (month == 1 and day <= 20):
                return "♑ Козерог"
            if (month == 1 and day >= 21) or (month == 2 and day <= 19):
                return "♒ Водолей"
            if (month == 2 and day >= 20) or (month == 3 and day <= 20):
                return "♓ Рыбы"
            if (month == 3 and day >= 21) or (month == 4 and day <= 20):
                return "♈ Овен"
            if (month == 4 and day >= 21) or (month == 5 and day <= 21):
                return "♉ Телец"
            if (month == 5 and day >= 22) or (month == 6 and day <= 21):
                return "♊ Близнецы"
            if (month == 6 and day >= 22) or (month == 7 and day <= 23):
                return "♋ Рак"
            if (month == 7 and day >= 24) or (month == 8 and day <= 23):
                return "♌ Лев"
            if (month == 8 and day >= 24) or (month == 9 and day <= 23):
                return "♍ Дева"
            if (month == 9 and day >= 24) or (month == 10 and day <= 23):
                return "♎ Весы"
            if (month == 10 and day >= 24) or (month == 11 and day <= 22):
                return "♏ Скорпион"
            if (month == 11 and day >= 23) or (month == 12 and day <= 21):
                return "♐ Стрелец"

            return None
        
        birth_date = parse_date(birth_date_str)
        if not birth_date:
            return ("?", None)
        
        # Определяем дату для расчёта возраста
        if death_date_str:
            end_date = parse_date(death_date_str)
            if not end_date:
                end_date = datetime.now()
        else:
            end_date = datetime.now()
        
        # Расчёт возраста
        age = end_date.year - birth_date.year
        if (end_date.month, end_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        # Знак зодиака
        zodiac = get_zodiac_sign(birth_date)
        
        age_str = str(age) if age >= 0 else "?"
        return (age_str, zodiac)

    def _calculate_years_together(self, marriage_date_str):
        """
        Рассчитывает количество лет, прожитых вместе в браке.
        Возвращает строку с количеством лет.
        """
        def parse_date(date_str):
            """Парсит дату в формате dd.mm.yyyy."""
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str.strip(), "%d.%m.%Y")
            except ValueError:
                try:
                    return datetime.strptime(date_str.strip(), "%d.%m.%y")
                except ValueError:
                    return None
        
        marriage_date = parse_date(marriage_date_str)
        if not marriage_date:
            return ""
        
        # Расчёт времени с даты брака до сегодня
        today = datetime.now()
        years = today.year - marriage_date.year
        if (today.month, today.day) < (marriage_date.month, marriage_date.day):
            years -= 1
        
        if years < 0:
            return ""
        elif years == 1:
            return "1 год"
        elif 2 <= years <= 4:
            return f"{years} года"
        else:
            return f"{years} лет"

    def _create_backup(self):
        """Созд��ть резервную копию."""
        if not BACKUP_AVAILABLE:
            return
        try:
            from backup import BackupManager
            bm = BackupManager()
            bm.create_backup(self.model.data_file)
        except Exception as e:
            print(f"Backup error: {e}")