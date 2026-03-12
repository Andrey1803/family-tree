# -*- coding: utf-8 -*-
"""Добавление отсутствующих констант"""

with open('constants.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим где-то в районе MSG_STATUS и добавляем недостающие
old_status = '''MSG_STATUS_DATA_SAVED = "Данные сохранены."
MSG_STATUS_DATA_LOADED = "Данные загружены."'''

new_status = '''MSG_STATUS_DATA_SAVED = "Данные сохранены."
MSG_STATUS_DATA_LOADED = "Данные загружены."
MSG_STATUS_PAN_ACTIVE = "Перемещение..."
MSG_STATUS_PAN_INACTIVE = "Перемещение завершено"
MSG_STATUS_ZOOM_IN = "Приближение..."
MSG_STATUS_ZOOM_OUT = "Отдаление..."'''

content = content.replace(old_status, new_status)

with open('constants.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Константы добавлены')
