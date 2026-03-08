# -*- coding: utf-8 -*-
"""Модели данных: Person и FamilyTreeModel."""

import json
import os
import logging

from constants import (
    GENDER_MALE,
    GENDER_FEMALE,
    PATRONYMIC_RULES,
    PATRONYMIC_NAME_RULES,
    VALIDATION_MSG_GENDER_INVALID,
    VALIDATION_MSG_BIRTH_DATE_INVALID,
    VALIDATION_MSG_DEATH_DATE_INVALID,
    MSG_ERROR_CANNOT_ADD_TO_SELF,
    MSG_ERROR_DUPLICATE_MARRIAGE,
    MSG_ERROR_BLOOD_RELATIVE_MARRIAGE,
    MSG_SUCCESS_MARRIAGE_ADDED,
    MSG_SUCCESS_PERSON_DELETED,
    MSG_SUCCESS_MARRIAGE_REMOVED,
)


class Person:
    """Модель одной персоны в семейном дереве."""

    def __init__(self, name="", surname="", patronymic="", birth_date="", gender="",
                 photo=None, photo_path="", is_deceased=False, death_date="", maiden_name="",
                 birth_place="", biography="", burial_place="", burial_date="",
                 photo_album=None, links=None, occupation="", education="", address="", notes=""):
        self.id = None
        self.name = name
        self.surname = surname
        self.patronymic = patronymic
        self.birth_date = birth_date
        self.gender = gender
        self.photo = photo
        self.photo_path = photo_path or ""
        self.is_deceased = is_deceased
        self.death_date = death_date or ""
        self.maiden_name = maiden_name or ""
        self.parents = set()
        self.children = set()
        self.spouse_ids = set()
        self.collapsed_branches = False
        self.birth_place = birth_place if birth_place is not None else ""
        self.biography = biography if biography is not None else ""
        self.burial_place = burial_place if burial_place is not None else ""
        self.burial_date = burial_date if burial_date is not None else ""
        self.photo_album = list(photo_album) if photo_album is not None else []
        self.links = list(links) if links is not None else []
        self.occupation = occupation if occupation is not None else ""
        self.education = education if education is not None else ""
        self.address = address if address is not None else ""
        self.notes = notes if notes is not None else ""

    def full_name(self):
        return f"{self.name} {self.surname}"

    def display_name(self):
        parts = [self.name]
        if self.patronymic:
            parts.append(self.patronymic)
        parts.append(self.surname)
        return " ".join(parts)

    def get_current_surname(self):
        if self.gender == GENDER_FEMALE and self.maiden_name:
            return self.maiden_name
        return self.surname

    def has_photo(self):
        if self.photo_path and os.path.exists(self.photo_path):
            return True
        if self.photo and isinstance(self.photo, str) and self.photo.strip():
            return True
        return False


class FamilyTreeModel:
    """Модель семейного дерева: персоны, браки, загрузка/сохранение."""

    def __init__(self, data_file="family_tree.json"):
        self.persons = {}
        self.marriages = set()
        self.data_file = data_file
        self.current_center = None
        self.logger = logging.getLogger(__name__)
        self._modified = False
        self.next_id = 1

    def get_person(self, pid):
        return self.persons.get(pid)

    @staticmethod
    def _validate_date(date_str):
        if not date_str:
            return True
        try:
            parts = date_str.split('.')
            if len(parts) != 3:
                return False
            day, month, year = map(int, parts)
            if len(str(year)) != 4:
                return False
            if not (1 <= month <= 12):
                return False
            if not (1 <= day <= 31):
                return False
            return True
        except ValueError:
            return False

    def remove_spouse_link(self, person1_id, person2_id):
        if person1_id not in self.persons or person2_id not in self.persons:
            return False, "One or both persons do not exist."
        p1 = self.persons[person1_id]
        p2 = self.persons[person2_id]
        p1.spouse_ids.discard(person2_id)
        p2.spouse_ids.discard(person1_id)
        marriage_key = tuple(sorted((person1_id, person2_id)))
        self.marriages.discard(marriage_key)
        self.mark_modified()
        return True, "Spouse link removed successfully."

    def creates_cycle(self, potential_parent_id, potential_child_id):
        visited = set()
        stack = [potential_child_id]
        while stack:
            current_id = stack.pop()
            if current_id == potential_parent_id:
                return True
            if current_id in visited:
                continue
            visited.add(current_id)
            current_person = self.persons.get(current_id)
            if current_person:
                stack.extend(current_person.parents)
        return False

    def add_parent(self, child_id, parent_id):
        if child_id not in self.persons or parent_id not in self.persons:
            return False, "Ребёнок или родитель не найдены"
        child_obj = self.persons[child_id]
        parent_obj = self.persons[parent_id]
        if self.creates_cycle(parent_id, child_id):
            return False, "Обнаружен цикл в родственных связях"
        child_obj.parents.add(parent_id)
        parent_obj.children.add(child_id)
        self.mark_modified()
        return True, f"Родитель {parent_id} успешно добавлен к ребёнку {child_id}"

    def add_person(self, name, surname="", patronymic="", birth_date="", gender=GENDER_MALE,
                   is_deceased=False, death_date="", maiden_name="", photo=None, photo_path=""):
        is_valid, validation_errors = self.validate_person_data(
            name, surname, patronymic, birth_date, gender,
            is_deceased, death_date, maiden_name
        )
        if not is_valid:
            return None, "\n".join(validation_errors)
        new_id = str(self.next_id)
        self.next_id += 1
        new_person = Person(
            name=name, surname=surname, patronymic=patronymic,
            birth_date=birth_date, gender=gender, photo=photo, photo_path=photo_path,
            is_deceased=is_deceased, death_date=death_date, maiden_name=maiden_name
        )
        new_person.id = new_id
        new_person.parents = set()
        new_person.children = set()
        new_person.spouse_ids = set()
        new_person.collapsed_branches = False
        self.persons[new_id] = new_person
        self.mark_modified()
        self.logger.info(f"Добавлена персона: {new_person.display_name()} (ID: {new_id})")
        return new_id, None

    def validate_person_data(self, name, surname, patronymic, birth_date, gender,
                             is_deceased, death_date, maiden_name):
        errors = []
        if not name.strip():
            errors.append("Имя обязательно для заполнения")
        if not surname.strip():
            errors.append("Фамилия обязательна для заполнения")
        if gender not in (GENDER_MALE, GENDER_FEMALE):
            errors.append(VALIDATION_MSG_GENDER_INVALID)
        if birth_date.strip() and not self._validate_date(birth_date):
            errors.append(VALIDATION_MSG_BIRTH_DATE_INVALID)
        if is_deceased and death_date.strip() and not self._validate_date(death_date):
            errors.append(VALIDATION_MSG_DEATH_DATE_INVALID)
        return len(errors) == 0, errors

    def add_marriage(self, person1_id, person2_id):
        if person1_id == person2_id:
            return False, MSG_ERROR_CANNOT_ADD_TO_SELF
        marriage_key = tuple(sorted((person1_id, person2_id)))
        if marriage_key in self.marriages:
            return False, MSG_ERROR_DUPLICATE_MARRIAGE
        if self._is_blood_relative(person1_id, person2_id):
            return False, MSG_ERROR_BLOOD_RELATIVE_MARRIAGE
        p1 = self.get_person(person1_id)
        p2 = self.get_person(person2_id)
        if p1 and p2:
            p1.spouse_ids.add(person2_id)
            p2.spouse_ids.add(person1_id)
        self.marriages.add(marriage_key)
        self.mark_modified()
        return True, MSG_SUCCESS_MARRIAGE_ADDED

    def delete_person(self, pid):
        if pid not in self.persons:
            return False, "Персона не найдена."
        person = self.persons[pid]
        for parent_id in list(person.parents):
            parent = self.get_person(parent_id)
            if parent and pid in parent.children:
                parent.children.discard(pid)
        for child_id in list(person.children):
            child = self.get_person(child_id)
            if child and pid in child.parents:
                child.parents.discard(pid)
        marriages_to_remove = [m for m in self.marriages if pid in m]
        for marriage in marriages_to_remove:
            self.marriages.discard(marriage)
            spouse_id = marriage[0] if marriage[1] == pid else marriage[1]
            spouse = self.get_person(spouse_id)
            if spouse and pid in spouse.spouse_ids:
                spouse.spouse_ids.discard(pid)
        del self.persons[pid]
        if self.current_center == pid:
            self.current_center = None
        self.mark_modified()
        return True, MSG_SUCCESS_PERSON_DELETED

    def remove_marriage(self, person1_id, person2_id):
        if person1_id not in self.persons or person2_id not in self.persons:
            return False, "One or both persons do not exist."
        marriage_key = tuple(sorted((person1_id, person2_id)))
        if marriage_key not in self.marriages:
            return False, "Marriage does not exist."
        p1 = self.persons[person1_id]
        p2 = self.persons[person2_id]
        p1.spouse_ids.discard(person2_id)
        p2.spouse_ids.discard(person1_id)
        self.marriages.discard(marriage_key)
        self.mark_modified()
        return True, MSG_SUCCESS_MARRIAGE_REMOVED

    def get_spouse(self, person_id):
        person = self.get_person(person_id)
        if person and person.spouse_ids:
            return min(person.spouse_ids, key=lambda x: (str(x),))
        return None

    def get_spouses(self, person_id):
        person = self.get_person(person_id)
        if not person or not person.spouse_ids:
            return []
        return sorted(person.spouse_ids, key=lambda x: (str(x),))

    def get_marriages(self):
        return self.marriages

    def get_all_persons(self):
        return self.persons

    def find_person_by_name_surname(self, name, surname):
        for p in self.persons.values():
            if p.name.lower() == name.lower() and p.surname.lower() == surname.lower():
                return p
        return None

    def _is_blood_relative(self, person1_id, person2_id):
        def get_all_ancestors(pid, ancestors):
            person = self.persons.get(pid)
            if not person:
                return
            for parent_id in person.parents:
                if parent_id not in ancestors:
                    ancestors.add(parent_id)
                    get_all_ancestors(parent_id, ancestors)

        if person1_id == person2_id:
            return True
        ancestors1 = set()
        get_all_ancestors(person1_id, ancestors1)
        ancestors2 = set()
        get_all_ancestors(person2_id, ancestors2)
        return bool(ancestors1 & ancestors2)

    def save_to_file(self, filename=None):
        if filename is None:
            filename = self.data_file
        try:
            data = {
                "persons": {
                    pid: {
                        "name": p.name, "surname": p.surname, "patronymic": p.patronymic,
                        "birth_date": p.birth_date, "gender": p.gender,
                        "photo": p.photo if p.photo and isinstance(p.photo, str) and p.photo.strip() else None,
                        "photo_path": getattr(p, "photo_path", "") or "",
                        "is_deceased": p.is_deceased, "death_date": p.death_date,
                        "maiden_name": getattr(p, "maiden_name", "") or "",
                        "parents": list(p.parents), "children": list(p.children),
                        "spouse_ids": list(p.spouse_ids), "collapsed_branches": p.collapsed_branches,
                        "birth_place": getattr(p, "birth_place", "") or "",
                        "biography": getattr(p, "biography", "") or "",
                        "burial_place": getattr(p, "burial_place", "") or "",
                        "burial_date": getattr(p, "burial_date", "") or "",
                        "photo_album": getattr(p, "photo_album", None) or [],
                        "links": getattr(p, "links", None) or [],
                        "occupation": getattr(p, "occupation", "") or "",
                        "education": getattr(p, "education", "") or "",
                        "address": getattr(p, "address", "") or "",
                        "notes": getattr(p, "notes", "") or "",
                    } for pid, p in self.persons.items()
                },
                "marriages": list(self.marriages),
                "current_center": self.current_center
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Данные успешно сохранены в {filename}")
            self.clear_modified_flag()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в {filename}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_from_file(self, filename=None):
        if filename is None:
            filename = self.data_file
        if not os.path.exists(filename):
            self.logger.info(f"Файл {filename} не найден, создание нового дерева.")
            return False
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.persons = {}
            for pid, pdata in data.get("persons", {}).items():
                p = Person(
                    name=pdata.get("name", ""),
                    surname=pdata.get("surname", ""),
                    patronymic=pdata.get("patronymic", ""),
                    birth_date=pdata.get("birth_date", ""),
                    gender=pdata.get("gender", ""),
                    photo=pdata.get("photo", None),
                    photo_path=pdata.get("photo_path", ""),
                    is_deceased=pdata.get("is_deceased", False) in (True, 1, "1", "true", "True"),
                    death_date=pdata.get("death_date", ""),
                    maiden_name=pdata.get("maiden_name", ""),
                    birth_place=pdata.get("birth_place", ""),
                    biography=pdata.get("biography", ""),
                    burial_place=pdata.get("burial_place", ""),
                    burial_date=pdata.get("burial_date", ""),
                    photo_album=pdata.get("photo_album", []),
                    links=pdata.get("links", []),
                    occupation=pdata.get("occupation", ""),
                    education=pdata.get("education", ""),
                    address=pdata.get("address", ""),
                    notes=pdata.get("notes", ""),
                )
                p.id = pid
                p.parents = set(str(pid) for pid in pdata.get("parents", []) if pid)
                p.children = set(str(pid) for pid in pdata.get("children", []) if pid)
                p.spouse_ids = set(str(pid) for pid in pdata.get("spouse_ids", []) if pid)
                p.collapsed_branches = pdata.get("collapsed_branches", False)
                self.persons[pid] = p

            marriages_raw = data.get("marriages", [])
            self.marriages = set()
            for pair in marriages_raw:
                if len(pair) == 2:
                    h_id, w_id = str(pair[0]), str(pair[1])
                    self.marriages.add(tuple(sorted((h_id, w_id))))

            center_val = data.get("current_center")
            self.current_center = str(center_val) if center_val and center_val != "None" else None

            numeric_ids = []
            for pid in self.persons:
                try:
                    numeric_ids.append(int(pid))
                except (ValueError, TypeError):
                    pass
            self.next_id = max(numeric_ids, default=0) + 1

            self.logger.info(f"Данные успешно загружены из {filename}")
            self.clear_modified_flag()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки из {filename}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_patronymic(self, father_name):
        if not father_name:
            return ""
        clean_name = father_name.strip().split()[0]
        if not clean_name:
            return ""
        name_lower = clean_name.lower()
        SPECIAL_CASES = {
            "николай": "николаевич", "сергей": "сергеевич",
            "владимир": "владимирович", "александр": "александрович",
            "михаил": "михайлович", "дмитрий": "дмитриевич",
            "андрей": "андреевич", "константин": "константинович",
            "пётр": "петрович", "петр": "петрович", "иван": "иванович",
            "юрий": "юрьевич", "фёдор": "фёдорович", "федор": "федорович",
            "геннадий": "геннадиевич", "никита": "никитич", "илья": "ильич",
        }
        if name_lower in SPECIAL_CASES:
            return SPECIAL_CASES[name_lower].capitalize()
        for ending, male_suffix, female_suffix in PATRONYMIC_RULES:
            if name_lower.endswith(ending):
                stem = clean_name[:-len(ending)]
                if not stem:
                    continue
                return (stem + male_suffix).capitalize()
        last_char = name_lower[-1]
        if last_char in "аы":
            suffix = "евич" if last_char == "ы" else "ович"
        elif last_char == "й":
            suffix = "евич"
        else:
            suffix = "ович"
        return (clean_name + suffix).capitalize()

    def generate_name_from_patronymic(self, patronymic, gender="Мужской"):
        if not patronymic:
            return "Неизвестный" if gender == "Мужской" else "Неизвестная"
        pat_lower = patronymic.strip().lower()
        special_reverse = {"никитич": "Никита", "ильич": "Илья"}
        if pat_lower in special_reverse:
            return special_reverse[pat_lower]
        for patronymic_suffix, name_base in PATRONYMIC_NAME_RULES:
            if pat_lower.endswith(patronymic_suffix):
                stem = patronymic.strip()[:-len(patronymic_suffix)]
                if not stem:
                    continue
                return (stem + name_base).capitalize()
        return "Неизвестный" if gender == "Мужской" else "Неизвестная"

    def add_or_link_parent(self, child_id, name, surname, patronymic, gender):
        existing_parent = self.find_person_by_name_surname(name, surname)
        if existing_parent:
            parent_id = existing_parent.id
            if child_id in self.persons[parent_id].children:
                return parent_id, "Родитель уже связан с этим ребёнком."
            self.add_parent(child_id, parent_id)
            return parent_id, None
        new_parent_id, error = self.add_person(name, surname, patronymic, "", gender)
        if error:
            return None, error
        self.add_parent(child_id, new_parent_id)
        return new_parent_id, None

    def mark_modified(self):
        self._modified = True

    def clear_modified_flag(self):
        self._modified = False

    @property
    def modified(self):
        return self._modified
