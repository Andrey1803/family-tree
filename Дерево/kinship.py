# -*- coding: utf-8 -*-
"""
Надёжный модуль вычисления родства через общих предков.
"""


def calculate_kinship(model, center_id):
    """Вычисляет родство для всех персон относительно center_id."""
    if not center_id or center_id not in model.persons:
        return {}

    relationships = {}
    for pid in model.persons:
        if pid == center_id:
            continue
        rel = _get_kinship(model, center_id, pid)
        if rel:
            relationships[pid] = rel

    return relationships


def _get_kinship(model, center_id, person_id, depth=0):
    """Определяет родство person_id относительно center_id."""
    if depth > 10:  # Защита от рекурсии
        return None

    center = model.get_person(center_id)
    person = model.get_person(person_id)

    if not center or not person:
        return None

    # === 1. ПРЯМЫЕ СВЯЗИ ===
    if person_id in center.parents:
        return "Отец" if person.gender == "Мужской" else "Мать"

    if center_id in person.parents:
        return "Сын" if person.gender == "Мужской" else "Дочь"

    if person_id in center.spouse_ids or center_id in person.spouse_ids:
        return "Супруг" if person.gender == "Мужской" else "Супруга"

    # === 1.1 ПРЯМЫЕ ПОТОМКИ (внуки, правнуки) ===
    # Проверяем, является ли person потомком center
    for child_id in center.children:
        if child_id == person_id:
            return "Сын" if person.gender == "Мужской" else "Дочь"
        # Проверяем внуков через детей
        child = model.get_person(child_id)
        if child:
            for grandchild_id in child.children:
                if grandchild_id == person_id:
                    return "Внук" if person.gender == "Мужской" else "Внучка"
                # Проверяем правнуков через внуков
                grandchild = model.get_person(grandchild_id)
                if grandchild:
                    for great_grandchild_id in grandchild.children:
                        if great_grandchild_id == person_id:
                            return "Правнук" if person.gender == "Мужской" else "Правнучка"
                    
                    # Рекурсивно для 4+ поколения от grandchild
                    # grandchild = 2-е колено, его дети = 3-е (правнуки), внуки = 4-е
                    result = _get_direct_descendant_relation(model, grandchild, person_id, 3)
                    if result:
                        return result

    # === 1.2 ПРЯМЫЕ ПРЕДКИ (деды, прадеды) ===
    for parent_id in center.parents:
        if parent_id == person_id:
            return "Отец" if person.gender == "Мужской" else "Мать"
        # Проверяем дедушку/бабушку через родителей (2-е колено)
        parent = model.get_person(parent_id)
        if parent:
            for grandparent_id in parent.parents:
                if grandparent_id == person_id:
                    return "Дед" if person.gender == "Мужской" else "Бабушка"
                # Проверяем прадеда через бабушку/дедушку (3-е колено)
                grandparent = model.get_person(grandparent_id)
                if grandparent:
                    for great_grandparent_id in grandparent.parents:
                        if great_grandparent_id == person_id:
                            return "Прадед" if person.gender == "Мужской" else "Прабабушка"
                    # Рекурсивно для 4+ поколения от grandparent
                    # grandparent = 2-е колено, его родители = 3-е (прадеды), деды = 4-е
                    result = _get_direct_ancestor_relation(model, grandparent, person_id, 3)
                    if result:
                        return result

    # === 2. КРОВНОЕ РОДСТВО (через общих предков) ===
    center_ancestors = _get_ancestors(model, center_id)
    person_ancestors = _get_ancestors(model, person_id)

    common = set(center_ancestors.keys()) & set(person_ancestors.keys())

    if common:
        # Ближайший общий предок
        best = min(common, key=lambda a: center_ancestors[a] + person_ancestors[a])
        c_level = center_ancestors[best]  # 1=родитель, 2=дед
        p_level = person_ancestors[best]

        return _by_levels(person.gender, p_level, c_level)

    # === 3. СВОЙСТВЕННИКИ (через супруга center) ===
    # Проверяем, является ли person родственником супруга center
    for center_spouse_id in center.spouse_ids:
        if center_spouse_id == person_id:
            continue
        center_spouse = model.get_person(center_spouse_id)
        if not center_spouse:
            continue
        
        # Проверяем, является ли person родителем супруга center
        if person_id in center_spouse.parents:
            return "Тесть" if person.gender == "Мужской" else "Теща"
        
        # Проверяем, является ли person братом/сестрой супруга center
        for spouse_parent_id in center_spouse.parents:
            spouse_parent = model.get_person(spouse_parent_id)
            if spouse_parent and person_id in spouse_parent.children:
                if person_id != center_spouse_id:  # Не сам супруг
                    return "Шурин" if person.gender == "Мужской" else "Золовка"
    
    # === 4. СВОЙСТВЕННИКИ (через супруга person) ===
    for spouse_id in person.spouse_ids:
        if spouse_id == center_id:
            continue
        spouse_rel = _get_kinship(model, center_id, spouse_id, depth + 1)
        if spouse_rel:
            return _inlaw_term(spouse_rel, person.gender)

    return None


def _get_ancestors(model, person_id):
    """Возвращает предков с уровнями: {id: level}, level=1 для родителя."""
    ancestors = {}
    queue = [(person_id, 0)]
    visited = {str(person_id)}

    while queue:
        current_id, level = queue.pop(0)
        current = model.get_person(current_id)
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


def _get_direct_descendant_relation(model, ancestor, person_id, generation):
    """Рекурсивно ищет прямого потомка. generation=2 для внука (2-е колено)."""
    if not ancestor:
        return None

    for child_id in ancestor.children:
        if child_id == person_id:
            if generation == 2:
                return "Внук" if model.get_person(person_id).gender == "Мужской" else "Внучка"
            elif generation == 3:
                return "Правнук" if model.get_person(person_id).gender == "Мужской" else "Правнучка"
            else:
                # 4+ поколение: Внук N-го колена
                return f"Внук {generation}-го колена" if model.get_person(person_id).gender == "Мужской" else f"Внучка {generation}-го колена"

        child = model.get_person(child_id)
        if child:
            result = _get_direct_descendant_relation(model, child, person_id, generation + 1)
            if result:
                return result

    return None


def _get_direct_ancestor_relation(model, descendant, person_id, generation):
    """Рекурсивно ищет прямого предка. generation=2 для деда/бабушки."""
    if not descendant:
        return None

    for parent_id in descendant.parents:
        if parent_id == person_id:
            if generation == 2:
                return "Дед" if model.get_person(person_id).gender == "Мужской" else "Бабушка"
            elif generation == 3:
                return "Прадед" if model.get_person(person_id).gender == "Мужской" else "Прабабушка"
            else:
                # 4+ поколение: Дед N-го колена
                return f"Дед {generation}-го колена" if model.get_person(person_id).gender == "Мужской" else f"Бабушка {generation}-го колена"

        parent = model.get_person(parent_id)
        if parent:
            result = _get_direct_ancestor_relation(model, parent, person_id, generation + 1)
            if result:
                return result

    return None


def _by_levels(gender, person_level, center_level):
    """
    Определяет родство по уровням до общего предка.
    level=1: родитель/ребёнок
    level=2: дед/внук
    level=3: прадед/правнук
    """
    diff = abs(person_level - center_level)

    # Один уровень = братья/сёстры или двоюродные/троюродные и т.д.
    if person_level == center_level:
        if person_level == 1:
            # Братья/сёстры на уровне родителей (общий предок — родитель)
            return "Брат" if gender == "Мужской" else "Сестра"
        elif person_level == 2:
            # Один уровень от общего деда = двоюродные братья/сёстры
            return "Двоюродный брат" if gender == "Мужской" else "Двоюродная сестра"
        elif person_level == 3:
            # Один уровень от общего прадеда = троюродные братья/сёстры
            return "Троюродный брат" if gender == "Мужской" else "Троюродная сестра"
        else:
            # Братья/сёстры на уровне 4+
            prefix = _cousin_type(person_level - 1)
            return prefix + "брат" if gender == "Мужской" else prefix + "сестра"

    # Разница 1 поколение
    if diff == 1:
        if person_level < center_level:
            # person старше - дядя/тётя или двоюродный дед/бабушка
            if person_level == 1 and center_level == 2:
                # Общий предок — родитель person, center на уровень ниже => дядя/тётя
                return "Дядя" if gender == "Мужской" else "Тётя"
            elif person_level == 1 and center_level > 2:
                # Общий предок — родитель person, center дальше => двоюродный/троюродный дядя
                if center_level == 3:
                    return "Двоюродный дядя" if gender == "Мужской" else "Двоюродная тётя"
                elif center_level == 4:
                    return "Троюродный дядя" if gender == "Мужской" else "Троюродная тётя"
                else:
                    prefix = _cousin_type(center_level - 2)
                    return prefix + "дядя" if gender == "Мужской" else prefix + "тётя"
            elif person_level == 2 and center_level == 3:
                # Общий предок — дед person, center на уровень ниже => двоюродный дядя/тётя
                return "Двоюродный дядя" if gender == "Мужской" else "Двоюродная тётя"
            elif person_level == 2:
                # Общий предок — дед person => двоюродный дед/бабушка
                return "Двоюродный дед" if gender == "Мужской" else "Двоюродная бабушка"
            else:
                # person_level >= 3 => Дед N-го колена
                return f"Дед {person_level}-го колена" if gender == "Мужской" else f"Бабушка {person_level}-го колена"
        else:
            # person младше - племянник/племянница или внучатый племянник
            if center_level == 1 and person_level == 2:
                # Общий предок — родитель center => племянник/племянница
                return "Племянник" if gender == "Мужской" else "Племянница"
            elif center_level == 1:
                # Общий предок — родитель center, person дальше => двоюродный/троюродный племянник
                if person_level == 3:
                    return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
                elif person_level == 4:
                    return "Троюродный племянник" if gender == "Мужской" else "Троюродная племянница"
                else:
                    return f"Племянник {person_level - 1}-го колена" if gender == "Мужской" else f"Племянница {person_level - 1}-го колена"
            elif center_level == 2 and person_level == 3:
                # Общий предок — дед center => двоюродный племянник/племянница
                return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
            elif center_level == 2:
                # Общий предок — дед center => двоюродный племянник/племянница
                return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
            else:
                # center_level >= 3 => Племянник N-го колена
                return f"Племянник {center_level}-го колена" if gender == "Мужской" else f"Племянница {center_level}-го колена"

    # Разница 2+ поколения = деды/внуки или двоюродные дяди/тёти
    if person_level < center_level:
        # person старше — дед/бабушка или двоюродный дед/бабушка
        if person_level == 1 and center_level == 2:
            # Общий предок — родитель person, center на 2 уровня ниже => дед/бабушка
            return "Дед" if gender == "Мужской" else "Бабушка"
        elif person_level == 1 and center_level > 2:
            # Общий предок — родитель person, center дальше => двоюродный дед/бабушка
            # center_level-1 = степень родства деда/бабушки
            if center_level == 3:
                return "Двоюродный дед" if gender == "Мужской" else "Двоюродная бабушка"
            elif center_level == 4:
                return "Троюродный дед" if gender == "Мужской" else "Троюродная бабушка"
            else:
                prefix = _cousin_type(center_level - 2)
                return prefix + "дед" if gender == "Мужской" else prefix + "бабушка"
        elif person_level == 2:
            # Общий предок — дед person => прадед/прабабушка
            return "Прадед" if gender == "Мужской" else "Прабабушка"
        else:
            # person_level >= 3 => Дед N-го колена
            return f"Дед {person_level + 1}-го колена" if gender == "Мужской" else f"Бабушка {person_level + 1}-го колена"
    else:
        # person младше — внук/внучка или правнук/правнучка
        if center_level == 1 and person_level == 2:
            # Общий предок — родитель center => внук/внучка (прямая линия)
            return "Внук" if gender == "Мужской" else "Внучка"
        elif center_level == 1 and person_level > 2:
            # Общий предок — родитель center, person дальше => это боковая линия (племянники)
            # person_level=3: сын племянника/племянницы = внучатый племянник
            # person_level=4: правнук племянника = внучатый племянник 2-го колена
            if person_level == 3:
                return "Внучатый племянник" if gender == "Мужской" else "Внучатая племянница"
            elif person_level == 4:
                return "Внучатый племянник 2-го колена" if gender == "Мужской" else "Внучатая племянница 2-го колена"
            else:
                return f"Внучатый племянник {person_level - 1}-го колена" if gender == "Мужской" else f"Внучатая племянница {person_level - 1}-го колена"
        elif center_level == 2:
            # Общий предок — дед center => правнук/правнучка (прямая линия) или двоюродный племянник
            if person_level == 3:
                return "Двоюродный племянник" if gender == "Мужской" else "Двоюродная племянница"
            else:
                return "Правнук" if gender == "Мужской" else "Правнучка"
        else:
            # center_level >= 3 => Внук N-го колена
            return f"Внук {center_level + 1}-го колена" if gender == "Мужской" else f"Внучка {center_level + 1}-го колена"


def _cousin_type(level):
    """Двоюродный, троюродный и т.д."""
    if level == 1:
        return "Двоюродный "
    elif level == 2:
        return "Троюродный "
    elif level == 3:
        return "Четыреюродный "
    else:
        return f"{level}-юродный "


def _inlaw_term(base_rel, gender):
    """Термин для свойственника."""
    # Прямые термины для свойственников
    inlaw_terms = {
        "Отец": "Тесть" if gender == "Мужской" else "Свекровь",
        "Мать": "Теща" if gender == "Женский" else "Свекор",
        "Брат": "Шурин" if gender == "Мужской" else "Свояченица",
        "Сестра": "Золовка" if gender == "Женский" else "Свояк",
    }
    
    # Проверяем точное совпадение
    if base_rel in inlaw_terms:
        return inlaw_terms[base_rel]
    
    # Остальные термины
    terms = {
        "Сын": "Невестка" if gender == "Женский" else "Зять",
        "Дочь": "Зять" if gender == "Мужской" else "Невестка",
        "Дядя": "Тётя" if gender == "Женский" else "Дядя",
        "Тётя": "Дядя" if gender == "Мужской" else "Тётя",
        "Племянник": "Невестка" if gender == "Женский" else "Зять",
        "Племянница": "Зять" if gender == "Мужской" else "Свояченица",
    }

    if base_rel in terms:
        return terms[base_rel]

    base_lower = base_rel.lower()
    if "брат" in base_lower or "дядя" in base_lower:
        return "Невестка" if gender == "Женский" else "Свояк"
    if "сестр" in base_lower or "тёт" in base_lower:
        return "Свояченица" if gender == "Женский" else "Зять"

    return "Свояк"
