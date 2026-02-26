# -*- coding: utf-8 -*-
"""
Timeline (Временная шкала) для приложения «Семейное древо».

Отображает жизни всех персон в виде горизонтальных полос.
"""

import tkinter as tk
from tkinter import ttk
import constants


class TimelineWindow:
    """Окно временной шкалы жизней персон."""

    def __init__(self, app, model):
        self.app = app  # FamilyTreeApp
        self.model = model
        
        print(f"TimelineWindow: создаётся окно, model.persons={len(model.persons) if model else 0}")

        # Создание окна
        self.window = tk.Toplevel(app.root)
        self.window.title("📅 Временная шкала")
        self.window.geometry("1200x700")

        # Заголовок
        title_frame = tk.Frame(self.window, bg="#ffffff", height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            title_frame,
            text="📅 Временная шкала жизней | Ctrl+колесо - зум, перетаскивание - ЛКМ",
            font=("Segoe UI", 14),
            bg="#ffffff",
            fg="#64748b"
        ).pack(pady=10)
        
        # Панель инструментов
        toolbar = tk.Frame(self.window, bg="#e9ecef")
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # Масштаб
        tk.Label(toolbar, text="Масштаб:", bg="#e9ecef", fg="#1e293b").pack(side=tk.LEFT, padx=10)
        
        self.scale_var = tk.IntVar(value=5)
        scale_combo = ttk.Combobox(
            toolbar,
            textvariable=self.scale_var,
            values=[1, 2, 5, 10, 20],
            width=5,
            state="readonly"
        )
        scale_combo.pack(side=tk.LEFT, padx=5)
        scale_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_timeline())
        tk.Label(toolbar, text="лет/см", bg="#e9ecef", fg="#64748b").pack(side=tk.LEFT, padx=5)
        
        # Фильтры
        tk.Label(toolbar, text="|", bg="#e9ecef", fg="#adb5bd").pack(side=tk.LEFT, padx=10)
        
        self.filter_var = tk.StringVar(value="Все персоны")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["Все персоны", "Только предки", "Только с фото", "Мужчины", "Женщины"],
            width=20,
            state="readonly"
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.on_filter_selected())

        # Легенда символов
        legend_frame = tk.Frame(toolbar, bg="#e9ecef")
        legend_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(legend_frame, text="👶 - Рождение ребёнка", font=("Segoe UI", 9), bg="#e9ecef").pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="💍 - Брак", font=("Segoe UI", 9), bg="#e9ecef").pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="📌 - Событие", font=("Segoe UI", 9), bg="#e9ecef").pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="| Двойной клик - переход к персоне", font=("Segoe UI", 9), bg="#e9ecef", fg="#64748b").pack(side=tk.LEFT, padx=10)

        # Словарь для отображения фильтров
        self.filter_map = {
            "Все персоны": "all",
            "Только предки": "ancestors",
            "Только с фото": "with_photos",
            "Мужчины": "male",
            "Женщины": "female"
        }
        
        # Кнопка закрытия
        tk.Button(
            toolbar,
            text="Закрыть",
            command=self.window.destroy,
            bg="#dc2626",
            fg="#ffffff",
            padx=20,
            pady=5
        ).pack(side=tk.RIGHT, padx=10)
        
        # Кнопка обновления данных
        tk.Button(
            toolbar,
            text="🔄 Обновить данные",
            command=self.reload_data,
            bg="#10b981",
            fg="#ffffff",
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT, padx=10)
        
        # Холст с прокруткой
        canvas_frame = tk.Frame(self.window, bg="#ffffff", bd=2, relief=tk.SUNKEN)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаём Canvas (без скроллбаров - теперь перетаскивание)
        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0, width=2000, height=500)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Фрейм для содержимого
        self.timeline_frame = tk.Frame(self.canvas, bg="#ffffff")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.timeline_frame,
            anchor="nw",
            width=1800
        )
        
        # Привязка событий
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.timeline_frame.bind("<Configure>", self.on_frame_configure)

        # Колесо мыши - зум (без Ctrl)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_zoom)

        # Перетаскивание - привязываем ко всем тегам
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Дополнительно привязываем к тегам, чтобы они не перехватывали события
        self.canvas.tag_bind("year_scale", "<ButtonPress-1>", self.on_mouse_press)
        self.canvas.tag_bind("year_scale", "<B1-Motion>", self.on_mouse_drag)
        self.canvas.tag_bind("year_scale", "<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.tag_bind("person_life", "<ButtonPress-1>", self.on_mouse_press_for_person)
        self.canvas.tag_bind("person_life", "<B1-Motion>", self.on_mouse_drag)
        self.canvas.tag_bind("person_life", "<ButtonRelease-1>", self.on_mouse_release)

        # Переменные для перетаскивания и зума
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_scroll_x = 0
        self.drag_start_scroll_y = 0
        self.is_dragging = False
        self.current_scale = 1.0
        self.min_scale = 0.5
        self.max_scale = 3.0
        
        # Центррирование окна
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1200) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"+{x}+{y}")
        
        # Отрисовка
        self.refresh_timeline()

    def on_canvas_configure(self, event):
        """Обновляет область прокрутки при изменении размера canvas."""
        # Устанавливаем большую область прокрутки для перетаскивания
        self.canvas.configure(scrollregion=(0, 0, 4000, 2000))

    def on_frame_configure(self, event):
        """Обновляет область прокрутки при изменении размера фрейма."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel_zoom(self, event):
        """Зум колесом мыши (без Ctrl)."""
        # Зум колесом мыши
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def on_mouse_press(self, event):
        """Начало перетаскивания."""
        try:
            # Проверяем, что холст готов
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Холст ещё не готов к перетаскиванию
                return
            
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Получаем текущие координаты прокрутки с защитой
            try:
                self.drag_start_scroll_x = self.canvas.xview()[0]
                self.drag_start_scroll_y = self.canvas.yview()[0]
            except Exception:
                # Если не удалось получить координаты, используем 0
                self.drag_start_scroll_x = 0.0
                self.drag_start_scroll_y = 0.0
        except Exception:
            # Тихо игнорируем, чтобы не закрывать окно
            self.is_dragging = False

    def on_mouse_drag(self, event):
        """Перетаскивание холста."""
        try:
            if not self.is_dragging:
                return

            # Получаем размеры холста
            try:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
            except Exception:
                # Окно ещё не готово
                return

            # Защита от деления на ноль
            if canvas_width <= 1 or canvas_height <= 1:
                return

            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # Вычисляем новые координаты прокрутки
            new_x = self.drag_start_scroll_x - dx / canvas_width
            new_y = self.drag_start_scroll_y - dy / canvas_height

            # Ограничиваем диапазон [0.0, 1.0]
            new_x = max(0.0, min(1.0, new_x))
            new_y = max(0.0, min(1.0, new_y))

            # Прокрутка с защитой от ошибок на границах
            try:
                self.canvas.xview_moveto(new_x)
                self.canvas.yview_moveto(new_y)
            except Exception:
                # Игнорируем ошибки прокрутки на границах
                pass
        except Exception:
            # Тихо игнорируем ошибки перетаскивания, чтобы не закрывать окно
            self.is_dragging = False

    def on_mouse_press_for_person(self, event):
        """
        Обработка нажатия на персону.
        Начинаем перетаскивание холста.
        """
        # Начинаем перетаскивание как обычно
        self.on_mouse_press(event)

    def on_mouse_release(self, event):
        """Конец перетаскивания."""
        try:
            self.is_dragging = False
        except Exception as e:
            print(f"Timeline: ошибка при отпускании: {e}")

    def zoom_in(self):
        """Увеличить масштаб."""
        try:
            new_scale = self.current_scale * 1.2
            if new_scale <= self.max_scale:
                self.current_scale = new_scale
                self.refresh_timeline()
        except Exception as e:
            print(f"Timeline: ошибка при увеличении: {e}")

    def zoom_out(self):
        """Уменьшить масштаб."""
        try:
            new_scale = self.current_scale / 1.2
            if new_scale >= self.min_scale:
                self.current_scale = new_scale
                self.refresh_timeline()
        except Exception as e:
            print(f"Timeline: ошибка при уменьшении: {e}")

    def get_filtered_persons(self):
        """Возвращает отфильтрованный список персон."""
        persons = list(self.model.get_all_persons().values())
        
        # Получаем тип фильтра из словаря
        filter_type = self.filter_map.get(self.filter_var.get(), "all")
        
        if filter_type == "all":
            return persons
        elif filter_type == "ancestors":
            return [p for p in persons if p.parents]
        elif filter_type == "with_photos":
            return [p for p in persons if p.has_photo()]
        elif filter_type == "male":
            return [p for p in persons if p.gender == "Мужской"]
        elif filter_type == "female":
            return [p for p in persons if p.gender == "Женский"]
        
        return persons

    def on_filter_selected(self):
        """Обработка выбора фильтра."""
        self.refresh_timeline()

    def reload_data(self):
        """Перезагружает данные из файла."""
        # Сохраняем текущий центр
        current_center = self.model.current_center
        
        # Перезагружаем данные из файла
        self.model.load_from_file()
        
        # Восстанавливаем центр
        if current_center:
            self.model.current_center = current_center
        
        # Обновляем Timeline
        self.refresh_timeline()
        
        # Показываем количество персон
        persons_count = len(self.model.get_all_persons())
        print(f"Данные обновлены: {persons_count} персон")

    def parse_date(self, date_str):
        """Парсит дату в формате DD.MM.YYYY и возвращает год."""
        if not date_str:
            return None
        try:
            parts = date_str.split(".")
            if len(parts) == 3:
                return int(parts[2])
        except:
            pass
        return None

    def draw_year_scale(self, min_year, max_year, pixels_per_year, y_position):
        """
        Отрисовывает шкалу лет (ось времени).
        
        Args:
            min_year: Минимальный год.
            max_year: Максимальный год.
            pixels_per_year: Пикселей на год.
            y_position: Позиция Y для шкалы.
        """
        # Очищаем старую шкалу
        self.canvas.delete("year_scale")
        
        # Параметры
        tick_height_major = 15  # Длинные засечки для десятилетий
        tick_height_minor = 8   # Короткие засечки для лет
        font_size = 9
        
        # Рисуем засечки и подписи для каждого года
        for year in range(min_year, max_year + 1):
            x = int((year - min_year) * pixels_per_year)
            
            # Определяем тип засечки
            if year % 10 == 0:
                # Десятилетие - длинная засечка с подписью
                self.canvas.create_line(
                    x, y_position,
                    x, y_position + tick_height_major,
                    fill="#64748b", width=1, tags="year_scale"
                )
                
                # Подпись года
                self.canvas.create_text(
                    x + 3, y_position + tick_height_major + 5,
                    text=str(year),
                    font=("Segoe UI", font_size),
                    fill="#1e293b",
                    anchor="w",
                    tags="year_scale"
                )
            elif year % 5 == 0:
                # Пятилетие - средняя засечка
                self.canvas.create_line(
                    x, y_position,
                    x, y_position + tick_height_minor,
                    fill="#94a3b8", width=1, tags="year_scale"
                )
            else:
                # Год - короткая засечка
                self.canvas.create_line(
                    x, y_position + tick_height_major - tick_height_minor,
                    x, y_position + tick_height_major,
                    fill="#cbd5e1", width=1, tags="year_scale"
                )
        
        # Рисуем горизонтальную линию оси
        self.canvas.create_line(
            0, y_position + tick_height_major,
            int((max_year - min_year) * pixels_per_year), y_position + tick_height_major,
            fill="#64748b", width=1, tags="year_scale"
        )
        
        # Заголовок шкалы
        self.canvas.create_text(
            10, y_position - 10,
            text="Шкала лет:",
            font=("Segoe UI", 9, "bold"),
            fill="#1e293b",
            anchor="w",
            tags="year_scale"
        )

    def refresh_timeline(self):
        """Обновляет временную шкалу."""
        try:
            # Очищаем canvas
            self.canvas.delete("person_life")
            self.canvas.delete("year_scale")
            self.canvas.delete("significant_event")
            
            persons = self.get_filtered_persons()
            print(f"Timeline: ВСЕГО персон={len(persons)}")
            
            if not persons:
                self.canvas.create_text(500, 200, text="Нет персон", font=("Segoe UI", 14), fill="#64748b", tags="message")
                return
            
            # Фильтруем персоны с датами
            persons_with_dates = [p for p in persons if self.parse_date(p.birth_date)]
            
            if not persons_with_dates:
                self.canvas.create_text(500, 200, text=f"Нет дат рождения\nПерсон: {len(persons)}", font=("Segoe UI", 14), fill="#64748b", justify="center", tags="message")
                return
            
            persons = persons_with_dates
            
            # Диапазон лет
            years = []
            for p in persons:
                birth_year = self.parse_date(p.birth_date)
                death_year = self.parse_date(p.death_date) if p.is_deceased else None
                if birth_year: years.append(birth_year)
                if death_year: years.append(death_year)
            
            if not years: return
            min_year = min(years) - 5
            max_year = max(years) + 5
            
            # Настройки
            scale = self.scale_var.get()
            base_pixels_per_year = 20 / scale
            pixels_per_year = base_pixels_per_year * self.current_scale
            
            # Сортировка
            persons.sort(key=lambda p: self.parse_date(p.birth_date) or 9999)
            
            # Отрисовка
            row_height = 40
            y_offset = 60
            
            self.draw_year_scale(min_year, max_year, pixels_per_year, y_offset - 50)
            
            for i, person in enumerate(persons):
                birth_year = self.parse_date(person.birth_date)
                death_year = self.parse_date(person.death_date) if person.is_deceased else 2026
                
                if not birth_year: continue
                
                x_start = int((birth_year - min_year) * pixels_per_year)
                width = max(50, int((death_year - birth_year) * pixels_per_year))
                y = y_offset + i * row_height
                color = "#60a5fa" if person.gender == "Мужской" else "#f472b6"
                
                # УНИКАЛЬНЫЙ тег для каждой полосы
                person_tag = f"person_{person.id}"
                
                # Полоса
                self.canvas.create_rectangle(
                    x_start, y, x_start + width, y + row_height - 4,
                    fill=color, outline="#1e293b", width=1,
                    tags=(person_tag, "person_life")
                )
                
                # Имя
                text = f"{person.surname} {person.name}"
                max_text_width = width - 60
                while len(text) > 3 and len(text) * 7 > max_text_width:
                    text = text[:-1]
                if len(text) < len(f"{person.surname} {person.name}"):
                    text = text[:-3] + "..."
                
                if width > 30:
                    self.canvas.create_text(x_start + 5, y + (row_height - 4) // 2, text=text, font=("Segoe UI", 8, "bold"), fill="#ffffff", anchor="w", tags=person_tag)
                
                # Даты
                if width > 80:
                    self.canvas.create_text(x_start + width - 5, y + (row_height - 4) // 2, text=f"{birth_year}-{death_year}", font=("Segoe UI", 7), fill="#ffffff", anchor="e", tags=person_tag)
                
                # === ВАЖНО: Bind с ПРАВИЛЬНЫМ замыканием ===
                # Сохраняем person.id в отдельную переменную ДО lambda
                pid = person.id
                self.canvas.tag_bind(person_tag, "<Double-Button-1>", lambda e, stored_pid=pid: self.on_person_double_click_by_id(stored_pid))
            
            # События
            self.draw_significant_events(persons, min_year, pixels_per_year, y_offset, row_height)
            
            # Прокрутка
            total_height = y_offset + len(persons) * row_height
            total_width = int((max_year - min_year) * pixels_per_year) + 100
            self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
            
        except Exception as e:
            print(f"Timeline: ошибка при отрисовке: {e}")
            import traceback
            traceback.print_exc()


    def draw_significant_events(self, persons, min_year, pixels_per_year, y_offset, row_height):
        """
        Отрисовывает значимые события на временной шкале (внутри полоски).
        
        События:
        - Рождение детей (👶)
        - Брак (💍)
        - Пользовательские события (📌)
        """
        self.canvas.delete("significant_event")
        
        # Параметры - размещаем внутри полоски
        event_y_offset = row_height // 2  # Середина полоски
        
        for i, person in enumerate(persons):
            birth_year = self.parse_date(person.birth_date)
            death_year = self.parse_date(person.death_date) if person.is_deceased else None
            
            if not birth_year:
                continue
            
            y = y_offset + i * row_height
            
            # 1. Рождение детей
            if hasattr(person, 'children') and person.children:
                for child_id in person.children:
                    child = self.model.get_person(child_id)
                    if child and child.birth_date:
                        child_year = self.parse_date(child.birth_date)
                        if child_year and birth_year <= child_year <= (death_year or 2026):
                            x_child = int((child_year - min_year) * pixels_per_year)
                            self.canvas.create_text(
                                x_child, y + event_y_offset,
                                text="👶", font=("Segoe UI Emoji", 9),
                                fill="#ffffff", anchor="center", tags="significant_event"
                            )
            
            # 2. Брак (если есть дата брака)
            if hasattr(person, 'spouse_ids') and person.spouse_ids:
                for spouse_id in person.spouse_ids:
                    marriage_date = self.model.get_marriage_date(person.id, spouse_id)
                    if marriage_date:
                        marriage_year = self.parse_date(marriage_date)
                        if marriage_year and birth_year <= marriage_year <= (death_year or 2026):
                            x_marriage = int((marriage_year - min_year) * pixels_per_year)
                            self.canvas.create_text(
                                x_marriage, y + event_y_offset,
                                text="💍", font=("Segoe UI Emoji", 9),
                                fill="#ffffff", anchor="center", tags="significant_event"
                            )
            
            # 3. Пользовательские значимые события
            if hasattr(person, 'significant_events') and person.significant_events:
                for event in person.significant_events:
                    event_date = event.get("date", "")
                    event_title = event.get("title", "Событие")
                    if event_date:
                        event_year = self.parse_date(event_date)
                        if event_year and birth_year <= event_year <= (death_year or 2026):
                            x_event = int((event_year - min_year) * pixels_per_year)
                            self.canvas.create_text(
                                x_event, y + event_y_offset,
                                text="📌", font=("Segoe UI Emoji", 9),
                                fill="#ffffff", anchor="center", tags="significant_event"
                            )

    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                print(f"  Персона найдена: {person.display_name()}")
                
                # Закрываем окно СРАЗУ
                self.window.destroy()
                
                # СНАЧАЛА устанавливаем центр
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                
                # Обновляем метку
                self.app.center_label.config(text=f"Центр: {person.display_name()}")
                
                # Перерисовываем дерево С ЦЕНТРИРОВАНИЕМ
                # refresh_view() сам отцентрирует на current_center
                self.app.refresh_view(skip_layout=False)
                
                # Даём время на отрисовку
                self.app.canvas.update_idletasks()
                
                # Теперь центрируем холст на персоне
                self.app.center_tree_on_person(person_id)
                
                print(f"  current_center={self.app.model.current_center}")
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def on_person_double_click(self, person):
        """Обработка двойного клика (старый метод)."""
        self.on_person_double_click_by_id(person.id)

    def on_person_release(self, person):
        """
        Обработка отпускания кнопки мыши на персоне.
        Если не было перетаскивания - выбираем персону.
        """
        # Проверяем, было ли перетаскивание
        if not self.is_dragging:
            self.on_person_click(person)

    def on_person_click(self, person):
        """Обработка клика на персону."""
        # Закрываем Timeline
        self.window.destroy()
        
        # Устанавливаем центр на выбранную персону
        self.model.current_center = person.id
        
        # Обновляем главное окно
        if hasattr(self, 'parent') and hasattr(self.parent, 'refresh_view'):
            self.parent.refresh_view()



    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                print(f"  Персона найдена: {person.display_name()}")
                
                # Устанавливаем центр
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                self.app.center_label.config(text=f"Центр: {person.display_name()}")
                
                # Перерисовываем и центрируем
                self.app.refresh_view(skip_layout=False)
                self.app.center_tree_on_person(person_id)
                
                # Закрываем окно через 100мс
                self.window.after(100, self.window.destroy)
                
                print(f"  current_center={self.app.model.current_center}")
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")

def open_timeline(parent, model):
    """Открывает окно временной шкалы."""
    timeline = TimelineWindow(parent, model)
    timeline.window.wait_window()
