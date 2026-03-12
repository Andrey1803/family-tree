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

# Настройки сервера
DEFAULT_SERVER_URL = "https://ravishing-caring-production-3656.up.railway.app"
CONFIG_FILE = "sync_config.json"
REMEMBER_FILE = "login_remember.json"

# Учётные данные пользователей
USER_CREDENTIALS = {
    "Гость": {"login": "guest", "password": "guest123"},
    "Емельянов Андрей": {"login": "andrey", "password": "andrey123"},
    "Андрей Емельянов": {"login": "Андрей Емельянов", "password": "18031981asdF"},  # Правильный пароль
}


class SyncClient:
    """Клиент для синхронизации с сервером."""

    def __init__(self, server_url=None):
        self.server_url = server_url or self._load_server_url()
        self.token = self._load_token()
        self.user_id = None
        self.username = self._load_username()

    def _load_username(self):
        """Загрузить сохранённое имя пользователя"""
        if os.path.exists(REMEMBER_FILE):
            try:
                with open(REMEMBER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('username')
            except:
                pass
        return None

    def _save_username(self, username):
        """Сохранить имя пользователя"""
        data = {'username': username}
        with open(REMEMBER_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
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
                    token = config.get('token')
                    print(f"[SYNC] Loaded token from config: {token[:20] if token else 'None'}...")
                    return token
            except Exception as e:
                print(f"[SYNC] Error loading token: {e}")
                pass
        print("[SYNC] No token in config")
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
    
    def login(self, login, password, remember=False):
        """Войти в систему."""
        print(f"[SYNC] Login attempt: {login}")
        result = self._request('/api/auth/login', method='POST', data={
            'login': login,
            'password': password
        })
        print(f"[SYNC] Login result: {result}")

        if 'token' in result:
            self._save_token(result['token'], result.get('user_id'))
            if remember:
                self._save_username(login)
            print(f"[SYNC] Token saved: {result['token'][:20]}...")

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
    def sync_trees(self, local_model, tree_name='Моё дерево'):
        """Умная синхронизация: сливает локальное и серверное деревья"""
        # 1. Скачиваем дерево с сервера
        server_data = self.download_tree()
        
        if not server_data or 'tree' not in server_data:
            # Сервер пустое - загружаем локальное
            return self.upload_tree(local_model, tree_name)
        
        server_tree = server_data.get('tree', {})
        server_persons = server_tree.get('persons', {})
        server_marriages = server_tree.get('marriages', [])
        
        # 2. Получаем локальное дерево
        local_persons = local_model.get_all_persons()
        local_marriages = local_model.get_marriages()
        
        # 3. Сливаем персоны (только новые с новыми ID)
        merged_persons = dict(server_persons)
        next_id = max([int(pid) for pid in server_persons.keys() if pid.isdigit()], default=0) + 1
        
        id_mapping = {}  # Старый ID -> Новый ID
        
        for pid, person in local_persons.items():
            if pid not in merged_persons:
                # Проверяем, есть ли такая же персона на сервере (по имени)
                person_key = (person.surname.lower(), person.name.lower(), person.patronymic.lower())
                found = False
                for spid, sperson in server_persons.items():
                    sperson_key = (sperson.get('surname', '').lower(), sperson.get('name', '').lower(), sperson.get('patronymic', '').lower())
                    if person_key == sperson_key and person_key != ('', '', ''):
                        found = True
                        id_mapping[pid] = spid
                        break
                
                if not found:
                    # Добавляем новую персону с новым ID
                    new_id = str(next_id)
                    id_mapping[pid] = new_id
                    merged_persons[new_id] = {
                        'id': new_id,
                        'name': person.name,
                        'surname': person.surname,
                        'patronymic': person.patronymic,
                        'birth_date': person.birth_date,
                        'gender': person.gender,
                        'is_deceased': person.is_deceased,
                        'death_date': person.death_date,
                        'parents': [],  # Родителей пока не связываем
                        'children': [],
                        'spouse_ids': [],
                    }
                    next_id += 1
        
        # 4. Сливаем браки (с учётом маппинга ID)
        merged_marriages = list(server_marriages)
        existing_marriages_set = set()
        for m in server_marriages:
            if isinstance(m, list) and len(m) >= 2:
                existing_marriages_set.add(tuple(sorted([str(m[0]), str(m[1])])))
        
        for m in local_marriages:
            # Маппим ID
            id1 = id_mapping.get(str(m[0]), str(m[0]))
            id2 = id_mapping.get(str(m[1]), str(m[1]))
            marriage_key = tuple(sorted([id1, id2]))
            
            if marriage_key not in existing_marriages_set:
                merged_marriages.append(list(marriage_key))
                existing_marriages_set.add(marriage_key)
        
        # 5. Загружаем слитое дерево на сервер
        merged_tree = {
            'persons': merged_persons,
            'marriages': merged_marriages
        }
        
        return self.upload_tree_data(merged_tree, tree_name)

    def upload_tree(self, model, tree_name='Моё дерево'):
        """Загрузить дерево на сервер из модели"""
        print(f"[SYNC] Uploading tree: {tree_name}")
        print(f"[SYNC] Token: {self.token[:20] if self.token else 'None'}...")
        
        tree_data = {
            'persons': {},
            'marriages': []
        }

        # Поддержка и модели, и dict
        if hasattr(model, 'get_all_persons'):
            # Это объект модели
            persons_dict = model.get_all_persons()
            marriages_list = model.get_marriages()
        else:
            # Это dict
            persons_dict = model if isinstance(model, dict) else {}
            marriages_list = []

        for pid, person in persons_dict.items():
            if hasattr(person, 'name'):
                # Это объект Person
                tree_data['persons'][pid] = {
                    'id': pid,
                    'name': person.name,
                    'surname': person.surname,
                    'patronymic': person.patronymic,
                    'birth_date': person.birth_date,
                    'gender': person.gender,
                    'is_deceased': person.is_deceased,
                    'death_date': person.death_date,
                    'parents': list(person.parents),
                    'children': list(person.children),
                    'spouse_ids': list(person.spouse_ids),
                }
            else:
                # Это dict
                tree_data['persons'][pid] = person

        if marriages_list:
            for marriage in marriages_list:
                if hasattr(marriage, '__iter__') and not isinstance(marriage, dict):
                    marr_list = list(marriage)
                    # Формат: {'persons': [id1, id2], 'date': ''}
                    tree_data['marriages'].append({
                        'persons': marr_list[:2] if len(marr_list) >= 2 else marr_list,
                        'date': marr_list[2] if len(marr_list) > 2 else ''
                    })
                elif isinstance(marriage, dict):
                    tree_data['marriages'].append(marriage)
                else:
                    tree_data['marriages'].append({'persons': [marriage], 'date': ''})

        print(f"[SYNC] Persons: {len(tree_data['persons'])}, Marriages: {len(tree_data['marriages'])}")

        return self.upload_tree_data(tree_data, tree_name)

    def upload_tree_data(self, tree_data, tree_name='Моё дерево'):
        """Загрузить дерево на сервер"""
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
