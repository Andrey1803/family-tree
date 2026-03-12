# -*- coding: utf-8 -*-
"""Точка входа для Railway (корень проекта)."""

import sys
import os

# Добавляем папку web в путь импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

# Импортируем приложение из web/app.py
from app import app

if __name__ == "__main__":
    app.run()
