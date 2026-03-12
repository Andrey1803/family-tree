# -*- coding: utf-8 -*-
"""
Админ-панель для работы с сервером
Показывает всех пользователей, их деревья и статистику
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
import os
from datetime import datetime

SERVER_URL = "https://ravishing-caring-production-3656.up.railway.app"


class ServerAdminDashboard:
    """Админ-панель с подключением к серверу"""

    def __init__(self, root, login, password):
        self.root = root
        self.root.title("👑 Админ-панель (Сервер)")
        self.root.geometry("1400x900")

        self.server_url = SERVER_URL
        self.token = None
        self.users_data = []
        self.trees_data = []

        # Вход на сервер
        if self.login(login, password):
            self.create_ui()
            self.load_all_data()
        else:
            messagebox.showerror("Ошибка", "Не удалось войти на сервер")
            self.root.destroy()

    def login(self, login, password):
        """Войти на сервер как администратор"""
        try:
            req = urllib.request.Request(
                f"{self.server_url}/api/auth/login",
                data=json.dumps({"login": login, "password": password}).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                self.token = data.get('token')
                self.user_id = data.get('user_id')
                return bool(self.token)
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def api_request(self, endpoint, method='GET', data=None):
        """API запрос к серверу"""
        url = f"{self.server_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        body = None
        if data:
            body = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            print(f"[API ERROR] {endpoint}: HTTP {e.code} - {error_body}")
            messagebox.showerror("Ошибка API", f"HTTP {e.code}: {e.reason}")
            return None
        except Exception as e:
            print(f"[API ERROR] {endpoint}: {e}")
            messagebox.showerror("Ошибка API", str(e))
            return None

    def create_ui(self):
        """Создать интерфейс"""
        # Заголовок
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(header, text="👑 Админ-панель (Сервер)",
                 font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="🔄 Обновить",
                  command=self.load_all_data).pack(side=tk.RIGHT, padx=5)

        ttk.Button(header, text="❌ Закрыть",
                  command=self.root.destroy).pack(side=tk.RIGHT, padx=5)

        # Вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Вкладка 1: Статистика
        self.stats_frame = ttk.Frame(notebook)
        notebook.add(self.stats_frame, text="📊 Статистика")
        self.create_stats_tab()

        # Вкладка 2: Пользователи
        self.users_frame = ttk.Frame(notebook)
        notebook.add(self.users_frame, text="👥 Пользователи")
        self.create_users_tab()

        # Вкладка 3: Деревья
        self.trees_frame = ttk.Frame(notebook)
        notebook.add(self.trees_frame, text="🌳 Деревья")
        self.create_trees_tab()

    def create_stats_tab(self):
        """Вкладка статистики"""
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
            cards_frame.columnconfigure(i, weight=1)

            value_label = ttk.Label(card, text="-", font=("Segoe UI", 24, "bold"))
            value_label.pack()
            self.stat_cards[key] = value_label

        # График
        chart_frame = ttk.LabelFrame(self.stats_frame, text="📈 Активность по дням", padding=20)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.chart_text = tk.Text(chart_frame, height=10, font=("Consolas", 10))
        self.chart_text.pack(fill=tk.BOTH, expand=True)

    def create_users_tab(self):
        """Вкладка пользователей"""
        # Таблица
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
        tree.column("last_login", width=150)
        tree.column("trees", width=80, anchor=tk.CENTER)
        tree.column("status", width=80, anchor=tk.CENTER)

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.users_tree = tree

        # Кнопки
        btn_frame = ttk.Frame(self.users_frame)
        btn_frame.pack(padx=20, pady=10)

        ttk.Button(btn_frame, text="🌳 Показать деревья",
                  command=self.show_user_trees).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="⚠️ Заблокировать",
                  command=self.toggle_user_status).pack(side=tk.LEFT, padx=5)

    def create_trees_tab(self):
        """Вкладка деревьев"""
        # Таблица деревьев
        columns = ("user", "name", "persons", "marriages", "updated")

        tree = ttk.Treeview(self.trees_frame, columns=columns, show="headings", height=20)

        tree.heading("user", text="Пользователь")
        tree.heading("name", text="Название")
        tree.heading("persons", text="Персон")
        tree.heading("marriages", text="Браков")
        tree.heading("updated", text="Обновлено")

        tree.column("user", width=150)
        tree.column("name", width=200)
        tree.column("persons", width=80, anchor=tk.CENTER)
        tree.column("marriages", width=80, anchor=tk.CENTER)
        tree.column("updated", width=150)

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.trees_tree = tree

        # Кнопки
        btn_frame = ttk.Frame(self.trees_frame)
        btn_frame.pack(padx=20, pady=10)

        ttk.Button(btn_frame, text="👁️ Просмотреть",
                  command=self.view_tree).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="💾 Скачать JSON",
                  command=self.download_tree).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="🗑️ Удалить",
                  command=self.delete_tree).pack(side=tk.LEFT, padx=5)

    def load_all_data(self):
        """Загрузить все данные"""
        self.load_stats()
        self.load_users()
        self.load_trees()

    def load_stats(self):
        """Загрузить статистику"""
        stats = self.api_request('/api/admin/stats')

        if not stats:
            return

        overview = stats.get('overview', {})

        for key, label in self.stat_cards.items():
            value = overview.get(key, 0)
            label.config(text=str(value))

        # График
        self.chart_text.delete('1.0', tk.END)
        daily_stats = stats.get('daily_stats', [])

        if daily_stats:
            self.chart_text.insert(tk.END, "Дата\t\tСинхронизаций\tПерсон\n")
            self.chart_text.insert(tk.END, "=" * 50 + "\n")

            for day in daily_stats[:10]:
                date = day.get('date', 'N/A')
                sync_count = day.get('sync_count', 0)
                total_entities = day.get('total_entities', 0)
                self.chart_text.insert(tk.END, f"{date}\t{sync_count}\t\t{total_entities}\n")

    def load_users(self):
        """Загрузить пользователей"""
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
                "?",  # Количество деревьев (будет загружено отдельно)
                is_active
            ), tags=(user.get('id'),))

    def load_trees(self):
        """Загрузить деревья всех пользователей"""
        # Получаем всех пользователей
        users_data = self.api_request('/api/admin/users')
        if not users_data:
            return

        # Очищаем таблицу
        for item in self.trees_tree.get_children():
            self.trees_tree.delete(item)

        # Для каждого пользователя загружаем деревья
        for user in users_data.get('users', []):
            user_id = user.get('id')
            username = user.get('login', 'Unknown')

            # Загружаем деревья пользователя (теперь endpoint работает!)
            trees = self.api_request(f'/api/admin/user/{user_id}/trees')

            if trees and 'trees' in trees:
                for tree in trees.get('trees', []):
                    tree_name = tree.get('name', 'Без названия')
                    persons_count = len(tree.get('persons', {}))
                    marriages_count = len(tree.get('marriages', []))
                    updated = tree.get('updated_at', 'N/A')[:19] if tree.get('updated_at') else 'N/A'

                    self.trees_tree.insert('', tk.END, values=(
                        username,
                        tree_name,
                        persons_count,
                        marriages_count,
                        updated
                    ), tags=(json.dumps(tree),))
            else:
                # Деревьев нет
                self.trees_tree.insert('', tk.END, values=(
                    username,
                    "Нет деревьев",
                    0,
                    0,
                    "N/A"
                ))

    def show_user_trees(self):
        """Показать деревья пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return

        item = self.users_tree.item(selection[0])
        tags = item['tags']
        if not tags:
            return

        user_id = tags[0]
        username = item['values'][0]

        # Переходим на вкладку деревьев и фильтруем
        messagebox.showinfo("Инфо", f"Деревья пользователя {username}\n\nПерейдите на вкладку 'Деревья' для просмотра")

    def toggle_user_status(self):
        """Заблокировать/разблокировать пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return

        item = self.users_tree.item(selection[0])
        tags = item['tags']
        user_id = tags[0] if tags else None

        if user_id:
            result = self.api_request(f'/api/admin/user/{user_id}/toggle', method='POST')
            if result:
                messagebox.showinfo("Успех", "Статус пользователя изменён")
                self.load_users()

    def view_tree(self):
        """Просмотреть дерево"""
        selection = self.trees_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите дерево")
            return

        item = self.trees_tree.item(selection[0])
        tags = item['tags']
        if not tags:
            return

        tree_json_str = tags[0]
        tree_data = json.loads(tree_json_str)

        # Создаём окно просмотра
        viewer = tk.Toplevel(self.root)
        viewer.title(f"🌳 Дерево: {tree_data.get('name', 'Без названия')}")
        viewer.geometry("1024x768")

        # Информация
        info_frame = ttk.Frame(viewer)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        persons_count = len(tree_data.get('persons', {}))
        marriages_count = len(tree_data.get('marriages', []))

        ttk.Label(info_frame, text=f"📊 Персон: {persons_count}  |  💍 Браков: {marriages_count}",
                 font=("Segoe UI", 12)).pack(side=tk.LEFT)

        ttk.Button(info_frame, text="❌ Закрыть",
                  command=viewer.destroy).pack(side=tk.RIGHT)

        # Список персон
        tree_frame = ttk.Frame(viewer)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "name", "gender", "birth_date")

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=30)

        tree.heading("id", text="ID")
        tree.heading("name", text="ФИО")
        tree.heading("gender", text="Пол")
        tree.heading("birth_date", text="Дата рождения")

        tree.column("id", width=50)
        tree.column("name", width=400)
        tree.column("gender", width=80)
        tree.column("birth_date", width=120)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Добавить персон
        persons = tree_data.get('persons', {})
        for pid, person in sorted(persons.items()):
            name = f"{person.get('surname', '')} {person.get('name', '')} {person.get('patronymic', '')}".strip()
            gender = person.get('gender', '')
            birth_date = person.get('birth_date', '')

            tree.insert('', tk.END, values=(pid, name, gender, birth_date))

    def download_tree(self):
        """Скачать дерево"""
        selection = self.trees_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите дерево")
            return

        item = self.trees_tree.item(selection[0])
        tags = item['tags']
        if not tags:
            return

        tree_json_str = tags[0]
        tree_data = json.loads(tree_json_str)

        # Диалог сохранения
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"tree_{tree_data.get('name', 'export')}.json"
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"Дерево сохранено в:\n{filename}")

    def delete_tree(self):
        """Удалить дерево"""
        messagebox.showinfo("Инфо", "Функция удаления будет доступна в следующей версии")


def open_server_admin_dashboard(login="admin", password="admin123", skip_dialog=False):
    """Открыть серверную админ-панель"""
    if skip_dialog or (login and password):
        # Прямой вход без диалога
        admin_root = tk.Toplevel()
        ServerAdminDashboard(admin_root, login, password)
    else:
        # Диалог ввода пароля
        dialog = tk.Toplevel()
        dialog.title("👑 Вход администратора")
        dialog.geometry("400x250")
        dialog.transient(tk._default_root)
        dialog.grab_set()

        ttk.Label(dialog, text="Введите данные администратора",
                 font=("Segoe UI", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(dialog, padding=20)
        frame.pack()

        # Логин
        ttk.Label(frame, text="Логин:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        login_var = tk.StringVar(value=login)
        ttk.Entry(frame, textvariable=login_var, width=30).grid(row=0, column=1, padx=10, pady=5)

        # Пароль
        ttk.Label(frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=password_var, show="*", width=30).grid(row=1, column=1, padx=10, pady=5)

        def do_open():
            l = login_var.get()
            p = password_var.get()
            dialog.destroy()
            admin_root = tk.Toplevel()
            ServerAdminDashboard(admin_root, l, p)

        ttk.Button(dialog, text="Войти", command=do_open).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
