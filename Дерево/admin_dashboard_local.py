# -*- coding: utf-8 -*-
"""
Локальная админ-панель для Андрея Емельянова.
Работает БЕЗ сервера, показывает данные из текущей сессии.
С подробным логированием для отладки.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
import sys
import traceback

# Логирование
LOG_FILE = Path(__file__).parent.parent / "admin_panel_log.txt"

def log(message):
    """Записывает лог в файл"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[LOG] {message}")
    except:
        pass

# Добавляем путь к модулю Дерево
sys.path.insert(0, str(Path(__file__).parent))


class LocalAdminDashboard:
    """Локальная админ-панель - просмотр и управление данными"""

    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.data_file = None
        self.data = {}
        self.persons = []
        self.marriages = []
        
        log("=" * 50)
        log(f"Запуск админ-панели для: {username}")
        
        self.root.title(f"👑 Админ-панель — {username}")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#2c3e50')
        style.configure('SubHeader.TLabel', font=('Segoe UI', 12), foreground='#7f8c8d')
        style.configure('Stat.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#34495e')
        
        self._setup_ui()
        
        # Загружаем ТОЛЬКО из файла (отключаем загрузку из приложения)
        self._find_data_file()

    def _try_load_from_app(self):
        """Пытается получить данные из текущего экземпляра приложения"""
        log("Попытка загрузки из приложения...")
        self.status_var.set("Попытка получения данных из приложения...")
        
        try:
            # Пробуем получить доступ к главному окну приложения
            import tkinter as tk
            main_app = tk._default_root
            
            if main_app and hasattr(main_app, 'model'):
                log("Главное приложение найдено")
                model = main_app.model
                
                # Получаем персоны
                if hasattr(model, 'persons') and model.persons:
                    log(f"Найдено персон: {len(model.persons)}")
                    self.persons = []
                    for pid, person in model.persons.items():
                        p_data = {
                            'id': pid,
                            'name': person.name,
                            'surname': person.surname,
                            'gender': person.gender,
                            'birth_date': getattr(person, 'birth_date', ''),
                            'death_date': getattr(person, 'death_date', ''),
                            'parents': list(getattr(person, 'parents', [])),
                            'children': list(getattr(person, 'children', [])),
                        }
                        self.persons.append(p_data)
                    
                    # Получаем браки
                    if hasattr(model, 'marriages') and model.marriages:
                        log(f"Найдено семей: {len(model.marriages)}")
                        self.marriages = []
                        for m in model.marriages:
                            if isinstance(m, dict):
                                self.marriages.append(m)
                            elif hasattr(m, '__dict__'):
                                self.marriages.append(m.__dict__)
                    
                    self._update_stats()
                    self._fill_persons_table()
                    self._fill_families_table()
                    self._show_info()
                    
                    msg = f"✅ Загружено из приложения: {len(self.persons)} персон"
                    self.status_var.set(msg)
                    log(msg)
                    return
            else:
                log("Главное приложение не найдено или нет модели")
            
            # Если не получилось - ищем файл
            log("Загрузка из файла...")
            self._find_data_file()
            
        except Exception as e:
            log(f"Ошибка загрузки из приложения: {e}")
            traceback.print_exc()
            self._find_data_file()

    def _setup_ui(self):
        """Создаёт интерфейс"""
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === ШАПКА ===
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header, text="👑 Админ-панель (Локальная)", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text=f"Администратор: {self.username}", style='SubHeader.TLabel').pack(anchor=tk.W)
        
        # Кнопки
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="📂 Открыть файл", command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.root.destroy).pack(side=tk.LEFT, padx=2)
        
        # === СТАТИСТИКА ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Статистика", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.stats_labels = {}
        stats_config = [
            ('persons', '📄 Персон', 0),
            ('families', '👨‍👩‍👧 Семей', 1),
            ('males', '👨 Мужчин', 2),
            ('females', '👩 Женщин', 3)
        ]
        
        for key, label, idx in stats_config:
            frame = ttk.Frame(stats_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            ttk.Label(frame, text=label, font=('Segoe UI', 11)).pack()
            self.stats_labels[key] = ttk.Label(frame, text="—", style='Stat.TLabel')
            self.stats_labels[key].pack()
        
        # === ВКЛАДКИ ===
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Вкладка 1: Персоны
        persons_frame = ttk.Frame(notebook, padding=10)
        notebook.add(persons_frame, text="📄 Персоны")
        self._create_persons_tab(persons_frame)
        
        # Вкладка 2: Семьи
        families_frame = ttk.Frame(notebook, padding=10)
        notebook.add(families_frame, text="👨‍👩‍👧 Семьи")
        self._create_families_tab(families_frame)
        
        # Вкладка 3: Информация
        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="ℹ️ Информация")
        self._create_info_tab(info_frame)
        
        # === СТАТУС БАР ===
        self.status_var = tk.StringVar(value="Ожидание файла...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

    def _create_persons_tab(self, parent):
        """Вкладка персоны"""
        # Таблица
        columns = ('id', 'name', 'surname', 'gender', 'birth', 'death', 'parents', 'children')
        self.persons_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        self.persons_tree.heading('id', text='ID')
        self.persons_tree.heading('name', text='Имя')
        self.persons_tree.heading('surname', text='Фамилия')
        self.persons_tree.heading('gender', text='Пол')
        self.persons_tree.heading('birth', text='Рождение')
        self.persons_tree.heading('death', text='Смерть')
        self.persons_tree.heading('parents', text='Родители')
        self.persons_tree.heading('children', text='Дети')
        
        self.persons_tree.column('id', width=50)
        self.persons_tree.column('name', width=150)
        self.persons_tree.column('surname', width=150)
        self.persons_tree.column('gender', width=60)
        self.persons_tree.column('birth', width=100)
        self.persons_tree.column('death', width=100)
        self.persons_tree.column('parents', width=80)
        self.persons_tree.column('children', width=80)
        
        # Скроллбары
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.persons_tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.persons_tree.xview)
        self.persons_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.persons_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

    def _create_families_tab(self, parent):
        """Вкладка семьи"""
        columns = ('husband', 'wife', 'date')
        self.families_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        self.families_tree.heading('husband', text='Муж')
        self.families_tree.heading('wife', text='Жена')
        self.families_tree.heading('date', text='Дата брака')
        
        self.families_tree.column('husband', width=200)
        self.families_tree.column('wife', width=200)
        self.families_tree.column('date', width=120)
        
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.families_tree.yview)
        self.families_tree.configure(yscrollcommand=vsb.set)
        
        self.families_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_info_tab(self, parent):
        """Вкладка информации"""
        info_text = tk.Text(parent, wrap=tk.WORD, font=('Consolas', 10))
        info_text.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = info_text

    def _find_data_file(self):
        """Ищет ВСЕ файлы с данными и показывает список пользователей"""
        log("Поиск всех файлов с данными...")
        self.status_var.set("Поиск файлов с данными...")
        
        all_files = []
        
        # Папка data в разных местах
        data_dirs = [
            Path(__file__).parent.parent / "data",  # data в корне проекта
        ]
        
        for data_dir in data_dirs:
            log(f"Проверка папки: {data_dir}")
            if data_dir.exists():
                for json_file in data_dir.glob("family_tree*.json"):
                    # Пропускаем служебные файлы
                    if "backup" in json_file.name.lower():
                        continue
                    log(f"  Найден файл: {json_file.name}")
                    all_files.append(json_file)
        
        if all_files:
            log(f"Найдено файлов: {len(all_files)}")
            self._show_user_list(all_files)
        else:
            log("Файлы не найдены")
            self._show_file_not_found()

    def _show_user_list(self, files):
        """Показывает список всех пользователей"""
        # Очищаем текущие данные
        self.persons = []
        self.marriages = []
        
        # Создаём список пользователей
        users_frame = ttk.Frame(self.root)
        users_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(users_frame, text="👥 Пользователи", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Таблица пользователей
        columns = ('user', 'file', 'persons', 'families')
        users_tree = ttk.Treeview(users_frame, columns=columns, show='headings', height=15)
        
        users_tree.heading('user', text='Пользователь')
        users_tree.heading('file', text='Файл')
        users_tree.heading('persons', text='Персон')
        users_tree.heading('families', text='Семей')
        
        users_tree.column('user', width=200)
        users_tree.column('file', width=300)
        users_tree.column('persons', width=80)
        users_tree.column('families', width=80)
        
        # Заполняем
        for f in files:
            # Извлекаем имя пользователя из имени файла
            user_name = f.name.replace('family_tree_', '').replace('.json', '')
            
            # Считаем персоны
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                persons_count = len(data.get('persons', {}))
                marriages_count = len(data.get('marriages', []))
            except:
                persons_count = 0
                marriages_count = 0
            
            users_tree.insert('', tk.END, values=(user_name, f.name, persons_count, marriages_count), tags=(str(f),))
        
        users_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(users_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        def open_selected():
            selection = users_tree.selection()
            if selection:
                item = users_tree.item(selection[0])
                tags = item.get('tags')
                if tags:
                    filepath = Path(tags[0])
                    users_frame.destroy()
                    self._load_file(filepath)
        
        ttk.Button(btn_frame, text="👁️ Просмотреть", command=open_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.root.destroy).pack(side=tk.LEFT, padx=5)
        
        self.status_var.set(f"Найдено пользователей: {len(files)}")

    def _show_file_choice(self, paths):
        """Показывает диалог выбора из найденных файлов"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выберите файл")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Найдено несколько файлов:", padding=10).pack()
        
        listbox = tk.Listbox(dialog, width=60, height=10)
        listbox.pack(padx=20, pady=10)
        
        for path in paths:
            listbox.insert(tk.END, path.name)
        
        def select():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                dialog.destroy()
                self._load_file(paths[idx])
        
        ttk.Button(dialog, text="Выбрать", command=select).pack(pady=5)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)
        
        dialog.wait_window()

    def _show_file_not_found(self):
        """Показывает сообщение что файл не найден"""
        self.status_var.set("❌ Файл не найден")
        
        # Создаём вкладку с инструкцией
        help_frame = ttk.Frame(self.root)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        ttk.Label(help_frame, text="📁 Файл с данными не найден", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=20)
        
        instructions = """
Пожалуйста, выберите файл с данными вручную.

Где обычно находится файл:
1. Папка "data" в папке программы
2. Документы пользователя
3. AppData\\FamilyTree

Имя файла обычно содержит:
• family_tree_*.json
• family_*.json
• tree_*.json

Нажмите "📂 Открыть файл" вверху окна.
"""
        ttk.Label(help_frame, text=instructions, justify=tk.LEFT).pack(pady=20)
        
        ttk.Button(help_frame, text="📂 Открыть файл", command=self._open_file).pack(pady=10)
        ttk.Button(help_frame, text="❌ Закрыть", command=self.root.destroy).pack(pady=10)

    def _open_file(self):
        """Открывает файл с данными"""
        filename = filedialog.askopenfilename(
            title="Открыть файл с данными",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path(__file__).parent.parent
        )
        
        if filename:
            self._load_file(filename)

    def _load_file(self, filepath):
        """Загружает файл"""
        log(f"Загрузка файла: {filepath}")
        self.data_file = filepath
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            log(f"✅ Файл загружен успешно")
            log(f"Тип данных: {type(self.data)}")
            self.status_var.set(f"✅ Загружено: {filepath.name}")
            
            # Извлекаем данные - проверяем формат
            persons_data = self.data.get('persons', [])
            log(f"Тип persons: {type(persons_data)}")
            
            # persons может быть dict {id: person} или list [person]
            if isinstance(persons_data, dict):
                # Конвертируем dict в список
                self.persons = []
                for pid, pdata in persons_data.items():
                    if isinstance(pdata, dict):
                        pdata['id'] = pid  # Добавляем ID
                        self.persons.append(pdata)
                log(f"✅ Персон загружено: {len(self.persons)} (из dict)")
            elif isinstance(persons_data, list):
                self.persons = persons_data
                log(f"✅ Персон загружено: {len(self.persons)} (из list)")
            else:
                self.persons = []
                log("❌ persons неизвестного формата")
            
            marriages_data = self.data.get('marriages', [])
            if isinstance(marriages_data, list):
                self.marriages = [m for m in marriages_data if isinstance(m, dict)]
                log(f"✅ Семей загружено: {len(self.marriages)}")
            else:
                self.marriages = []
            
            # Обновляем статистику
            self._update_stats()
            
            # Заполняем таблицы
            self._fill_persons_table()
            self._fill_families_table()
            
            # Показываем информацию
            self._show_info()
            
        except Exception as e:
            log(f"❌ Ошибка загрузки: {e}")
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")
            self.status_var.set("❌ Ошибка загрузки")

    def _update_stats(self):
        """Обновляет статистику"""
        total = len(self.persons)
        males = sum(1 for p in self.persons if p.get('gender') == 'Мужской')
        females = sum(1 for p in self.persons if p.get('gender') == 'Женский')
        families = len(self.marriages)
        
        self.stats_labels['persons'].config(text=str(total))
        self.stats_labels['families'].config(text=str(families))
        self.stats_labels['males'].config(text=str(males))
        self.stats_labels['females'].config(text=str(females))

    def _fill_persons_table(self):
        """Заполняет таблицу персон"""
        self.persons_tree.delete(*self.persons_tree.get_children())
        
        for person in self.persons:
            pid = person.get('id', '')
            name = person.get('name', '')
            surname = person.get('surname', '')
            gender = person.get('gender', '')
            birth = person.get('birth_date', '')
            death = person.get('death_date', '')
            parents = len(person.get('parents', []))
            children = len(person.get('children', []))
            
            self.persons_tree.insert('', tk.END, values=(
                pid, name, surname, gender, birth, death, parents, children
            ))

    def _fill_families_table(self):
        """Заполняет таблицу семей"""
        self.families_tree.delete(*self.families_tree.get_children())

        # Создаём словарь для поиска имён по ID
        person_names = {p.get('id'): f"{p.get('surname', '')} {p.get('name', '')}"
                       for p in self.persons}

        for marriage in self.marriages:
            # Защита от неправильного формата
            if not isinstance(marriage, dict):
                continue
                
            husband_id = marriage.get('husband_id', '')
            wife_id = marriage.get('wife_id', '')
            date = marriage.get('date', '')

            husband_name = person_names.get(husband_id, str(husband_id))
            wife_name = person_names.get(wife_id, str(wife_id))

            self.families_tree.insert('', tk.END, values=(
                husband_name, wife_name, date
            ))

    def _show_info(self):
        """Показывает информацию о файле"""
        self.info_text.delete(1.0, tk.END)
        
        info = f"""
=== ИНФОРМАЦИЯ О ФАЙЛЕ ===

Файл: {self.data_file}
Загружено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

=== СТАТИСТИКА ===

Всего персон: {len(self.persons)}
Мужчин: {sum(1 for p in self.persons if p.get('gender') == 'Мужской')}
Женщин: {sum(1 for p in self.persons if p.get('gender') == 'Женский')}
Семей: {len(self.marriages)}

=== ПОЛЬЗОВАТЕЛЬ ===

Администратор: {self.username}
Доступ: Полный (локальный)

=== ПРИМЕЧАНИЕ ===

Это локальная админ-панель.
Она работает без подключения к серверу.
Все данные хранятся на вашем компьютере.
"""
        self.info_text.insert(tk.END, info)


def open_local_admin_dashboard(username):
    """Открывает локальную админ-панель"""
    dashboard_root = tk.Toplevel()
    dashboard = LocalAdminDashboard(dashboard_root, username)
    dashboard_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "Андрей Емельянов"
    
    open_local_admin_dashboard(username)
