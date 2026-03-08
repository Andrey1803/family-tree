# -*- coding: utf-8 -*-
"""Модуль отслеживания активных пользователей."""

import threading
import time
from datetime import datetime, timedelta

class ActiveUsersTracker:
    """Отслеживает активных пользователей."""
    
    def __init__(self, timeout_seconds=300):
        """
        :param timeout_seconds: Время бездействия для считания оффлайн (по умолчанию 5 минут)
        """
        self.timeout_seconds = timeout_seconds
        self.active_users = {}  # {username: last_activity_time}
        self._lock = threading.Lock()
    
    def mark_active(self, username):
        """Отметить пользователя как активного."""
        with self._lock:
            self.active_users[username] = datetime.now()
    
    def get_active_users(self):
        """Получить список активных пользователей."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.timeout_seconds)
        
        with self._lock:
            # Очищаем устаревшие записи и возвращаем активных
            active = [
                username for username, last_seen in list(self.active_users.items())
                if last_seen > cutoff
            ]
            # Удаляем неактивных
            self.active_users = {
                username: last_seen for username, last_seen in self.active_users.items()
                if last_seen > cutoff
            }
            return active
    
    def is_user_active(self, username):
        """Проверить, активен ли пользователь."""
        with self._lock:
            last_seen = self.active_users.get(username)
            if not last_seen:
                return False
            return last_seen > datetime.now() - timedelta(seconds=self.timeout_seconds)
    
    def get_all_users_status(self):
        """Получить статус всех пользователей."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.timeout_seconds)
        
        with self._lock:
            return [
                {
                    'username': username,
                    'is_online': last_seen > cutoff,
                    'last_seen': last_seen.strftime("%d.%m.%Y %H:%M:%S")
                }
                for username, last_seen in self.active_users.items()
            ]


# Глобальный экземпляр для всего приложения
_tracker = None

def get_tracker():
    """Получить глобальный трекер активных пользователей."""
    global _tracker
    if _tracker is None:
        _tracker = ActiveUsersTracker()
    return _tracker

def mark_user_active(username):
    """Отметить пользователя как активного."""
    get_tracker().mark_active(username)

def get_active_users():
    """Получить список активных пользователей."""
    return get_tracker().get_active_users()

def is_user_active(username):
    """Проверить, активен ли пользователь."""
    return get_tracker().is_user_active(username)
