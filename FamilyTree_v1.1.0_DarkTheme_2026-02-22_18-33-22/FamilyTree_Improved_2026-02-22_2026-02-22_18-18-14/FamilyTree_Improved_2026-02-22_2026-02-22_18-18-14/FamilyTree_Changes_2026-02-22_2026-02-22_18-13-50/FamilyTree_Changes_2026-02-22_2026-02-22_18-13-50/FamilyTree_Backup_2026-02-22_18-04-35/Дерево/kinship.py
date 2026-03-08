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
    if depth > 3:  # Защита от рекурсии
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
    
    # === 3. СВОЙСТВЕННИКИ (через супруга) ===
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


def _by_levels(gender, person_level, center_level):
    """Определяет родство по уровням до общего предка."""
    diff = abs(person_level - center_level)
    
    # Один уровень = братья/сёстры
    if person_level == center_level:
        if person_level == 1:
            return "Брат" if gender == "Мужской" else "Сестра"
        else:
            prefix = _cousin_type(person_level - 1)
            return prefix + ("Брат" if gender == "Мужской" else "Сестра")
    
    # Разница 1 поколение
    if diff == 1:
        if person_level < center_level:
            # person старше - дядя/тётя
            prefix = _cousin_type(person_level - 1) if person_level > 1 else ""
            return prefix + ("Дядя" if gender == "Мужской" else "Тётя")
        else:
            # person младше - племянник/племянница
            prefix = _cousin_type(center_level - 1) if center_level > 1 else ""
            return prefix + ("Племянник" if gender == "Мужской" else "Племянница")
    
    # Разница 2+ поколения = деды/внуки
    if person_level < center_level:
        prefix = _grand_prefix(person_level)
        return prefix + ("Дед" if gender == "Мужской" else "Бабка")
    else:
        prefix = _grand_prefix(center_level)
        return prefix + ("Внук" if gender == "Мужской" else "Внучка")


def _cousin_type(level):
    """Двоюродный, троюродный и т.д."""
    if level == 1:
        return "Двоюродный "
    elif level == 2:
        return "Троюродный "
    elif level == 3:
        return "Четыреюродный "
    else:
        return f"{level}юродный "


def _grand_prefix(level):
    """пра-, прапра- для дедов/внуков"""
    if level <= 1:
        return ""
    elif level == 2:
        return "пра"
    else:
        return "пра" * (level - 1)


def _inlaw_term(base_rel, gender):
    """Термин для свойственника."""
    terms = {
        "Сын": "Невестка" if gender == "Женский" else "Зять",
        "Дочь": "Зять" if gender == "Мужской" else "Невестка",
        "Отец": "Мачеха" if gender == "Женский" else "Отчим",
        "Мать": "Отчим" if gender == "Мужской" else "Мачеха",
        "Брат": "Невестка" if gender == "Женский" else "Зять",
        "Сестра": "Зять" if gender == "Мужской" else "Свояченица",
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
