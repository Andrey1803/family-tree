# -*- coding: utf-8 -*-
"""Единое добавление: Контакты + Медицина"""

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Person.__init__ - добавляем параметры
old_params = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes=""):'''

new_params = '''    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes="",
                 phone="", email="", social_media=None, blood_type="", medical_info=None):'''

content = content.replace(old_params, new_params)

# 2. Person - добавляем поля
old_fields = '''        self.address = address if address is not None else ""
        self.notes = notes if notes is not None else ""'''

new_fields = '''        self.address = address if address is not None else ""
        self.notes = notes if notes is not None else ""
        self.phone = phone if phone is not None else ""
        self.email = email if email is not None else ""
        self.social_media = list(social_media) if social_media is not None else []
        self.blood_type = blood_type if blood_type is not None else ""
        self.medical_info = list(medical_info) if medical_info is not None else []'''

content = content.replace(old_fields, new_fields)

# 3. FamilyTreeModel.save_to_file - добавляем сохранение
old_save = '''                        "address": getattr(p, "address", "") or "",
                        "notes": getattr(p, "notes", "") or "",
                    } for pid, p in self.persons.items()'''

new_save = '''                        "address": getattr(p, "address", "") or "",
                        "notes": getattr(p, "notes", "") or "",
                        "phone": getattr(p, "phone", "") or "",
                        "email": getattr(p, "email", "") or "",
                        "social_media": getattr(p, "social_media", []) or [],
                        "blood_type": getattr(p, "blood_type", "") or "",
                        "medical_info": getattr(p, "medical_info", []) or [],
                    } for pid, p in self.persons.items()'''

content = content.replace(old_save, new_save)

# 4. FamilyTreeModel.load_from_file - добавляем загрузку
old_load = '''                    address=pdata.get("address", ""),
                    notes=pdata.get("notes", ""),
                )'''

new_load = '''                    address=pdata.get("address", ""),
                    notes=pdata.get("notes", ""),
                    phone=pdata.get("phone", ""),
                    email=pdata.get("email", ""),
                    social_media=pdata.get("social_media", []),
                    blood_type=pdata.get("blood_type", ""),
                    medical_info=pdata.get("medical_info", []),
                )'''

content = content.replace(old_load, new_load)

# 5. FamilyTreeModel.add_person - добавляем параметры
old_add = '''    def add_person(self, name, surname="", patronymic="", birth_date="", gender=GENDER_MALE,
                   is_deceased=False, death_date="", maiden_name="", photo=None, photo_path=""):'''

new_add = '''    def add_person(self, name, surname="", patronymic="", birth_date="", gender=GENDER_MALE,
                   is_deceased=False, death_date="", maiden_name="", photo=None, photo_path="",
                   birth_place="", biography="", burial_place="", burial_date="",
                   photo_album=None, links=None, occupation="", education="", address="", notes="",
                   phone="", email="", social_media=None, blood_type="", medical_info=None):'''

content = content.replace(old_add, new_add)

# 6. add_person - создание Person
old_person = '''        new_person = Person(
            name=name, surname=surname, patronymic=patronymic,
            birth_date=birth_date, gender=gender, photo=photo, photo_path=photo_path,
            is_deceased=is_deceased, death_date=death_date, maiden_name=maiden_name
        )'''

new_person = '''        new_person = Person(
            name=name, surname=surname, patronymic=patronymic,
            birth_date=birth_date, gender=gender, photo=photo, photo_path=photo_path,
            is_deceased=is_deceased, death_date=death_date, maiden_name=maiden_name,
            birth_place=birth_place, biography=biography, burial_place=burial_place,
            burial_date=burial_date, photo_album=photo_album, links=links,
            occupation=occupation, education=education, address=address, notes=notes,
            phone=phone, email=email, social_media=social_media, blood_type=blood_type,
            medical_info=medical_info
        )'''

content = content.replace(old_person, new_person)

with open('models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Модель обновлена')
