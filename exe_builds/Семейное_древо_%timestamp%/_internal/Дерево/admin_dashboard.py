# -*- coding: utf-8 -*-
"""
Админ-панель для просмотра статистики пользователей и их деревьев
Работает с ЛОКАЛЬНЫМИ файлами
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import urllib.request
from datetime import datetime
import glob

class AdminDashboard:
    """Панель администратора"""
    
    def __init__(self, root, server_url, admin_token):
        self.root = root
        self.server_url = server_url
        self.admin_token = admin_token
        
        self.root.title("👑 Админ-панель")
        self.root.geometry("1200x800")
        
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

        self.create_stats_tab()
        self.create_users_tab()
    
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
        columns = ("login", "email", "created", "last_login", "status")

        tree = ttk.Treeview(self.users_frame, columns=columns, show="headings", height=20)

        tree.heading("login", text="Логин")
        tree.heading("email", text="Email")
        tree.heading("created", text="Дата регистрации")
        tree.heading("last_login", text="Последний вход")
        tree.heading("status", text="Статус")

        tree.column("login", width=150)
        tree.column("email", width=200)
        tree.column("created", width=120)
        tree.column("last_login", width=120)
        tree.column("status", width=80)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.users_tree = tree
        
        # Кнопки действий
        btn_frame = ttk.Frame(self.users_frame)
        btn_frame.pack(padx=20, pady=10)

        ttk.Button(btn_frame, text="🔓 Сбросить пароль",
                  command=self.reset_user_password).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="⚠️ Заблокировать",
                  command=self.toggle_user_status).pack(side=tk.LEFT, padx=5)

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
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            print(f"[API ERROR] {endpoint}: HTTP {e.code} - {error_body}")
            # Если токен истёк, пробуем обновить
            if e.code == 401 or e.code == 403:
                messagebox.showwarning("Токен истёк", 
                    "Ваша сессия истекла. Закройте админ-панель и войдите снова.")
            else:
                messagebox.showerror("Ошибка API", f"HTTP {e.code}: {e.reason}\n\n{error_body}")
            return None
        except Exception as e:
            print(f"[API ERROR] {endpoint}: {e}")
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

            self.users_tree.insert('', tk.END, values=(
                f"{login} {is_admin}",
                email,
                created,
                last_login,
                is_active
            ), tags=(user.get('id'),))
    
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

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        messagebox.showerror("Ошибка входа", f"HTTP {e.code}: {e.reason}\n\n{error_body}")
    except Exception as e:
        messagebox.showerror("Ошибка входа", str(e))
