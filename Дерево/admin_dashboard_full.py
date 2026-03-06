# -*- coding: utf-8 -*-
"""
Админ-панель для Андрея Емельянова.
Полный доступ ко всем пользователям и их деревьям.
Данные подтягиваются с сервера.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import urllib.request
import urllib.error
import base64

# URL сервера
SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"


class AdminDashboard:
    """Админ-панель с полным доступом ко всем пользователям"""

    def __init__(self, root, login, password):
        self.root = root
        self.login = login
        self.password = password
        self.token = None
        self.all_users = []
        self.all_trees = []
        
        self.root.title(f"👑 Админ-панель — {login}")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 700)
        
        # Настройка стиля
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#2c3e50')
        style.configure('SubHeader.TLabel', font=('Segoe UI', 12), foreground='#7f8c8d')
        style.configure('Stat.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#34495e')
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Warning.TLabel', foreground='#e67e22')
        style.configure('Danger.TLabel', foreground='#e74c3c')
        style.configure('Admin.TFrame', background='#ecf0f1')
        
        self._setup_ui()
        
        # Сначала получаем токен, затем загружаем данные
        self.root.after(100, lambda: self._authenticate_and_load())

    def _setup_ui(self):
        """Создаёт интерфейс админ-панели"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === ШАПКА ===
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header, text="👑 Админ-панель", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text=f"Администратор: {self.login}", style='SubHeader.TLabel').pack(anchor=tk.W)
        
        # Кнопки управления
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="🔄 Обновить", command=self._load_all_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.root.destroy).pack(side=tk.LEFT, padx=2)
        
        # === СТАТИСТИКА СИСТЕМЫ ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Статистика системы", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.stats_labels = {}
        stats_config = [
            ('users', '👥 Пользователей', 0),
            ('trees', '🌳 Деревьев', 1),
            ('persons', '📄 Персон', 2),
            ('active', '✅ Активных', 3)
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
        
        # Вкладка 1: Пользователи
        users_frame = ttk.Frame(notebook, padding=10)
        notebook.add(users_frame, text="👥 Пользователи")
        self._create_users_tab(users_frame)
        
        # Вкладка 2: Деревья
        trees_frame = ttk.Frame(notebook, padding=10)
        notebook.add(trees_frame, text="🌳 Все деревья")
        self._create_trees_tab(trees_frame)
        
        # Вкладка 3: Логи
        log_frame = ttk.Frame(notebook, padding=10)
        notebook.add(log_frame, text="📋 Журнал операций")
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # === СТАТУС БАР ===
        self.status_var = tk.StringVar(value="Готово")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

    def _create_users_tab(self, parent):
        """Создаёт вкладку пользователей"""
        # Таблица пользователей
        columns = ('login', 'email', 'created', 'trees', 'status', 'last_sync')
        self.users_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        self.users_tree.heading('login', text='Логин')
        self.users_tree.heading('email', text='Email')
        self.users_tree.heading('created', text='Создан')
        self.users_tree.heading('trees', text='Деревья')
        self.users_tree.heading('status', text='Статус')
        self.users_tree.heading('last_sync', text='Последняя синхронизация')
        
        self.users_tree.column('login', width=150)
        self.users_tree.column('email', width=200)
        self.users_tree.column('created', width=120)
        self.users_tree.column('trees', width=80)
        self.users_tree.column('status', width=100)
        self.users_tree.column('last_sync', width=150)
        
        # Скроллбары
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.users_tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.users_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Контекстное меню
        self.user_menu = tk.Menu(self.users_tree, tearoff=0)
        self.user_menu.add_command(label="👁️ Просмотреть деревья", command=self._view_user_trees)
        self.user_menu.add_command(label="🔓 Сбросить пароль", command=self._reset_user_password)
        self.user_menu.add_command(label="⚠️ Заблокировать/Разблокировать", command=self._toggle_user_status)
        self.user_menu.add_separator()
        self.user_menu.add_command(label="🗑️ Удалить пользователя", command=self._delete_user)
        
        self.users_tree.bind('<Button-3>', self._show_user_menu)
        self.users_tree.bind('<Double-Button-1>', lambda e: self._open_user_full_tree())

    def _create_trees_tab(self, parent):
        """Создаёт вкладку деревьев"""
        # Таблица деревьев
        columns = ('owner', 'name', 'updated', 'size', 'persons')
        self.trees_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        self.trees_tree.heading('owner', text='Владелец')
        self.trees_tree.heading('name', text='Название')
        self.trees_tree.heading('updated', text='Обновлено')
        self.trees_tree.heading('size', text='Размер')
        self.trees_tree.heading('persons', text='Персон')
        
        self.trees_tree.column('owner', width=150)
        self.trees_tree.column('name', width=250)
        self.trees_tree.column('updated', width=140)
        self.trees_tree.column('size', width=100)
        self.trees_tree.column('persons', width=80)
        
        # Скроллбары
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.trees_tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.trees_tree.xview)
        self.trees_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.trees_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Контекстное меню
        self.tree_menu = tk.Menu(self.trees_tree, tearoff=0)
        self.tree_menu.add_command(label="👁️ Просмотреть дерево", command=self._view_tree)
        self.tree_menu.add_command(label="📥 Скачать", command=self._download_tree)
        self.tree_menu.add_command(label="🗑️ Удалить", command=self._delete_tree)
        
        self.trees_tree.bind('<Button-3>', self._show_tree_menu)
        self.trees_tree.bind('<Double-Button-1>', lambda e: self._view_tree())

    def _authenticate_and_load(self):
        """Сначала аутентифицируется, затем загружает данные"""
        # Используем пароль по умолчанию для Андрея Емельянова
        # (не запрашиваем у пользователя)
        self.status_var.set("Аутентификация...")
        self._log("🔐 Аутентификация на сервере...")

        # Получаем токен
        token = self._get_auth_token()

        if token:
            self.token = token
            self._log("✅ Аутентификация успешна")
            self._load_all_data()
        else:
            self._log("❌ Не удалось аутентифицироваться")
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу.\n\nПроверьте интернет-соединение.")
            self.root.destroy()

    def _get_auth_token(self):
        """Получает JWT токен для авторизации."""
        
        # Пробуем разные варианты логина (Андрей Емельянов - основной)
        login_variants = [
            self.login,  # Как ввели (Андрей Емельянов)
            "admin",  # Резерв
        ]
        
        # Пароль по умолчанию для Андрея Емельянова
        default_password = "18031981asdF"
        
        for login_attempt in login_variants:
            # Используем введённый пароль или пароль по умолчанию
            password_to_use = self.password if self.password else default_password
            
            try:
                url = f"{SYNC_URL}/api/auth/login"
                headers = {'Content-Type': 'application/json'}
                data = json.dumps({"login": login_attempt, "password": password_to_use}).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    token = result.get('token')
                    
                    if token:
                        self._log(f"✅ Аутентификация успешна: {login_attempt}")
                        return token
                        
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    continue  # Пробуем следующий вариант
                else:
                    self._log(f"❌ HTTP ошибка {e.code}")
                    return None
            except Exception as e:
                self._log(f"❌ Ошибка: {type(e).__name__}: {e}")
                return None
        
        self._log("❌ Не удалось аутентифицироваться")
        return None

    def _api_request(self, endpoint, method='GET', data=None):
        """Выполняет запрос к серверу с авторизацией (Bearer Token)"""
        try:
            url = f"{SYNC_URL}{endpoint}"
            
            headers = {'Content-Type': 'application/json'}
            
            # Используем Bearer токен
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            else:
                self._log("❌ Нет токена авторизации")
                return None
            
            req = urllib.request.Request(url, method=method, headers=headers)
            
            if data:
                req.data = json.dumps(data).encode('utf-8')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._log("❌ Ошибка авторизации (401)")
                messagebox.showerror("Ошибка", "Сессия истекла. Войдите повторно.")
            elif e.code == 403:
                self._log("❌ Доступ запрещён (403)")
                messagebox.showerror("Ошибка", "Недостаточно прав")
            else:
                self._log(f"❌ HTTP ошибка: {e.code}")
            return None
        except urllib.error.URLError as e:
            self._log(f"❌ Ошибка подключения: {e.reason}")
            return None
        except Exception as e:
            self._log(f"❌ Ошибка: {type(e).__name__}: {e}")
            return None

    def _log(self, message):
        """Добавляет запись в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.status_var.set(message.replace("❌ ", "").replace("✅ ", ""))

    def _load_all_data(self):
        """Загружает все данные с сервера"""
        self.status_var.set("Загрузка данных...")
        self._log("🔄 Загрузка данных системы...")
        
        # Загружаем статистику (если есть доступ)
        stats = self._api_request('/api/admin/stats')
        
        if stats:
            self.stats_labels['users'].config(text=str(stats.get('overview', {}).get('total_users', 0)))
            self.stats_labels['trees'].config(text=str(stats.get('overview', {}).get('total_trees', 0)))
            self.stats_labels['persons'].config(text=str(stats.get('overview', {}).get('total_persons', 0)))
            self.stats_labels['active'].config(text=str(stats.get('overview', {}).get('active_users', 0)))
            self._log("✅ Статистика загружена")
        else:
            # Если нет доступа к админ API, показываем данные пользователя
            self._log("⚠️ Режим ограниченного доступа")
            self.stats_labels['users'].config(text="1")
            self.stats_labels['trees'].config(text="—")
            self.stats_labels['persons'].config(text="—")
            self.stats_labels['active'].config(text="1")
        
        # Загружаем пользователей (если есть доступ)
        users_response = self._api_request('/api/admin/users')

        # Сервер возвращает {"users": [...]}
        users_data = users_response.get('users', []) if isinstance(users_response, dict) else users_response
        
        if users_data and isinstance(users_data, list):
            self.all_users = users_data
            for user in users_data:
                login = user.get('login', 'Неизвестно')
                email = user.get('email', '-')
                created = user.get('created_at', '-')
                trees_count = user.get('trees_count', 0)
                is_active = user.get('is_active', True)
                last_sync = user.get('last_sync', 'Никогда')
                
                # Форматируем даты
                if created and created != '-':
                    try:
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        created = dt.strftime("%d.%m.%Y")
                    except:
                        pass
                
                if last_sync and last_sync != 'Никогда':
                    try:
                        dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        last_sync = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pass
                
                status = "✅ Активен" if is_active else "⚠️ Заблокирован"
                
                self.users_tree.insert('', tk.END, values=(
                    login, email, created, trees_count, status, last_sync
                ), tags=(user.get('id'),))
            
            self._log(f"✅ Загружено пользователей: {len(users_data)}")
        else:
            # Показываем только текущего пользователя
            self._log("⚠️ Показаны данные текущего пользователя")
            self.all_users = [{
                'id': 'current',
                'login': self.login,
                'email': '-',
                'created_at': '-',
                'trees_count': 0,
                'is_active': True,
                'last_sync': datetime.now().strftime("%Y-%m-%d %H:%M")
            }]
            self.users_tree.insert('', tk.END, values=(
                self.login, '-', '-', '0', '✅ Активен', datetime.now().strftime("%d.%m.%Y %H:%M")
            ))
        
        # Загружаем деревья (если есть доступ)
        self._load_all_trees()

    def _load_stats(self):
        """Загружает статистику системы"""
        stats = self._api_request('/api/admin/stats')
        
        if stats:
            self.stats_labels['users'].config(text=str(stats.get('total_users', 0)))
            self.stats_labels['trees'].config(text=str(stats.get('total_trees', 0)))
            self.stats_labels['persons'].config(text=str(stats.get('total_persons', 0)))
            self.stats_labels['active'].config(text=str(stats.get('active_users', 0)))
            self._log(f"✅ Статистика загружена")
        else:
            self._log("⚠️ Не удалось загрузить статистику")

    def _load_users(self):
        """Загружает список пользователей"""
        self.users_tree.delete(*self.users_tree.get_children())
        
        users_data = self._api_request('/api/admin/users')
        
        if users_data and isinstance(users_data, list):
            self.all_users = users_data
            
            for user in users_data:
                login = user.get('login', 'Неизвестно')
                email = user.get('email', '-')
                created = user.get('created_at', '-')
                trees_count = user.get('trees_count', 0)
                is_active = user.get('is_active', True)
                last_sync = user.get('last_sync', 'Никогда')
                
                # Форматируем даты
                if created and created != '-':
                    try:
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        created = dt.strftime("%d.%m.%Y")
                    except:
                        pass
                
                if last_sync and last_sync != 'Никогда':
                    try:
                        dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        last_sync = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pass
                
                status = "✅ Активен" if is_active else "⚠️ Заблокирован"
                
                self.users_tree.insert('', tk.END, values=(
                    login, email, created, trees_count, status, last_sync
                ), tags=(user.get('id'),))
            
            self._log(f"✅ Загружено пользователей: {len(users_data)}")
        else:
            self._log("⚠️ Не удалось загрузить пользователей")

    def _load_all_trees(self):
        """Загружает все деревья системы"""
        self.trees_tree.delete(*self.trees_tree.get_children())

        trees_response = self._api_request('/api/admin/trees')

        # Сервер возвращает {"trees": [...]}
        trees_data = trees_response.get('trees', []) if isinstance(trees_response, dict) else trees_response
        
        if trees_data and isinstance(trees_data, list):
            self.all_trees = trees_data
            
            for tree in trees_data:
                owner = tree.get('owner_login', 'Неизвестно')
                name = tree.get('name', 'Без названия')
                updated = tree.get('updated_at', 'Неизвестно')
                size = tree.get('size', 0)
                persons_count = tree.get('persons_count', 0)
                
                # Форматируем дату
                if updated and updated != 'Неизвестно':
                    try:
                        dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        updated = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pass
                
                # Форматируем размер
                if isinstance(size, (int, float)):
                    size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
                else:
                    size_str = str(size)
                
                self.trees_tree.insert('', tk.END, values=(
                    owner, name, updated, size_str, persons_count
                ), tags=(tree.get('id'),))
            
            self._log(f"✅ Загружено деревьев: {len(trees_data)}")
        else:
            self._log("⚠️ Не удалось загрузить деревья")

    def _get_selected_user_id(self):
        """Получает ID выбранного пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите пользователя")
            return None
        item = self.users_tree.item(selection[0])
        tags = item.get('tags')
        return tags[0] if tags else None

    def _get_selected_tree_id(self):
        """Получает ID выбранного дерева"""
        selection = self.trees_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите дерево")
            return None
        item = self.trees_tree.item(selection[0])
        tags = item.get('tags')
        return tags[0] if tags else None

    def _show_user_menu(self, event):
        """Показывает контекстное меню пользователя"""
        item = self.users_tree.identify_row(event.y)
        if item:
            self.users_tree.selection_set(item)
            self.user_menu.post(event.x_root, event.y_root)

    def _show_tree_menu(self, event):
        """Показывает контекстное меню дерева"""
        item = self.trees_tree.identify_row(event.y)
        if item:
            self.trees_tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def _view_user_trees(self):
        """Показывает деревья выбранного пользователя"""
        user_id = self._get_selected_user_id()
        if not user_id:
            return

        # Находим логин пользователя
        selection = self.users_tree.selection()
        if selection:
            item = self.users_tree.item(selection[0])
            login = item['values'][0]

            self._log(f"👁️ Просмотр деревьев пользователя: {login}")

            # Переключаемся на вкладку деревьев
            notebook = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[0].winfo_children()[0])
            for i, tab in enumerate(notebook.tabs()):
                if "Деревья" in notebook.tab(tab, "text"):
                    notebook.select(i)
                    break

            # Фильтруем деревья по пользователю
            self.trees_tree.delete(*self.trees_tree.get_children())
            
            # Находим деревья этого пользователя
            user_trees = [t for t in self.all_trees if t.get('user_login') == login or t.get('owner_login') == login]
            
            if not user_trees:
                messagebox.showinfo("Инфо", f"У пользователя {login} нет деревьев")
                self._load_all_trees()  # Возвращаем все деревья
                return
            
            for tree in user_trees:
                owner = tree.get('owner_login', tree.get('user_login', 'Неизвестно'))
                name = tree.get('name', 'Без названия')
                updated = tree.get('updated_at', 'Неизвестно')
                size = tree.get('size', 0)
                persons_count = len(tree.get('persons', {}))

                # Форматируем дату
                if updated and updated != 'Неизвестно':
                    try:
                        dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        updated = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pass

                # Форматируем размер
                if isinstance(size, (int, float)):
                    size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
                else:
                    size_str = str(size)

                self.trees_tree.insert('', tk.END, values=(
                    owner, name, updated, size_str, persons_count
                ), tags=(tree.get('id'),))

            self._log(f"✅ Показано деревьев пользователя {login}: {len(user_trees)}")
    
    def _open_user_full_tree(self):
        """Открывает полное дерево выбранного пользователя при двойном клике"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите пользователя")
            return
        
        item = self.users_tree.item(selection[0])
        login = item['values'][0]
        
        self._log(f"🌳 Открытие полного дерева пользователя: {login}")
        
        # Находим деревья этого пользователя
        user_trees = [t for t in self.all_trees if t.get('user_login') == login or t.get('owner_login') == login]
        
        if not user_trees:
            messagebox.showinfo("Инфо", f"У пользователя {login} нет деревьев")
            return
        
        # Если несколько деревьев, берём первое (или можно показать выбор)
        tree_data = user_trees[0]
        
        if len(user_trees) > 1:
            # Показываем диалог выбора дерева
            dialog = tk.Toplevel(self.root)
            dialog.title("Выберите дерево")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text=f"У пользователя {login} несколько деревьев:",
                     padding=10).pack()
            
            trees_listbox = tk.Listbox(dialog, width=50, height=10)
            trees_listbox.pack(padx=20, pady=10)
            
            for i, tree in enumerate(user_trees):
                trees_count = len(tree.get('persons', {}))
                trees_listbox.insert(tk.END, f"{tree.get('name', 'Без названия')} ({trees_count} персон)")
            
            def select_tree():
                sel = trees_listbox.curselection()
                if sel:
                    dialog.destroy()
                    self._show_full_tree_window(user_trees[sel[0]], login)
            
            ttk.Button(dialog, text="Открыть", command=select_tree).pack(pady=5)
            ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)
            
            trees_listbox.bind('<Double-Button-1>', lambda e: select_tree())
        else:
            self._show_full_tree_window(tree_data, login)
    
    def _show_full_tree_window(self, tree_data, owner_login):
        """Открывает главное приложение с деревом пользователя"""
        import subprocess
        import sys
        import os
        import json
        import tempfile
        
        self._log(f"🌳 Запуск просмотра дерева {owner_login}...")
        
        # Сохраняем данные дерева во временный файл в формате family_tree.json
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"family_tree_{owner_login}.json")
        
        # Подготовка данных в формате, совместимом с FamilyTreeModel
        save_data = {
            'persons': tree_data.get('persons', {}),
            'marriages': tree_data.get('marriages', []),
            'metadata': {
                'tree_name': tree_data.get('name', f'Дерево {owner_login}'),
                'owner': owner_login,
                'last_modified': datetime.now().isoformat()
            }
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # Определяем путь к исполняемому файлу
        if getattr(sys, 'frozen', False):
            # Запущено как .exe
            app_path = sys.executable
            args = [app_path, '--tree-file', temp_file, '--username', owner_login]
        else:
            # Запущено из исходников
            script_dir = os.path.dirname(os.path.abspath(__file__))
            main_py = os.path.normpath(os.path.join(script_dir, '..', 'main.py'))
            args = [sys.executable, main_py, '--tree-file', temp_file, '--username', owner_login]
        
        # Запускаем главное приложение
        subprocess.Popen(args)
        
        self._log(f"✅ Дерево {owner_login} открыто в новом окне")

    def _view_tree(self):
        """Просмотр выбранного дерева"""
        tree_id = self._get_selected_tree_id()
        if not tree_id:
            return

        # Находим дерево в списке
        selection = self.trees_tree.selection()
        if selection:
            item = self.trees_tree.item(selection[0])
            values = item['values']
            owner_login = values[0] if values else None
            tree_name = values[1] if len(values) > 1 else None

            self._log(f"👁️ Открытие дерева {tree_name} пользователя {owner_login}")

            # Находим полное дерево в all_trees
            tree_data = None
            for t in self.all_trees:
                if str(t.get('id')) == str(tree_id):
                    tree_data = t
                    break

            if tree_data:
                # Открываем главное приложение с графическим деревом
                self._show_full_tree_window(tree_data, owner_login)
            else:
                messagebox.showerror("Ошибка", "Не удалось найти данные дерева")

    def _download_tree(self):
        """Скачивает выбранное дерево"""
        tree_id = self._get_selected_tree_id()
        if not tree_id:
            return

        # Находим дерево в списке
        selection = self.trees_tree.selection()
        if selection:
            item = self.trees_tree.item(selection[0])
            values = item['values']
            owner_login = values[0] if values else None
            tree_name = values[1] if len(values) > 1 else 'Дерево'
            
            self._log(f"📥 Скачивание дерева {tree_name}...")
            
            # Находим полное дерево в all_trees
            tree_data = None
            for t in self.all_trees:
                if str(t.get('id')) == str(tree_id):
                    tree_data = t
                    break
            
            if tree_data:
                # Сохраняем дерево в файл
                import json
                from tkinter import filedialog
                
                # Предлагаем сохранить файл
                default_filename = f"{tree_name}_{owner_login}.json".replace(' ', '_')
                filename = filedialog.asksaveasfilename(
                    title="Сохранить дерево",
                    defaultextension=".json",
                    initialfile=default_filename,
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                
                if filename:
                    try:
                        # Подготовка данных в формате family_tree.json
                        save_data = {
                            'persons': tree_data.get('persons', {}),
                            'marriages': tree_data.get('marriages', []),
                            'metadata': {
                                'tree_name': tree_name,
                                'owner': owner_login,
                                'exported_from_admin_panel': True,
                                'export_date': datetime.now().isoformat()
                            }
                        }
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(save_data, f, ensure_ascii=False, indent=2)
                        
                        self._log(f"✅ Дерево сохранено: {filename}")
                        messagebox.showinfo("Успех", f"Дерево успешно сохранено:\n{filename}")
                        
                        # Открываем папку с файлом
                        import subprocess
                        subprocess.Popen(f'explorer /select,"{filename}"', shell=True)
                        
                    except Exception as e:
                        self._log(f"❌ Ошибка сохранения: {e}")
                        messagebox.showerror("Ошибка", f"Не удалось сохранить дерево:\n{e}")
            else:
                messagebox.showerror("Ошибка", "Не удалось найти данные дерева")

    def _delete_tree(self):
        """Удаляет выбранное дерево"""
        tree_id = self._get_selected_tree_id()
        if not tree_id:
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить дерево {tree_id}?\n\nЭто действие нельзя отменить!"):
            result = self._api_request(f'/api/admin/trees/{tree_id}', method='DELETE')
            if result:
                self._log(f"✅ Дерево удалено")
                self._load_all_trees()
            else:
                self._log("❌ Ошибка при удалении")

    def _reset_user_password(self):
        """Сбрасывает пароль пользователя"""
        user_id = self._get_selected_user_id()
        if not user_id:
            return
        
        if messagebox.askyesno("Подтверждение", "Сбросить пароль пользователя?\n\nПользователю будет отправлен новый пароль."):
            result = self._api_request(f'/api/admin/user/{user_id}/reset-password', method='POST')
            if result:
                self._log(f"✅ Пароль сброшен")
            else:
                self._log("❌ Ошибка при сбросе пароля")

    def _toggle_user_status(self):
        """Блокирует/разблокирует пользователя"""
        user_id = self._get_selected_user_id()
        if not user_id:
            return
        
        result = self._api_request(f'/api/admin/user/{user_id}/toggle', method='POST')
        if result:
            self._log(f"✅ Статус пользователя изменён")
            self._load_users()
        else:
            self._log("❌ Ошибка при изменении статуса")

    def _delete_user(self):
        """Удаляет пользователя"""
        user_id = self._get_selected_user_id()
        if not user_id:
            return
        
        selection = self.users_tree.selection()
        login = self.users_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {login}?\n\nВсе деревья будут удалены!"):
            result = self._api_request(f'/api/admin/user/{user_id}', method='DELETE')
            if result:
                self._log(f"✅ Пользователь {login} удалён")
                self._load_users()
            else:
                self._log("❌ Ошибка при удалении")


def open_admin_dashboard(login, password):
    """Открывает админ-панель"""
    dashboard_root = tk.Toplevel()
    dashboard = AdminDashboard(dashboard_root, login, password)
    dashboard_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    import sys
    login = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    
    open_admin_dashboard(login, password)
