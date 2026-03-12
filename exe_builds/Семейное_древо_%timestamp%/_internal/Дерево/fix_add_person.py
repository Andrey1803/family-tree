# -*- coding: utf-8 -*-
"""Исправление add_person в FamilyTreeModel"""

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим метод add_person
import re
match = re.search(r'def add_person\(self, name.*?\):.*?(?=\n    def |\Z)', content, re.DOTALL)

if match:
    old_method = match.group()
    
    new_method = '''    def add_person(self, name, surname="", patronymic="", birth_date="", gender=GENDER_MALE,
                   is_deceased=False, death_date="", maiden_name="", photo=None, photo_path="",
                   birth_place="", biography="", burial_place="", burial_date="",
                   photo_album=None, links=None, occupation="", education="", address="", notes="",
                   significant_events=None, phone="", email="", social_media=None,
                   blood_type="", medical_info=None):
        is_valid, validation_errors = self.validate_person_data(
            name, surname, patronymic, birth_date, gender,
            is_deceased, death_date, maiden_name
        )
        if not is_valid:
            return None, "\\n".join(validation_errors)
        new_id = str(self.next_id)
        self.next_id += 1
        new_person = Person(
            name=name, surname=surname, patronymic=patronymic,
            birth_date=birth_date, gender=gender, photo=photo, photo_path=photo_path,
            is_deceased=is_deceased, death_date=death_date, maiden_name=maiden_name,
            birth_place=birth_place, biography=biography, burial_place=burial_place,
            burial_date=burial_date, photo_album=photo_album, links=links,
            occupation=occupation, education=education, address=address, notes=notes,
            significant_events=significant_events, phone=phone, email=email,
            social_media=social_media, blood_type=blood_type, medical_info=medical_info
        )
        new_person.id = new_id
        new_person.parents = set()
        new_person.children = set()
        new_person.spouse_ids = set()
        new_person.collapsed_branches = False
        self.persons[new_id] = new_person
        self.mark_modified()
        self.logger.info(f"Добавлена персона: {new_person.display_name()} (ID: {new_id})")
        return new_id, None'''
    
    content = content.replace(old_method, new_method)
    
    with open('models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('OK - add_person исправлен')
else:
    print('ERROR - add_person не найден')
