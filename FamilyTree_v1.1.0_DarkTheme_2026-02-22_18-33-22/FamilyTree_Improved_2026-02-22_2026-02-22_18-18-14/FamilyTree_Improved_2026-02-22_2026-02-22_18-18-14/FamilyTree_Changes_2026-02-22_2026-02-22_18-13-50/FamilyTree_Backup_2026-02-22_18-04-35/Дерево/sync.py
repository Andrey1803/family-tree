# -*- coding: utf-8 -*-
"""
Модуль синхронизации с сервером.
Отправляет данные на сервер для резервного копирования.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

# URL сервера для синхронизации (замените на актуальный)
SYNC_SERVER_URL = os.environ.get("SYNC_SERVER_URL", "https://your-server.com/api/sync")


def sync_to_server(data_file, username="Гость"):
    """
    Синхронизирует данные с сервером.
    
    Args:
        data_file: Путь к файлу данных JSON
        username: Имя пользователя
    
    Returns:
        bool: True если синхронизация успешна, False иначе
    """
    try:
        import urllib.request
        import urllib.error
        
        # Проверяем существование файла
        if not os.path.exists(data_file):
            logger.warning(f"Файл данных не найден: {data_file}")
            return False
        
        # Читаем данные
        with open(data_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        # Подготовка данных для отправки
        sync_data = {
            'username': username,
            'data': data,
            'filename': os.path.basename(data_file)
        }
        
        # Отправка на сервер
        req = urllib.request.Request(
            SYNC_SERVER_URL,
            data=json.dumps(sync_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                logger.info(f"Синхронизация успешна для {username}")
                return True
            else:
                logger.warning(f"Сервер вернул статус {response.status}")
                return False
                
    except urllib.error.URLError as e:
        logger.warning(f"Не удалось подключиться к серверу синхронизации: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        return False


def sync_from_server(username="Гость"):
    """
    Загружает данные с сервера.
    
    Args:
        username: Имя пользователя
    
    Returns:
        dict или None: Данные дерева или None при ошибке
    """
    try:
        import urllib.request
        import urllib.error
        
        # Запрос данных с сервера
        url = f"{SYNC_SERVER_URL}?username={urllib.parse.quote(username)}"
        
        req = urllib.request.Request(url, method='GET')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"Данные загружены с сервера для {username}")
                return result.get('data')
            else:
                logger.warning(f"Сервер вернул статус {response.status}")
                return None
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.info(f"Данные для {username} не найдены на сервере")
        else:
            logger.warning(f"Ошибка при загрузке данных: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return None
