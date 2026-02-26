# -*- coding: utf-8 -*-
"""
Модуль синхронизации для desktop-приложения "Семейное древо".
Синхронизация с сервером через REST API.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime

# Настройки сервера по умолчанию
DEFAULT_SERVER_URL = "https://family-tree-server.herokuapp.com"
CONFIG_FILE = "sync_config.json"


class SyncClient:
    """Клиент для синхронизации с сервером."""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or self._load_server_url()
        self.token = self._load_token()
        self.user_id = None
    
    def _load_server_url(self):
        """Загрузить URL сервера из конфига."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('server_url', DEFAULT_SERVER_URL)
            except:
                pass
        return DEFAULT_SERVER_URL
    
    def _save_server_url(self, url):
        """Сохранить URL сервера в конфиг."""
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        
        config['server_url'] = url
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.server_url = url
    
    def _load_token(self):
        """Загрузить токен из конфига."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('token')
            except:
                pass
        return None
    
    def _save_token(self, token, user_id=None):
        """Сохранить токен в конфиг."""
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        
        config['token'] = token
        if user_id:
            config['user_id'] = user_id
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.token = token
        self.user_id = user_id
    
    def _request(self, endpoint, method='GET', data=None):
        """Выполнить HTTP запрос к серверу."""
        url = f"{self.server_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        body = None
        if data:
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get('error', str(e))
            except:
                error_msg = str(e)
            raise Exception(f"HTTP {e.code}: {error_msg}")
        except urllib.error.URLError as e:
            raise Exception(f"Ошибка соединения: {e.reason}")
        except Exception as e:
            raise Exception(f"Ошибка запроса: {str(e)}")
    
    # === АУТЕНТИФИКАЦИЯ ===
    def register(self, login, password, email=''):
        """Зарегистрировать нового пользователя."""
        result = self._request('/api/auth/register', method='POST', data={
            'login': login,
            'password': password,
            'email': email
        })
        return result
    
    def login(self, login, password):
        """Войти в систему."""
        result = self._request('/api/auth/login', method='POST', data={
            'login': login,
            'password': password
        })
        
        if 'token' in result:
            self._save_token(result['token'], result.get('user_id'))
        
        return result
    
    def logout(self):
        """Выйти из системы."""
        try:
            self._request('/api/auth/logout', method='POST')
        except:
            pass
        
        self.token = None
        self.user_id = None
        
        # Удаляем токен из конфига
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if 'token' in config:
                    del config['token']
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            except:
                pass
    
    def is_logged_in(self):
        """Проверить, авторизован ли пользователь."""
        return self.token is not None
    
    # === СИНХРОНИЗАЦИЯ ===
    def upload_tree(self, tree_data, tree_name='Моё дерево'):
        """Загрузить дерево на сервер."""
        if not self.token:
            raise Exception("Требуется авторизация")
        
        result = self._request('/api/sync/upload', method='POST', data={
            'tree': tree_data,
            'tree_name': tree_name
        })
        
        return result
    
    def download_tree(self):
        """Скачать дерево с сервера."""
        if not self.token:
            raise Exception("Требуется авторизация")
        
        result = self._request('/api/sync/download')
        return result
    
    def sync(self, model, tree_name='Моё дерево'):
        """
        Полная синхронизация: загрузка локальных данных на сервер.
        
        Args:
            model: FamilyTreeModel для экспорта данных
            tree_name: Название дерева
        """
        # Собираем данные для отправки
        tree_data = {
            'persons': {},
            'marriages': []
        }
        
        # Экспорт персон
        for pid, person in model.get_all_persons().items():
            tree_data['persons'][pid] = {
                'name': person.name,
                'surname': person.surname,
                'patronymic': person.patronymic or '',
                'birth_date': person.birth_date or '',
                'death_date': person.death_date or '',
                'is_deceased': person.is_deceased,
                'gender': person.gender,
                'photo_path': person.photo_path or '',
                'photo': person.photo,
                'birth_place': getattr(person, 'birth_place', '') or '',
                'biography': getattr(person, 'biography', '') or '',
                'burial_place': getattr(person, 'burial_place', '') or '',
                'burial_date': getattr(person, 'burial_date', '') or '',
                'occupation': getattr(person, 'occupation', '') or '',
                'education': getattr(person, 'education', '') or '',
                'address': getattr(person, 'address', '') or '',
                'notes': getattr(person, 'notes', '') or '',
                'phone': getattr(person, 'phone', '') or '',
                'email': getattr(person, 'email', '') or '',
                'vk': getattr(person, 'vk', '') or '',
                'telegram': getattr(person, 'telegram', '') or '',
                'whatsapp': getattr(person, 'whatsapp', '') or '',
                'blood_type': getattr(person, 'blood_type', '') or '',
                'rh_factor': getattr(person, 'rh_factor', '') or '',
                'allergies': getattr(person, 'allergies', '') or '',
                'chronic_conditions': getattr(person, 'chronic_conditions', '') or '',
                'links': getattr(person, 'links', []) or [],
                'photo_album': getattr(person, 'photo_album', []) or [],
                'parents': list(person.parents),
                'children': list(person.children),
                'spouse_ids': list(person.spouse_ids),
                'collapsed_branches': getattr(person, 'collapsed_branches', False)
            }
        
        # Экспорт браков
        for marriage in model.get_marriages():
            tree_data['marriages'].append({
                'persons': list(marriage),
                'date': ''
            })
        
        # Загрузка на сервер
        return self.upload_tree(tree_data, tree_name)
    
    # === АДМИН ФУНКЦИИ ===
    def get_stats(self):
        """Получить статистику системы (только для админа)."""
        return self._request('/api/admin/stats')
    
    def get_users(self):
        """Получить список пользователей (только для админа)."""
        return self._request('/api/admin/users')
    
    def toggle_user(self, user_id):
        """Активировать/деактивировать пользователя (только для админа)."""
        return self._request(f'/api/admin/user/{user_id}/toggle', method='POST')
    
    # === НАСТРОЙКИ ===
    def set_server_url(self, url):
        """Установить URL сервера."""
        self._save_server_url(url)
    
    def get_server_url(self):
        """Получить URL сервера."""
        return self.server_url
    
    def check_health(self):
        """Проверить доступность сервера."""
        try:
            result = self._request('/api/health')
            return result.get('status') == 'ok'
        except:
            return False


# === Глобальный экземпляр ===
_sync_client = None

def get_sync_client():
    """Получить глобальный экземпляр клиента синхронизации."""
    global _sync_client
    if _sync_client is None:
        _sync_client = SyncClient()
    return _sync_client
