# -*- coding: utf-8 -*-
"""Точка входа для Railway (корень проекта)."""

import sys
import os

# Добавляем корень и web в путь импорта
ROOT_DIR = os.path.dirname(__file__)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'web'))

# Импортируем приложение из web/app.py
from web.app import app

if __name__ == "__main__":
    app.run()
