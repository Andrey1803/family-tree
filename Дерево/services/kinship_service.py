# -*- coding: utf-8 -*-
"""
Сервис вычисления родства.
Расширяет базовый kinship.py с улучшенной архитектурой.
"""

import logging
from typing import Dict, Optional, List, Set, Any

logger = logging.getLogger(__name__)


class KinshipService:
    """Сервис для вычисления родственных связей."""

    def __init__(self, model: Any = None):
        """
        Инициализация сервиса.

        Args:
            model: Модель дерева для операций.
        """
        self.model = model

    def set_model(self, model: Any):
        """Устанавливает модель дерева."""
        self.model = model

    def calculate_kinship(self, center_id: str) -> Dict[str, str]:
        """
        Вычисляет родство для всех персон относительно center_id.

        Args:
            center_id: ID центральной персоны.

        Returns:
            Словарь {person_id: relationship}.
        """
        if not self.model or not center_id or center_id not in self.model.persons:
            return {}

        relationships = {}
        for pid in self.model.persons:
            if pid == center_id:
                continue
            rel = self._get_kinship(center_id, pid)
            if rel:
                relationships[pid] = rel

        return relationships

    def get_kinship(self, center_id: str, person_id: str) -> Optional[str]:
        """
        Определяет родство person_id относительно center_id.

        Args:
            center_id: ID центральной персоны.
            person_id: ID персоны для определения родства.

        Returns:
            Строка с описанием родства или None.
        """
        if not self.model:
            return None
        return self._get_kinship(center_id, person_id)

    def _get_kinship(self, center_id: str, person_id: str, depth: int = 0) -> Optional[str]:
        """Определяет родство person_id относительно center_id."""
        if depth > 5:  # Защита от рекурсии
            return None

        center = self.model.get_person(center_id)
        person = self.model.get_person(person_id)

        if not center or not person:
            return None

        # === 1. ПРЯМЫЕ СВЯЗИ ===
        if person_id in center.parents:
            return "Отец" if person.gender == "Мужской" else "Мать"

        if center_id in person.parents:
            return "Сын" if person.gender == "Мужской" else "Дочь"

        if person_id in center.spouse_ids or center_id in person.spouse_ids:
            return "Супруг" if person.gender == "Мужской" else "Супруга"

        # === 2. КРОВНОЕ РОДСТВО (через общих предков) ===
        center_ancestors = self._get_ancestors(center_id)
        person_ancestors = self._get_ancestors(person_id)

        common = set(center_ancestors.keys()) & set(person_ancestors.keys())

        if common:
            # Ближайший общий предок
            best = min(common, key=lambda a: center_ancestors[a] + person_ancestors[a])
            c_level = center_ancestors[best]  # 1=родитель, 2=дед
            p_level = person_ancestors[best]

            return self._by_levels(person.gender, p_level, c_level)

        # === 3. СВОЙСТВЕННИКИ (через супруга center) ===
        # Проверяем, является ли person родственником супруга center
        for center_spouse_id in center.spouse_ids:
            if center_spouse_id == person_id:
                continue
            center_spouse = self.model.get_person(center_spouse_id)
            if not center_spouse:
                continue
            
            # Проверяем, является ли person родителем супруга center
            if person_id in center_spouse.parents:
                return "Тесть" if person.gender == "Мужской" else "Теща"
            
            # Проверяем, является ли person братом/сестрой супруга center
            for spouse_parent_id in center_spouse.parents:
                spouse_parent = self.model.get_person(spouse_parent_id)
                if spouse_parent and person_id in spouse_parent.children:
                    if person_id != center_spouse_id:  # Не сам супруг
                        return "Шурин" if person.gender == "Мужской" else "Золовка"
        
        # === 4. СВОЙСТВЕННИКИ (через супруга person) ===
        for spouse_id in person.spouse_ids:
            if spouse_id == center_id:
                continue
            spouse_rel = self._get_kinship(center_id, spouse_id, depth + 1)
            if spouse_rel:
                return self._inlaw_term(spouse_rel, person.gender)

        return None

    def _get_ancestors(self, person_id: str) -> Dict[str, int]:
        """
        Возвращает предков с уровнями: {id: level}, level=1 для родителя.

        Args:
            person_id: ID персоны.

        Returns:
            Словарь {ancestor_id: level}.
        """
        ancestors = {}
        queue = [(person_id, 0)]
        visited = {str(person_id)}

        while queue:
            current_id, level = queue.pop(0)
            current = self.model.get_person(current_id)
            if not current:
                continue

            if current.parents:
                for parent_id in current.parents:
                    pid_str = str(parent_id)
                    if pid_str not in visited:
                        visited.add(pid_str)
                        ancestors[pid_str] = level + 1
                        queue.append((pid_str, level + 1))

        return ancestors

    def _by_levels(self, gender: str, person_level: int, center_level: int) -> str:
        """
        Определяет родство по уровням до общего предка.

        Args:
            gender: Пол персоны.
            person_level: Уровень персоны до общего предка.
            center_level: Уровень центральной персоны до общего предка.

        Returns:
            Строка с описанием родства.
        """
        diff = abs(person_level - center_level)

        # Один уровень = братья/сёстры
        if person_level == center_level:
            if person_level == 1:
                return "Брат" if gender == "Мужской" else "Сестра"
            elif person_level == 2:
                return "Двоюродный брат" if gender == "Мужской" else "Двоюродная сестра"
            elif person_level == 3:
                return "Троюродный брат" if gender == "Мужской" else "Троюродная сестра"
            else:
                cousin_term = self._cousin_term(person_level - 1)
                return cousin_term + ("Брат" if gender == "Мужской" else "Сестра")

        # Разница 1 поколение
        if diff == 1:
            if person_level < center_level:
                # person старше
                if person_level == 1 and center_level == 2:
                    return "Дядя" if gender == "Мужской" else "Тётя"
                elif person_level == 1 and center_level > 2:
                    if center_level == 3:
                        return "Двоюродный дядя" if gender == "Мужской" else "Двоюродная тётя"
                    elif center_level == 4:
                        return "Троюродный дядя" if gender == "Мужской" else "Троюродная тётя"
                    else:
                        prefix = self._cousin_term(center_level - 2)
                        return prefix + ("дядя" if gender == "Мужской" else "тётя")
                elif person_level == 2 and center_level == 3:
                    return "Двоюродный дядя" if gender == "Мужской" else "Двоюродная тётя"
                elif person_level == 2:
                    return "Двоюродный дед" if gender == "Мужской" else "Двоюродная бабушка"
                else:
                    return f"Дед {person_level}-го колена" if gender == "Мужской" else f"Бабушка {person_level}-го колена"
            else:
                # person младше
                if center_level == 1 and person_level == 2:
                    return "Племянник" if gender == "Мужской" else "Племянница"
                elif center_level == 1:
                    if person_level == 3:
                        return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
                    elif person_level == 4:
                        return "Троюродный племянник" if gender == "Мужской" else "Троюродная племянница"
                    else:
                        return f"Племянник {person_level - 1}-го колена" if gender == "Мужской" else f"Племянница {person_level - 1}-го колена"
                elif center_level == 2 and person_level == 3:
                    return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
                elif center_level == 2:
                    return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
                else:
                    return f"Племянник {center_level}-го колена" if gender == "Мужской" else f"Племянница {center_level}-го колена"

        # Разница 2+ поколения
        if person_level < center_level:
            # person старше
            if person_level == 1 and center_level == 2:
                return "Дед" if gender == "Мужской" else "Бабушка"
            elif person_level == 1 and center_level > 2:
                if center_level == 3:
                    return "Двоюродный дед" if gender == "Мужской" else "Двоюродная бабушка"
                elif center_level == 4:
                    return "Троюродный дед" if gender == "Мужской" else "Троюродная бабушка"
                else:
                    prefix = self._cousin_term(center_level - 2)
                    return prefix + ("дед" if gender == "Мужской" else "бабушка")
            elif person_level == 2:
                return "Прадед" if gender == "Мужской" else "Прабабушка"
            else:
                return f"Дед {person_level + 1}-го колена" if gender == "Мужской" else f"Бабушка {person_level + 1}-го колена"
        else:
            # person младше
            if center_level == 1 and person_level == 2:
                return "Внук" if gender == "Мужской" else "Внучка"
            elif center_level == 1 and person_level > 2:
                # Боковая линия (племянники)
                if person_level == 3:
                    return "Внучатый племянник" if gender == "Мужской" else "Внучатая племянница"
                elif person_level == 4:
                    return "Внучатый племянник 2-го колена" if gender == "Мужской" else "Внучатая племянница 2-го колена"
                else:
                    return f"Внучатый племянник {person_level - 1}-го колена" if gender == "Мужской" else f"Внучатая племянница {person_level - 1}-го колена"
            elif center_level == 2:
                if person_level == 3:
                    return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
                else:
                    return "Правнук" if gender == "Мужской" else "Правнучка"
            else:
                return f"Внук {center_level + 1}-го колена" if gender == "Мужской" else f"Внучка {center_level + 1}-го колена"

    def _cousin_term(self, level: int) -> str:
        """
        Возвращает термин для двоюродного родства.

        Args:
            level: Уровень (1=двоюродный, 2=троюродный, etc.)

        Returns:
            Строка с термином.
        """
        if level == 1:
            return "Двоюродный "
        elif level == 2:
            return "Троюродный "
        elif level == 3:
            return "Четвероюродный "
        else:
            return f"{level}-юродный "

    def _inlaw_term(self, relationship: str, gender: str) -> str:
        """
        Добавляет приставку для свойственников.

        Args:
            relationship: Базовое родство.
            gender: Пол персоны.

        Returns:
            Строка с термином для свойственника.
        """
        # Прямые термины для свойственников
        inlaw_terms = {
            "Отец": "Тесть" if gender == "Мужской" else "Свекровь",
            "Мать": "Теща" if gender == "Женский" else "Свекор",
            "Брат": "Шурин" if gender == "Мужской" else "Свояченица",
            "Сестра": "Золовка" if gender == "Женский" else "Свояк",
        }
        
        if relationship in inlaw_terms:
            return inlaw_terms[relationship]
        
        # Остальные термины
        terms = {
            "Сын": "Невестка" if gender == "Женский" else "Зять",
            "Дочь": "Зять" if gender == "Мужской" else "Невестка",
            "Дядя": "Тётя" if gender == "Женский" else "Дядя",
            "Тётя": "Дядя" if gender == "Мужской" else "Тётя",
            "Племянник": "Невестка" if gender == "Женский" else "Зять",
            "Племянница": "Зять" if gender == "Мужской" else "Свояченица",
        }

        if relationship in terms:
            return terms[relationship]

        base_lower = relationship.lower()
        if "брат" in base_lower or "дядя" in base_lower:
            return "Невестка" if gender == "Женский" else "Свояк"
        if "сестр" in base_lower or "тёт" in base_lower:
            return "Свояченица" if gender == "Женский" else "Зять"

        return "Свояк"

    def get_all_ancestors(self, person_id: str) -> List[str]:
        """
        Возвращает список всех предков персоны.

        Args:
            person_id: ID персоны.

        Returns:
            Список ID предков.
        """
        if not self.model:
            return []

        ancestors = self._get_ancestors(person_id)
        return list(ancestors.keys())

    def get_all_descendants(self, person_id: str) -> List[str]:
        """
        Возвращает список всех потомков персоны.

        Args:
            person_id: ID персоны.

        Returns:
            Список ID потомков.
        """
        if not self.model:
            return []

        descendants = {}
        queue = [(person_id, 0)]
        visited = {str(person_id)}

        while queue:
            current_id, level = queue.pop(0)
            current = self.model.get_person(current_id)
            if not current:
                continue

            if current.children:
                for child_id in current.children:
                    cid_str = str(child_id)
                    if cid_str not in visited:
                        visited.add(cid_str)
                        descendants[cid_str] = level + 1
                        queue.append((cid_str, level + 1))

        return list(descendants.keys())

    def find_common_ancestors(self, person_id1: str, person_id2: str) -> List[str]:
        """
        Находит общих предков двух персон.

        Args:
            person_id1: ID первой персоны.
            person_id2: ID второй персоны.

        Returns:
            Список ID общих предков.
        """
        if not self.model:
            return []

        ancestors1 = self._get_ancestors(person_id1)
        ancestors2 = self._get_ancestors(person_id2)

        common = set(ancestors1.keys()) & set(ancestors2.keys())
        return list(common)

    def is_blood_relative(self, person_id1: str, person_id2: str) -> bool:
        """
        Проверяет, являются ли персоны кровными родственниками.

        Args:
            person_id1: ID первой персоны.
            person_id2: ID второй персоны.

        Returns:
            True если кровные родственники.
        """
        return len(self.find_common_ancestors(person_id1, person_id2)) > 0
