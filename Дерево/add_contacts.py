# -*- coding: utf-8 -*-
"""Добавление контактов в модель Person"""

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем поля в __init__ Person
old_init = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes="",
                 significant_events=None):'''

new_init = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes="",
                 significant_events=None, phone="", email="", social_media=None):'''

content = content.replace(old_init, new_init)

# 2. Добавляем инициализацию полей
old_fields = '''        self.notes = notes if notes is not None else ""
        # Значимые события: [{"date": "ДД.ММ.ГГГГ", "title": "Событие", "type": "event"}]
        self.significant_events = list(significant_events) if significant_events is not None else []'''

new_fields = '''        self.notes = notes if notes is not None else ""
        # Значимые события: [{"date": "ДД.ММ.ГГГГ", "title": "Событие", "type": "event"}]
        self.significant_events = list(significant_events) if significant_events is not None else []
        # Контакты (для живых персон)
        self.phone = phone if phone is not None else ""
        self.email = email if email is not None else ""
        self.social_media = list(social_media) if social_media is not None else []  # [{"platform": "VK", "url": "..."}]'''

content = content.replace(old_fields, new_fields)

# 3. Добавляем сохранение контактов
old_save = '''                        "notes": getattr(p, "notes", "") or "",
                        "significant_events": getattr(p, "significant_events", []) or [],
                    } for pid, p in self.persons.items()
                },'''

new_save = '''                        "notes": getattr(p, "notes", "") or "",
                        "significant_events": getattr(p, "significant_events", []) or [],
                        "phone": getattr(p, "phone", "") or "",
                        "email": getattr(p, "email", "") or "",
                        "social_media": getattr(p, "social_media", []) or [],
                    } for pid, p in self.persons.items()
                },'''

content = content.replace(old_save, new_save)

# 4. Добавляем загрузку контактов
old_load = '''                    notes=pdata.get("notes", ""),
                    significant_events=pdata.get("significant_events", []),
                )'''

new_load = '''                    notes=pdata.get("notes", ""),
                    significant_events=pdata.get("significant_events", []),
                    phone=pdata.get("phone", ""),
                    email=pdata.get("email", ""),
                    social_media=pdata.get("social_media", []),
                )'''

content = content.replace(old_load, new_load)

with open('models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Контакты добавлены в модель')
