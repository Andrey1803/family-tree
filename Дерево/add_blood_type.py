# -*- coding: utf-8 -*-
"""Добавление группы крови и медицинских данных"""

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем поля в __init__ Person
old_init = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes="",
                 significant_events=None, phone="", email="", social_media=None):'''

new_init = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes="",
                 significant_events=None, phone="", email="", social_media=None,
                 blood_type="", medical_info=None):'''

content = content.replace(old_init, new_init)

# 2. Добавляем инициализацию
old_fields = '''        self.social_media = list(social_media) if social_media is not None else []  # [{"platform": "VK", "url": "..."}]'''

new_fields = '''        self.social_media = list(social_media) if social_media is not None else []  # [{"platform": "VK", "url": "..."}]
        # Медицинская информация
        self.blood_type = blood_type if blood_type is not None else ""  # Группа крови
        self.medical_info = list(medical_info) if medical_info is not None else []  # [{"type": "disease", "name": "...", "notes": "..."}]'''

content = content.replace(old_fields, new_fields)

# 3. Добавляем сохранение
old_save = '''                        "phone": getattr(p, "phone", "") or "",
                        "email": getattr(p, "email", "") or "",
                        "social_media": getattr(p, "social_media", []) or [],
                    } for pid, p in self.persons.items()
                },'''

new_save = '''                        "phone": getattr(p, "phone", "") or "",
                        "email": getattr(p, "email", "") or "",
                        "social_media": getattr(p, "social_media", []) or [],
                        "blood_type": getattr(p, "blood_type", "") or "",
                        "medical_info": getattr(p, "medical_info", []) or [],
                    } for pid, p in self.persons.items()
                },'''

content = content.replace(old_save, new_save)

# 4. Добавляем загрузку
old_load = '''                    phone=pdata.get("phone", ""),
                    email=pdata.get("email", ""),
                    social_media=pdata.get("social_media", []),
                )'''

new_load = '''                    phone=pdata.get("phone", ""),
                    email=pdata.get("email", ""),
                    social_media=pdata.get("social_media", []),
                    blood_type=pdata.get("blood_type", ""),
                    medical_info=pdata.get("medical_info", []),
                )'''

content = content.replace(old_load, new_load)

with open('models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Группа крови и мед.информация добавлены')
