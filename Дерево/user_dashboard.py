# -*- coding: utf-8 -*-
"""
Персональная панель пользователя.
Данные подтягиваются с сервера синхронизации.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import urllib.request
import urllib.error

# URL сервера
SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"


class UserDashboard:
    """Персональная панель пользователя с данными с сервера"""

    def __init__(self, root, login, password):
        self.root = root
        self.login = login
        self.password = password
        self.token = None
        
        self.root.title(f"👤 Панель пользователя — {login}")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2c3e50')
        style.configure('SubHeader.TLabel', font=('Segoe UI', 12), foreground='#7f8c8d')
        style.configure('Stat.TLabel', font=('Segoe UI', 14), foreground='#34495e')
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Warning.TLabel', foreground='#e67e22')
        style.configure('Danger.TLabel', foreground='#e74c3c')
        
        self._setup_ui()
        
        # Загружаем данные после отображения окна
        self.root.after(100, self._load_user_data)

    def _setup_ui(self):
        """Создаёт интерфейс панели"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === ШАПКА ===
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 20))
        
        self.header_label = ttk.Label(header, text=f"Загрузка...", style='Header.TLabel')
        self.header_label.pack(anchor=tk.W)
        
        self.subheader_label = ttk.Label(header, text="", style='SubHeader.TLabel')
        self.subheader_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Кнопка обновления
        self.refresh_btn = ttk.Button(header, text="🔄 Обновить", command=self._load_user_data)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # === СТАТИСТИКА (3 колонки) ===
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.stats_cards = {}
        
        # Карточка 1: Деревья
        card1 = ttk.LabelFrame(stats_frame, text="🌳 Деревья", padding=15)
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.stats_cards['trees'] = ttk.Label(card1, text="—", style='Stat.TLabel')
        self.stats_cards['trees'].pack()
        
        # Карточка 2: Персоны
        card2 = ttk.LabelFrame(stats_frame, text="👥 Персоны", padding=15)
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10))
        self.stats_cards['persons'] = ttk.Label(card2, text="—", style='Stat.TLabel')
        self.stats_cards['persons'].pack()
        
        # Карточка 3: Последняя активность
        card3 = ttk.LabelFrame(stats_frame, text="🕐 Последняя активность", padding=15)
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.stats_cards['last_activity'] = ttk.Label(card3, text="—", style='Stat.TLabel')
        self.stats_cards['last_activity'].pack()
        
        # === СПИСОК ДЕРЕВЬЕВ ===
        trees_frame = ttk.LabelFrame(main_frame, text="📁 Ваши деревья", padding=15)
        trees_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Таблица деревьев
        columns = ('name', 'updated', 'size', 'status')
        self.trees_tree = ttk.Treeview(trees_frame, columns=columns, show='headings', height=12)
        
        self.trees_tree.heading('name', text='Название')
        self.trees_tree.heading('updated', text='Обновлено')
        self.trees_tree.heading('size', text='Размер')
        self.trees_tree.heading('status', text='Статус')
        
        self.trees_tree.column('name', width=300)
        self.trees_tree.column('updated', width=150)
        self.trees_tree.column('size', width=100)
        self.trees_tree.column('status', width=120)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(trees_frame, orient=tk.VERTICAL, command=self.trees_tree.yview)
        self.trees_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trees_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки действий
        tree_btn_frame = ttk.Frame(main_frame)
        tree_btn_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Button(tree_btn_frame, text="📥 Скачать", command=self._download_tree).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tree_btn_frame, text="📤 Загрузить", command=self._upload_tree).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tree_btn_frame, text="🗑️ Удалить", command=self._delete_tree).pack(side=tk.LEFT)
        
        # === ЛОГ ОПЕРАЦИЙ ===
        log_frame = ttk.LabelFrame(main_frame, text="📋 Журнал операций", padding=10)
        log_frame.pack(fill=tk.X)
        
        self.log_text = tk.Text(log_frame, height=4, wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(fill=tk.X)
        
        # === СТАТУС БАР ===
        self.status_var = tk.StringVar(value="Готово")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def _api_request(self, endpoint, method='GET', data=None):
        """Выполняет запрос к серверу с авторизацией"""
        try:
            url = f"{SYNC_URL}{endpoint}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Добавляем токен или базовую авторизацию
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            else:
                # Используем логин/пароль для авторизации
                import base64
                credentials = base64.b64encode(f"{self.login}:{self.password}".encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
            
            req = urllib.request.Request(url, method=method, headers=headers)
            
            if data:
                req.data = json.dumps(data).encode('utf-8')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._log("❌ Ошибка авторизации")
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
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

    def _load_user_data(self):
        """Загружает данные пользователя с сервера"""
        self.status_var.set("Загрузка данных...")
        self._log("🔄 Загрузка данных пользователя...")
        
        # Получаем статистику пользователя
        stats = self._api_request('/api/user/stats')
        
        if stats:
            self.header_label.config(text=f"👤 {self.login}")
            self.subheader_label.config(text=f"Персональная панель")
            
            # Обновляем статистику
            trees_count = stats.get('trees_count', 0)
            persons_count = stats.get('persons_count', 0)
            last_sync = stats.get('last_sync', 'Никогда')
            
            self.stats_cards['trees'].config(text=str(trees_count))
            self.stats_cards['persons'].config(text=str(persons_count))
            
            if last_sync and last_sync != 'Никогда':
                try:
                    # Форматируем дату
                    dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    formatted = dt.strftime("%d.%m.%Y %H:%M")
                    self.stats_cards['last_activity'].config(text=formatted)
                except:
                    self.stats_cards['last_activity'].config(text=last_sync)
            else:
                self.stats_cards['last_activity'].config(text="Никогда")
            
            self._log(f"✅ Данные загружены: {trees_count} деревьев, {persons_count} персон")
        else:
            self.header_label.config(text=f"👤 {self.login}")
            self.subheader_label.config(text="Не удалось загрузить данные")
            self._log("❌ Не удалось загрузить данные")
        
        # Загружаем список деревьев
        self._load_trees()

    def _load_trees(self):
        """Загружает список деревьев пользователя"""
        self.trees_tree.delete(*self.trees_tree.get_children())
        
        trees = self._api_request('/api/user/trees')
        
        if trees and isinstance(trees, list):
            for tree in trees:
                name = tree.get('name', 'Без названия')
                updated = tree.get('updated_at', 'Неизвестно')
                size = tree.get('size', 0)
                status = tree.get('status', 'active')
                
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
                
                # Статус
                status_str = "✅ Активно" if status == 'active' else "⚠️ Архив"
                
                self.trees_tree.insert('', tk.END, values=(name, updated, size_str, status_str), tags=(tree.get('id'),))
            
            self._log(f"✅ Загружено деревьев: {len(trees)}")
        else:
            self._log("⚠️ Деревья не найдены или ошибка загрузки")

    def _get_selected_tree_id(self):
        """Получает ID выбранного дерева"""
        selection = self.trees_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите дерево из списка")
            return None
        item = self.trees_tree.item(selection[0])
        tags = item.get('tags')
        return tags[0] if tags else None

    def _download_tree(self):
        """Скачивает выбранное дерево"""
        tree_id = self._get_selected_tree_id()
        if not tree_id:
            return
        
        self._log(f"📥 Скачивание дерева {tree_id}...")
        # TODO: Реализовать скачивание
        messagebox.showinfo("Инфо", "Функция скачивания в разработке")

    def _upload_tree(self):
        """Загружает дерево на сервер"""
        self._log("📤 Загрузка дерева...")
        # TODO: Реализовать загрузку
        messagebox.showinfo("Инфо", "Функция загрузки в разработке")

    def _delete_tree(self):
        """Удаляет выбранное дерево"""
        tree_id = self._get_selected_tree_id()
        if not tree_id:
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить дерево {tree_id}?\n\nЭто действие нельзя отменить!"):
            result = self._api_request(f'/api/user/trees/{tree_id}', method='DELETE')
            if result:
                self._log(f"✅ Дерево удалено")
                self._load_trees()
            else:
                self._log("❌ Ошибка при удалении")


def open_user_dashboard(login, password):
    """Открывает персональную панель пользователя"""
    dashboard_root = tk.Toplevel()
    dashboard = UserDashboard(dashboard_root, login, password)
    
    # Делаем окно модальным (опционально)
    # dashboard_root.transient(tk._default_root)
    # dashboard_root.grab_set()
    
    dashboard_root.mainloop()


# Для тестирования
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # Тест с демо-данными
    import sys
    login = sys.argv[1] if len(sys.argv) > 1 else "Андрей Емельянов"
    password = sys.argv[2] if len(sys.argv) > 2 else "demo"
    
    open_user_dashboard(login, password)
