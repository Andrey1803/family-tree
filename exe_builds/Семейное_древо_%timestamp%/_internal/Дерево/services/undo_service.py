# -*- coding: utf-8 -*-
"""
Сервис отмены/повтора действий (Undo/Redo).
Расширяет базовый undo.py с улучшенной архитектурой.
"""

import logging
from typing import Optional, List, Callable, Any, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

MAX_HISTORY_SIZE = 50


class UndoAction(ABC):
    """Базовый класс для действий отмены/повтора."""

    def __init__(self, name: str):
        self.name = name
        self._done = False

    @abstractmethod
    def undo(self, context: Any) -> bool:
        """
        Отменить действие.

        Args:
            context: Контекст (модель дерева).

        Returns:
            True если успешно.
        """
        pass

    @abstractmethod
    def redo(self, context: Any) -> bool:
        """
        Повторить действие.

        Args:
            context: Контекст (модель дерева).

        Returns:
            True если успешно.
        """
        pass


class UndoService:
    """Сервис управления историей действий."""

    def __init__(self, model: Any = None):
        """
        Инициализация сервиса.

        Args:
            model: Модель дерева для операций.
        """
        self.model = model
        self._undo_stack: List[UndoAction] = []
        self._redo_stack: List[UndoAction] = []

    def set_model(self, model: Any):
        """Устанавливает модель дерева."""
        self.model = model

    def execute(self, action: UndoAction) -> bool:
        """
        Выполняет действие и добавляет в историю.

        Args:
            action: Действие для выполнения.

        Returns:
            True если успешно.
        """
        if self.model is None:
            logger.error("Модель не установлена")
            return False

        try:
            if action.redo(self.model):
                self._undo_stack.append(action)
                self._redo_stack.clear()

                # Ограничение размера истории
                if len(self._undo_stack) > MAX_HISTORY_SIZE:
                    self._undo_stack.pop(0)

                logger.debug(f"Дей выполнено: {action.name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Ошибка выполнения действия: {e}")
            return False

    def undo(self) -> Optional[str]:
        """
        Отменяет последнее действие.

        Returns:
            Название отменённого действия или None.
        """
        if not self._undo_stack:
            logger.debug("Нечего отменять")
            return None

        action = self._undo_stack.pop()
        try:
            if action.undo(self.model):
                self._redo_stack.append(action)
                logger.debug(f"Отменено: {action.name}")
                return action.name
            else:
                # Возвращаем обратно если не удалось отменить
                self._undo_stack.append(action)
                return None
        except Exception as e:
            logger.error(f"Ошибка отмены действия: {e}")
            self._undo_stack.append(action)
            return None

    def redo(self) -> Optional[str]:
        """
        Повторяет отменённое действие.

        Returns:
            Название повторённого действия или None.
        """
        if not self._redo_stack:
            logger.debug("Нечего повторять")
            return None

        action = self._redo_stack.pop()
        try:
            if action.redo(self.model):
                self._undo_stack.append(action)
                logger.debug(f"Повторено: {action.name}")
                return action.name
            else:
                # Возвращаем обратно если не удалось повторить
                self._redo_stack.append(action)
                return None
        except Exception as e:
            logger.error(f"Ошибка повтора действия: {e}")
            self._redo_stack.append(action)
            return None

    def can_undo(self) -> bool:
        """Проверяет, доступна ли отмена."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Проверяет, доступен ли повтор."""
        return len(self._redo_stack) > 0

    def get_undo_stack_size(self) -> int:
        """Возвращает размер стека отмены."""
        return len(self._undo_stack)

    def get_redo_stack_size(self) -> int:
        """Возвращает размер стека повтора."""
        return len(self._redo_stack)

    def clear_history(self):
        """Очищает историю действий."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.debug("История очищена")

    def get_last_action_name(self) -> Optional[str]:
        """Возвращает название последнего действия."""
        if self._undo_stack:
            return self._undo_stack[-1].name
        return None


# === Конкретные действия ===

class AddPersonAction(UndoAction):
    """Действие: добавление персоны."""

    def __init__(self, person_id: str, person_data: Dict[str, Any]):
        super().__init__("Добавление персоны")
        self.person_id = person_id
        self.person_data = person_data

    def undo(self, context: Any) -> bool:
        if self.person_id in context.persons:
            self.person_data = self._serialize_person(context.persons[self.person_id])
            del context.persons[self.person_id]
            context.mark_modified()
            return True
        return False

    def redo(self, context: Any) -> bool:
        from models import Person
        person = self._deserialize_person(self.person_data)
        person.id = self.person_id
        context.persons[self.person_id] = person
        context.mark_modified()
        return True

    def _serialize_person(self, person: Any) -> Dict[str, Any]:
        if not person:
            return {}
        return {
            "name": person.name,
            "surname": person.surname,
            "patronymic": person.patronymic,
            "birth_date": person.birth_date,
            "gender": person.gender,
            "is_deceased": person.is_deceased,
            "death_date": person.death_date,
            "maiden_name": person.maiden_name,
            "parents": list(person.parents),
            "children": list(person.children),
            "spouse_ids": list(person.spouse_ids),
        }

    def _deserialize_person(self, data: Dict[str, Any]) -> Any:
        from models import Person
        if not data:
            return None
        p = Person(
            name=data.get("name", ""),
            surname=data.get("surname", ""),
            patronymic=data.get("patronymic", ""),
            birth_date=data.get("birth_date", ""),
            gender=data.get("gender", ""),
            is_deceased=data.get("is_deceased", False),
            death_date=data.get("death_date", ""),
            maiden_name=data.get("maiden_name", ""),
        )
        p.parents = set(data.get("parents", []))
        p.children = set(data.get("children", []))
        p.spouse_ids = set(data.get("spouse_ids", []))
        return p


class DeletePersonAction(UndoAction):
    """Действие: удаление персоны."""

    def __init__(self, person_id: str):
        super().__init__("Удаление персоны")
        self.person_id = person_id
        self.person_data = None
        self.connections = None

    def undo(self, context: Any) -> bool:
        from models import Person
        if self.person_data and self.connections:
            person = self._deserialize_person(self.person_data)
            person.id = self.person_id
            context.persons[self.person_id] = person

            # Восстанавливаем связи
            self._restore_connections(context, self.connections)
            context.mark_modified()
            return True
        return False

    def redo(self, context: Any) -> bool:
        if self.person_id in context.persons:
            # Сохраняем данные для undo
            self.person_data = self._serialize_person(context.persons[self.person_id])
            self.connections = self._save_connections(context, self.person_id)

            del context.persons[self.person_id]
            context.mark_modified()
            return True
        return False

    def _serialize_person(self, person: Any) -> Dict[str, Any]:
        return {
            "name": person.name,
            "surname": person.surname,
            "patronymic": person.patronymic,
            "birth_date": person.birth_date,
            "gender": person.gender,
            "is_deceased": person.is_deceased,
            "death_date": person.death_date,
            "maiden_name": person.maiden_name,
            "parents": list(person.parents),
            "children": list(person.children),
            "spouse_ids": list(person.spouse_ids),
        }

    def _deserialize_person(self, data: Dict[str, Any]) -> Any:
        from models import Person
        p = Person(
            name=data.get("name", ""),
            surname=data.get("surname", ""),
            patronymic=data.get("patronymic", ""),
            birth_date=data.get("birth_date", ""),
            gender=data.get("gender", ""),
            is_deceased=data.get("is_deceased", False),
            death_date=data.get("death_date", ""),
            maiden_name=data.get("maiden_name", ""),
        )
        p.parents = set(data.get("parents", []))
        p.children = set(data.get("children", []))
        p.spouse_ids = set(data.get("spouse_ids", []))
        return p

    def _save_connections(self, context: Any, person_id: str) -> Dict[str, Any]:
        """Сохраняет связи удаляемой персоны для восстановления."""
        person = context.persons.get(person_id)
        if not person:
            return {}

        connections = {
            "parents": [],
            "children": [],
            "spouses": [],
        }

        # Сохраняем связи с родителями
        for parent_id in person.parents:
            parent = context.persons.get(parent_id)
            if parent and person_id in parent.children:
                connections["parents"].append(str(parent_id))

        # Сохраняем связи с детьми
        for child_id in person.children:
            child = context.persons.get(child_id)
            if child and person_id in child.parents:
                connections["children"].append(str(child_id))

        # Сохраняем связи с супругами
        for spouse_id in person.spouse_ids:
            spouse = context.persons.get(spouse_id)
            if spouse and person_id in spouse.spouse_ids:
                connections["spouses"].append(str(spouse_id))

        return connections

    def _restore_connections(self, context: Any, connections: Dict[str, Any]):
        """Восстанавливает связи персоны."""
        person = context.persons.get(self.person_id)
        if not person:
            return

        for parent_id in connections.get("parents", []):
            parent = context.persons.get(parent_id)
            if parent:
                parent.children.add(self.person_id)
                person.parents.add(parent_id)

        for child_id in connections.get("children", []):
            child = context.persons.get(child_id)
            if child:
                child.parents.add(self.person_id)
                person.children.add(child_id)

        for spouse_id in connections.get("spouses", []):
            spouse = context.persons.get(spouse_id)
            if spouse:
                spouse.spouse_ids.add(self.person_id)
                person.spouse_ids.add(spouse_id)


class EditPersonAction(UndoAction):
    """Действие: редактирование персоны."""

    def __init__(self, person_id: str, old_data: Dict[str, Any], new_data: Dict[str, Any]):
        super().__init__("Редактирование персоны")
        self.person_id = person_id
        self.old_data = old_data
        self.new_data = new_data

    def undo(self, context: Any) -> bool:
        from models import Person
        if self.person_id not in context.persons:
            return False

        person = context.persons[self.person_id]
        self._apply_data(person, self.old_data)
        context.mark_modified()
        return True

    def redo(self, context: Any) -> bool:
        from models import Person
        if self.person_id not in context.persons:
            return False

        person = context.persons[self.person_id]
        self._apply_data(person, self.new_data)
        context.mark_modified()
        return True

    def _apply_data(self, person: Any, data: Dict[str, Any]):
        """Применяет данные к персоне."""
        for key, value in data.items():
            if hasattr(person, key):
                setattr(person, key, value)


class AddMarriageAction(UndoAction):
    """Действие: добавление брака."""

    def __init__(self, person_id1: str, person_id2: str):
        super().__init__("Добавление брака")
        self.person_id1 = str(person_id1)
        self.person_id2 = str(person_id2)

    def undo(self, context: Any) -> bool:
        p1 = context.persons.get(self.person_id1)
        p2 = context.persons.get(self.person_id2)

        if p1 and p2:
            p1.spouse_ids.discard(self.person_id2)
            p2.spouse_ids.discard(self.person_id1)

            marriage = tuple(sorted([self.person_id1, self.person_id2]))
            context.marriages.discard(marriage)
            context.mark_modified()
            return True
        return False

    def redo(self, context: Any) -> bool:
        p1 = context.persons.get(self.person_id1)
        p2 = context.persons.get(self.person_id2)

        if p1 and p2:
            p1.spouse_ids.add(self.person_id2)
            p2.spouse_ids.add(self.person_id1)

            marriage = tuple(sorted([self.person_id1, self.person_id2]))
            context.marriages.add(marriage)
            context.mark_modified()
            return True
        return False


class RemoveMarriageAction(UndoAction):
    """Действие: удаление брака."""

    def __init__(self, person_id1: str, person_id2: str):
        super().__init__("Удаление брака")
        self.person_id1 = str(person_id1)
        self.person_id2 = str(person_id2)

    def undo(self, context: Any) -> bool:
        p1 = context.persons.get(self.person_id1)
        p2 = context.persons.get(self.person_id2)

        if p1 and p2:
            p1.spouse_ids.add(self.person_id2)
            p2.spouse_ids.add(self.person_id1)

            marriage = tuple(sorted([self.person_id1, self.person_id2]))
            context.marriages.add(marriage)
            context.mark_modified()
            return True
        return False

    def redo(self, context: Any) -> bool:
        p1 = context.persons.get(self.person_id1)
        p2 = context.persons.get(self.person_id2)

        if p1 and p2:
            p1.spouse_ids.discard(self.person_id2)
            p2.spouse_ids.discard(self.person_id1)

            marriage = tuple(sorted([self.person_id1, self.person_id2]))
            context.marriages.discard(marriage)
            context.mark_modified()
            return True
        return False
