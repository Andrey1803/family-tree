# -*- coding: utf-8 -*-
"""WSGI entry point для Gunicorn"""

# Сначала инициализируем БД
from app import initialize_database
initialize_database()

# Потом импортируем app для Gunicorn
from app import app

if __name__ == "__main__":
    app.run()
