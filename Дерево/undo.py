# -*- coding: utf-8 -*-
"""
Модуль отмены/повтора действий (Undo/Redo) для приложения «Семейное древо».

Поддерживаемые операции:
- Добавление персоны
- Удаление персоны
- Редактирование персоны
- Добавление брака
- Удаление брака
- Добавление родителя
- Добавление ребёнка
"""

import json
import copy
import logging

logger = logging.getLogger(__name__)

# Максимальное количество действий в истории
MAX_HISTORY_SIZE = 50


class UndoAction:
    """Базовый класс для действий."""

    def __init__(self, name):
        self.name = name

    def undo(self, model):
        """Отменить действие."""
        raise NotImplementedError

    def redo(self, model):
        """Повторить действие."""
        raise NotImplementedError


class AddPersonAction(UndoAction):
    """Действие: добавление персоны."""

    def __init__(self, person_id, person_data):
        super().__init__("Добавление персоны")
        self.person_id = person_id
        self.person_data = person_data

    def undo(self, model):
        # Сохраняем данные перед удалением для redo
        self.person_data = self._serialize_person(model.persons.get(self.person_id))
        if self.person_id in model.persons:
            del model.persons[self.person_id]
            model.mark_modified()

    def redo(self, model):
        from models import Person
        person = self._deserialize_person(self.person_data)
        person.id = self.person_id
        model.persons[self.person_id] = person
        model.mark_modified()

    def _serialize_person(self, person):
        if not person:
            return None
        return {
            'name': person.name,
            'surname': person.surname,
            'patronymic': person.patronymic,
            'birth_date': person.birth_date,
            'gender': person.gender,
            'is_deceased': person.is_deceased,
            'death_date': person.death_date,
            'maiden_name': person.maiden_name,
            'parents': list(person.parents),
            'children': list(person.children),
            'spouse_ids': list(person.spouse_ids),
        }

    def _deserialize_person(self, data):
        from models import Person
        if not data:
            return None
        p = Person(
            name=data['name'],
            surname=data['surname'],
            patronymic=data['patronymic'],
            birth_date=data['birth_date'],
            gender=data['gender'],
            is_deceased=data['is_deceased'],
            death_date=data['death_date'],
            maiden_name=data['maiden_name'],
        )
        p.parents = set(data['parents'])
        p.children = set(data['children'])
        p.spouse_ids = set(data['spouse_ids'])
        return p


class DeletePersonAction(UndoAction):
    """Действие: удаление персоны."""

    def __init__(self, person_id, person_data, affected_relations):
        super().__init__("Удаление персоны")
        self.person_id = person_id
        self.person_data = person_data
        self.affected_relations = affected_relations  # {'parents': [...], 'children': [...], 'spouses': [...]}

    def undo(self, model):
        from models import Person
        # Восстанавливаем персону
        person = self._deserialize_person(self.person_data)
        person.id = self.person_id
        model.persons[self.person_id] = person

        # Восстанавливаем связи
        for parent_id in self.affected_relations.get('parents', []):
            if parent_id in model.persons:
                model.persons[parent_id].children.add(self.person_id)
                person.parents.add(parent_id)

        for child_id in self.affected_relations.get('children', []):
            if child_id in model.persons:
                model.persons[child_id].parents.add(self.person_id)
                person.children.add(child_id)

        for spouse_id in self.affected_relations.get('spouses', []):
            if spouse_id in model.persons:
                model.persons[spouse_id].spouse_ids.add(self.person_id)
                person.spouse_ids.add(spouse_id)
                model.marriages.add(tuple(sorted((self.person_id, spouse_id))))

        model.mark_modified()

    def redo(self, model):
        if self.person_id in model.persons:
            del model.persons[self.person_id]
            model.mark_modified()

    def _deserialize_person(self, data):
        from models import Person
        if not data:
            return None
        p = Person(
            name=data['name'],
            surname=data['surname'],
            patronymic=data['patronymic'],
            birth_date=data['birth_date'],
            gender=data['gender'],
            is_deceased=data['is_deceased'],
            death_date=data['death_date'],
            maiden_name=data['maiden_name'],
        )
        return p


class EditPersonAction(UndoAction):
    """Действие: редактирование персоны."""

    def __init__(self, person_id, old_data, new_data):
        super().__init__("Редактирование персоны")
        self.person_id = person_id
        self.old_data = old_data
        self.new_data = new_data

    def undo(self, model):
        if self.person_id not in model.persons:
            return
        person = model.persons[self.person_id]
        self._apply_data(person, self.old_data)
        model.mark_modified()

    def redo(self, model):
        if self.person_id not in model.persons:
            return
        person = model.persons[self.person_id]
        self._apply_data(person, self.new_data)
        model.mark_modified()

    def _apply_data(self, person, data):
        person.name = data['name']
        person.surname = data['surname']
        person.patronymic = data['patronymic']
        person.birth_date = data['birth_date']
        person.gender = data['gender']
        person.is_deceased = data['is_deceased']
        person.death_date = data['death_date']
        person.maiden_name = data['maiden_name']


class AddMarriageAction(UndoAction):
    """Действие: добавление брака."""

    def __init__(self, person1_id, person2_id):
        super().__init__("Добавление брака")
        self.person1_id = person1_id
        self.person2_id = person2_id

    def undo(self, model):
        p1 = model.get_person(self.person1_id)
        p2 = model.get_person(self.person2_id)
        if p1:
            p1.spouse_ids.discard(self.person2_id)
        if p2:
            p2.spouse_ids.discard(self.person1_id)
        marriage_key = tuple(sorted((self.person1_id, self.person2_id)))
        model.marriages.discard(marriage_key)
        model.mark_modified()

    def redo(self, model):
        p1 = model.get_person(self.person1_id)
        p2 = model.get_person(self.person2_id)
        if p1 and p2:
            p1.spouse_ids.add(self.person2_id)
            p2.spouse_ids.add(self.person1_id)
            marriage_key = tuple(sorted((self.person1_id, self.person2_id)))
            model.marriages.add(marriage_key)
            model.mark_modified()


class RemoveMarriageAction(UndoAction):
    """Действие: удаление брака."""

    def __init__(self, person1_id, person2_id):
        super().__init__("Удаление брака")
        self.person1_id = person1_id
        self.person2_id = person2_id

    def undo(self, model):
        p1 = model.get_person(self.person1_id)
        p2 = model.get_person(self.person2_id)
        if p1 and p2:
            p1.spouse_ids.add(self.person2_id)
            p2.spouse_ids.add(self.person1_id)
            marriage_key = tuple(sorted((self.person1_id, self.person2_id)))
            model.marriages.add(marriage_key)
            model.mark_modified()

    def redo(self, model):
        p1 = model.get_person(self.person1_id)
        p2 = model.get_person(self.person2_id)
        if p1:
            p1.spouse_ids.discard(self.person2_id)
        if p2:
            p2.spouse_ids.discard(self.person1_id)
        marriage_key = tuple(sorted((self.person1_id, self.person2_id)))
        model.marriages.discard(marriage_key)
        model.mark_modified()


class UndoManager:
    """Менеджер истории действий."""

    def __init__(self, model):
        self.model = model
        self.undo_stack = []
        self.redo_stack = []
        self.enabled = True

    def push(self, action):
        """Добавить действие в историю."""
        if not self.enabled:
            return

        self.undo_stack.append(action)
        self.redo_stack.clear()  # Очищаем redo при новом действии

        # Ограничиваем размер истории
        if len(self.undo_stack) > MAX_HISTORY_SIZE:
            self.undo_stack.pop(0)

    def undo(self):
        """Отменить последнее действие."""
        if not self.undo_stack:
            return False

        action = self.undo_stack.pop()
        try:
            self.enabled = False  # Отключаем запись в историю при отмене
            action.undo(self.model)
            self.redo_stack.append(action)
            return True
        except Exception as e:
            logger.error(f"Ошибка при отмене действия: {e}")
            return False
        finally:
            self.enabled = True

    def redo(self):
        """Повторить отменённое действие."""
        if not self.redo_stack:
            return False

        action = self.redo_stack.pop()
        try:
            self.enabled = False
            action.redo(self.model)
            self.undo_stack.append(action)
            return True
        except Exception as e:
            logger.error(f"Ошибка при повторе действия: {e}")
            return False
        finally:
            self.enabled = True

    def can_undo(self):
        """Можно ли отменить действие."""
        return len(self.undo_stack) > 0

    def can_redo(self):
        """Можно ли повторить действие."""
        return len(self.redo_stack) > 0

    def clear(self):
        """Очистить историю."""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_last_action_name(self):
        """Название последнего действия."""
        if self.undo_stack:
            return self.undo_stack[-1].name
        return ""


def create_add_person_action(model, person_id):
    """Создать действие добавления персоны."""
    person = model.get_person(person_id)
    if not person:
        return None

    action = AddPersonAction(person_id, None)
    action.person_data = action._serialize_person(person)
    return action


def create_delete_person_action(model, person_id):
    """Создать действие удаления персоны."""
    person = model.get_person(person_id)
    if not person:
        return None

    affected = {
        'parents': list(person.parents),
        'children': list(person.children),
        'spouses': list(person.spouse_ids),
    }

    action = DeletePersonAction(
        person_id,
        action._serialize_person(person) if hasattr(action, '_serialize_person') else {
            'name': person.name,
            'surname': person.surname,
            'patronymic': person.patronymic,
            'birth_date': person.birth_date,
            'gender': person.gender,
            'is_deceased': person.is_deceased,
            'death_date': person.death_date,
            'maiden_name': person.maiden_name,
        },
        affected
    )
    return action


def create_edit_person_action(model, person_id, old_data, new_data):
    """Создать действие редактирования персоны."""
    return EditPersonAction(person_id, old_data, new_data)


def create_add_marriage_action(person1_id, person2_id):
    """Создать действие добавления брака."""
    return AddMarriageAction(person1_id, person2_id)


def create_remove_marriage_action(person1_id, person2_id):
    """Создать действие удаления брака."""
    return RemoveMarriageAction(person1_id, person2_id)
