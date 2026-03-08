# -*- coding: utf-8 -*-
"""
Админ-панель для просмотра статистики пользователей и их деревьев
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
from datetime import datetime

class AdminDashboard:
    """Панель администратора"""
    
    def __init__(self, root, server_url, admin_token):
        self.root = root
        self.server_url = server_url
        self.admin_token = admin_token

        self.root.title("👑 Админ-панель")
        self.root.geometry("1200x800")
        
        # Проверяем, тёмная ли тема
        import constants
        is_dark_theme = getattr(constants, 'WINDOW_BG', '#f8f9fa').lower() in ['#1e293b', '#0f172a', '#1a1a2e', '#16213e', '#2d3748', '#1a202c', '#2c3e50']
        
        if is_dark_theme:
            self.root.configure(bg='#1e293b')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('.', background='#1e293b', foreground='#ffffff')
            style.configure('TLabel', background='#1e293b', foreground='#ffffff')
            style.configure('TButton', background='#334155', foreground='#ffffff', font=('Arial', 10, 'bold'))
            style.configure('TEntry', fieldbackground='#334155', foreground='#ffffff')
            style.configure('Treeview', background='#1e293b', foreground='#ffffff', fieldbackground='#1e293b')
            style.configure('Treeview.Heading', background='#334155', foreground='#ffffff')
            style.configure('TNotebook', background='#1e293b')
            style.configure('TNotebook.Tab', background='#334155', foreground='#ffffff')
            style.map('TNotebook.Tab', background=[('selected', '#475569')])
            style.map('TButton', background=[('active', '#475568'), ('pressed', '#1e293b')])

        self.create_ui()
        self.load_stats()
    
    def create_ui(self):
        """Создать интерфейс"""
        # Заголовок
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header, text="👑 Админ-панель", 
                 font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(header, text="🔄 Обновить", 
                  command=self.load_stats).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(header, text="❌ Закрыть", 
                  command=self.root.destroy).pack(side=tk.RIGHT)
        
        # Вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Вкладка 1: Общая статистика
        self.stats_frame = ttk.Frame(notebook)
        notebook.add(self.stats_frame, text="📊 Статистика")
        
        # Вкладка 2: Пользователи
        self.users_frame = ttk.Frame(notebook)
        notebook.add(self.users_frame, text="👥 Пользователи")
        
        # Вкладка 3: Деревья
        self.trees_frame = ttk.Frame(notebook)
        notebook.add(self.trees_frame, text="🌳 Деревья")
        
        self.create_stats_tab()
        self.create_users_tab()
        self.create_trees_tab()
    
    def create_stats_tab(self):
        """Вкладка статистики"""
        # Карточки статистики
        cards_frame = ttk.Frame(self.stats_frame)
        cards_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.stat_cards = {}
        stats = [
            ("total_users", "👥 Пользователей", "blue"),
            ("active_users", "✅ Активных", "green"),
            ("total_trees", "🌳 Деревьев", "orange"),
            ("total_persons", "👤 Персон", "purple"),
            ("active_sessions", "🔐 Сессий", "red"),
        ]
        
        for i, (key, label, color) in enumerate(stats):
            card = ttk.LabelFrame(cards_frame, text=label, padding=20)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            value_label = ttk.Label(card, text="-", 
                                   font=("Segoe UI", 24, "bold"),
                                   foreground=color)
            value_label.pack()
            
            self.stat_cards[key] = value_label
        
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)
        cards_frame.columnconfigure(4, weight=1)
        
        # График по дням
        chart_frame = ttk.LabelFrame(self.stats_frame, text="📈 Активность по дням", padding=20)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.chart_text = tk.Text(chart_frame, height=10, font=("Consolas", 10))
        self.chart_text.pack(fill=tk.BOTH, expand=True)
    
    def create_users_tab(self):
        """Вкладка пользователей"""
        # Таблица пользователей
        columns = ("login", "email", "created", "last_login", "trees", "status")
        
        tree = ttk.Treeview(self.users_frame, columns=columns, show="headings", height=20)
        
        tree.heading("login", text="Логин")
        tree.heading("email", text="Email")
        tree.heading("created", text="Дата регистрации")
        tree.heading("last_login", text="Последний вход")
        tree.heading("trees", text="Деревьев")
        tree.heading("status", text="Статус")
        
        tree.column("login", width=150)
        tree.column("email", width=200)
        tree.column("created", width=120)
        tree.column("last_login", width=120)
        tree.column("trees", width=80)
        tree.column("status", width=80)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.users_tree = tree
        
        # Кнопки действий
        btn_frame = ttk.Frame(self.users_frame)
        btn_frame.pack(padx=20, pady=10)
        
        ttk.Button(btn_frame, text="🌳 Показать деревья", 
                  command=self.show_user_trees).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔓 Сбросить пароль", 
                  command=self.reset_user_password).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="⚠️ Заблокировать", 
                  command=self.toggle_user_status).pack(side=tk.LEFT, padx=5)
    
    def create_trees_tab(self):
        """Вкладка деревьев"""
        # Таблица деревьев
        columns = ("user", "name", "persons", "created", "updated")
        
        tree = ttk.Treeview(self.trees_frame, columns=columns, show="headings", height=20)
        
        tree.heading("user", text="Пользователь")
        tree.heading("name", text="Название")
        tree.heading("persons", text="Персон")
        tree.heading("created", text="Создано")
        tree.heading("updated", text="Обновлено")
        
        tree.column("user", width=150)
        tree.column("name", width=200)
        tree.column("persons", width=80)
        tree.column("created", width=120)
        tree.column("updated", width=120)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.trees_tree = tree
        
        # Кнопки действий
        btn_frame = ttk.Frame(self.trees_frame)
        btn_frame.pack(padx=20, pady=10)
        
        ttk.Button(btn_frame, text="👁️ Просмотреть дерево", 
                  command=self.view_tree).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="💾 Скачать JSON", 
                  command=self.download_tree).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🗑️ Удалить дерево", 
                  command=self.delete_tree).pack(side=tk.LEFT, padx=5)
    
    def api_request(self, endpoint, method='GET', data=None):
        """API запрос к серверу"""
        url = f"{self.server_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        body = None
        if data:
            body = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            messagebox.showerror("Ошибка API", str(e))
            return None
    
    def load_stats(self):
        """Загрузить статистику"""
        stats = self.api_request('/api/admin/stats')
        
        if not stats:
            return
        
        # Обновить карточки
        overview = stats.get('overview', {})
        
        for key, label in self.stat_cards.items():
            value = overview.get(key, 0)
            label.config(text=str(value))
        
        # Обновить график
        self.chart_text.delete('1.0', tk.END)
        daily_stats = stats.get('daily_stats', [])
        
        if daily_stats:
            self.chart_text.insert(tk.END, "Дата\t\tСинхронизаций\tПерсон\n")
            self.chart_text.insert(tk.END, "=" * 50 + "\n")
            
            for day in daily_stats[:10]:  # Последние 10 дней
                date = day.get('date', 'N/A')
                sync_count = day.get('sync_count', 0)
                total_entities = day.get('total_entities', 0)
                self.chart_text.insert(tk.END, f"{date}\t{sync_count}\t\t{total_entities}\n")
        
        # Загрузить пользователей
        self.load_users()
        
        # Загрузить деревья
        self.load_trees()
    
    def load_users(self):
        """Загрузить список пользователей"""
        users_data = self.api_request('/api/admin/users')
        
        if not users_data:
            return
        
        # Очистить таблицу
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Добавить пользователей
        for user in users_data.get('users', []):
            login = user.get('login', 'N/A')
            email = user.get('email', 'N/A')
            created = user.get('created_at', 'N/A')[:10] if user.get('created_at') else 'N/A'
            last_login = user.get('last_login', 'N/A')[:19] if user.get('last_login') else 'Никогда'
            is_active = "✅" if user.get('is_active') else "❌"
            is_admin = "👑" if user.get('is_admin') else ""
            
            # Получаем количество деревьев
            trees_count = len(self.api_request(f'/api/admin/user/{user.get("id")}/trees') or {})
            
            self.users_tree.insert('', tk.END, values=(
                f"{login} {is_admin}",
                email,
                created,
                last_login,
                trees_count,
                is_active
            ), tags=(user.get('id'),))
    
    def load_trees(self):
        """Загрузить список деревьев"""
        # Пока заглушка - нужно добавить API endpoint
        pass
    
    def show_user_trees(self):
        """Показать деревья пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        # Получить ID пользователя из tags
        item = self.users_tree.item(selection[0])
        user_id = item['tags'][0] if item['tags'] else None
        
        if not user_id:
            return
        
        # Запросить деревья пользователя
        trees = self.api_request(f'/api/admin/user/{user_id}/trees')
        
        if trees:
            messagebox.showinfo("Деревья пользователя", json.dumps(trees, indent=2, ensure_ascii=False))
        else:
            messagebox.showinfo("Деревья", "У пользователя нет деревьев")
    
    def reset_user_password(self):
        """Сбросить пароль пользователя"""
        messagebox.showinfo("Инфо", "Функция в разработке")
    
    def toggle_user_status(self):
        """Заблокировать/разблокировать пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        # API запрос на блокировку
        item = self.users_tree.item(selection[0])
        user_id = item['tags'][0] if item['tags'] else None
        
        if user_id:
            result = self.api_request(f'/api/admin/user/{user_id}/toggle', method='POST')
            if result:
                messagebox.showinfo("Успех", "Статус пользователя изменён")
                self.load_stats()
    
    def view_tree(self):
        """Просмотреть дерево"""
        messagebox.showinfo("Инфо", "Функция в разработке")
    
    def download_tree(self):
        """Скачать дерево"""
        messagebox.showinfo("Инфо", "Функция в разработке")
    
    def delete_tree(self):
        """Удалить дерево"""
        messagebox.showinfo("Инфо", "Функция в разработке")


def open_admin_dashboard(server_url, login, password):
    """Открыть админ-панель"""
    
    # Логин администратора
    try:
        req = urllib.request.Request(
            f"{server_url}/api/auth/login",
            data=json.dumps({"login": login, "password": password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')
            
            if token:
                # Открыть админ-панель
                admin_root = tk.Toplevel()
                AdminDashboard(admin_root, server_url, token)
            else:
                messagebox.showerror("Ошибка", "Не удалось получить токен")
    
    except Exception as e:
        messagebox.showerror("Ошибка входа", str(e))
