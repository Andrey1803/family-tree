# -*- coding: utf-8 -*-
"""Тест для отладки родства на простых примерах."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

from models import FamilyTreeModel
from kinship import calculate_kinship, _get_kinship, _get_ancestors

def test_case(name, setup_func, center_name, expected):
    """Тестирует один случай."""
    print(f"\n{'='*70}")
    print(f"ТЕСТ: {name}")
    print(f"{'='*70}")
    
    model = FamilyTreeModel()
    id_map = setup_func(model)
    
    # Находим ID центра по имени
    center_id = None
    for pid, person in model.persons.items():
        if person.name == center_name:
            center_id = pid
            break
    
    if not center_id:
        print(f"ERROR: Центр '{center_name}' не найден!")
        return False
    
    # Вычисляем родство
    relationships = calculate_kinship(model, center_id)
    
    # Проверяем ожидания
    all_ok = True
    for person_name, expected_rel in expected.items():
        # Находим ID персоны
        pid = None
        for p_id, p in model.persons.items():
            if p.name == person_name:
                pid = p_id
                break
        
        if pid is None:
            print(f"  ✗ {person_name}: НЕ НАЙДЕН В МОДЕЛИ")
            all_ok = False
            continue
        
        actual_rel = relationships.get(pid, "НЕ ОПРЕДЕЛЕНО")
        status = "OK" if actual_rel == expected_rel else "FAIL"
        if actual_rel != expected_rel:
            all_ok = False
        
        print(f"  {status} | {person_name}: ожидалось '{expected_rel}', получено '{actual_rel}'")
    
    return all_ok


# === ТЕСТОВЫЕ СЦЕНАРИИ ===

def setup_basic_family(model):
    """Базовая семья: родители, дети, братья."""
    id_map = {}
    id_map['Отец'] = model.add_person("Отец", "Иванов", "", "", "Мужской")[0]
    id_map['Мать'] = model.add_person("Мать", "Иванова", "", "", "Женский")[0]
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['Брат'] = model.add_person("Брат", "Иванов", "", "", "Мужской")[0]
    id_map['Сестра'] = model.add_person("Сестра", "Иванова", "", "", "Женский")[0]
    id_map['Сын'] = model.add_person("Сын", "Иванов", "", "", "Мужской")[0]
    id_map['Дочь'] = model.add_person("Дочь", "Иванова", "", "", "Женский")[0]
    
    model.add_parent(id_map['Я'], id_map['Отец'])
    model.add_parent(id_map['Я'], id_map['Мать'])
    model.add_parent(id_map['Брат'], id_map['Отец'])
    model.add_parent(id_map['Брат'], id_map['Мать'])
    model.add_parent(id_map['Сестра'], id_map['Отец'])
    model.add_parent(id_map['Сестра'], id_map['Мать'])
    model.add_parent(id_map['Сын'], id_map['Я'])
    model.add_parent(id_map['Дочь'], id_map['Я'])
    model.add_marriage(id_map['Отец'], id_map['Мать'])
    
    return id_map


def setup_uncle_aunt(model):
    """Семья с дядями и тётями."""
    id_map = {}
    id_map['Дед'] = model.add_person("Дед", "Иванов", "", "", "Мужской")[0]
    id_map['Бабушка'] = model.add_person("Бабушка", "Иванова", "", "", "Женский")[0]
    id_map['Отец'] = model.add_person("Отец", "Иванов", "", "", "Мужской")[0]
    id_map['Дядя'] = model.add_person("Дядя", "Иванов", "", "", "Мужской")[0]
    id_map['Тётя'] = model.add_person("Тётя", "Иванова", "", "", "Женский")[0]
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['ДвоюродныйБрат'] = model.add_person("ДвоюродныйБрат", "Иванов", "", "", "Мужской")[0]
    
    model.add_parent(id_map['Отец'], id_map['Дед'])
    model.add_parent(id_map['Отец'], id_map['Бабушка'])
    model.add_parent(id_map['Дядя'], id_map['Дед'])
    model.add_parent(id_map['Дядя'], id_map['Бабушка'])
    model.add_parent(id_map['Тётя'], id_map['Дед'])
    model.add_parent(id_map['Тётя'], id_map['Бабушка'])
    model.add_parent(id_map['Я'], id_map['Отец'])
    model.add_parent(id_map['ДвоюродныйБрат'], id_map['Тётя'])
    
    return id_map


def setup_cousins(model):
    """Двоюродные, троюродные братья."""
    id_map = {}
    id_map['Прадед'] = model.add_person("Прадед", "Иванов", "", "", "Мужской")[0]
    id_map['Дед1'] = model.add_person("Дед1", "Иванов", "", "", "Мужской")[0]
    id_map['Дед2'] = model.add_person("Дед2", "Иванов", "", "", "Мужской")[0]
    id_map['Отец'] = model.add_person("Отец", "Иванов", "", "", "Мужской")[0]
    id_map['Дядя'] = model.add_person("Дядя", "Иванов", "", "", "Мужской")[0]
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['ДвоюродныйБрат'] = model.add_person("ДвоюродныйБрат", "Иванов", "", "", "Мужской")[0]
    
    model.add_parent(id_map['Дед1'], id_map['Прадед'])
    model.add_parent(id_map['Дед2'], id_map['Прадед'])
    model.add_parent(id_map['Отец'], id_map['Дед1'])
    model.add_parent(id_map['Дядя'], id_map['Дед2'])
    model.add_parent(id_map['Я'], id_map['Отец'])
    model.add_parent(id_map['ДвоюродныйБрат'], id_map['Дядя'])
    
    return id_map


def setup_inlaws(model):
    """Свойственники (через супруга)."""
    id_map = {}
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['Жена'] = model.add_person("Жена", "Иванова", "", "", "Женский")[0]
    id_map['Тесть'] = model.add_person("Тесть", "Петров", "", "", "Мужской")[0]
    id_map['Теща'] = model.add_person("Теща", "Петрова", "", "", "Женский")[0]
    id_map['Шурин'] = model.add_person("Шурин", "Петров", "", "", "Мужской")[0]
    
    model.add_parent(id_map['Жена'], id_map['Тесть'])
    model.add_parent(id_map['Жена'], id_map['Теща'])
    model.add_parent(id_map['Шурин'], id_map['Тесть'])
    model.add_parent(id_map['Шурин'], id_map['Теща'])
    model.add_marriage(id_map['Я'], id_map['Жена'])
    
    return id_map


def setup_grandparents(model):
    """Деды, прадеды."""
    id_map = {}
    id_map['Прадед'] = model.add_person("Прадед", "Иванов", "", "", "Мужской")[0]
    id_map['Дед'] = model.add_person("Дед", "Иванов", "", "", "Мужской")[0]
    id_map['Отец'] = model.add_person("Отец", "Иванов", "", "", "Мужской")[0]
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['Сын'] = model.add_person("Сын", "Иванов", "", "", "Мужской")[0]
    id_map['Внук'] = model.add_person("Внук", "Иванов", "", "", "Мужской")[0]
    
    model.add_parent(id_map['Дед'], id_map['Прадед'])
    model.add_parent(id_map['Отец'], id_map['Дед'])
    model.add_parent(id_map['Я'], id_map['Отец'])
    model.add_parent(id_map['Сын'], id_map['Я'])
    model.add_parent(id_map['Внук'], id_map['Сын'])
    
    return id_map


def setup_grandnephew(model):
    """Внучатые племянники."""
    id_map = {}
    id_map['Родитель'] = model.add_person("Родитель", "Иванов", "", "", "Мужской")[0]
    id_map['Я'] = model.add_person("Я", "Иванов", "", "", "Мужской")[0]
    id_map['Брат'] = model.add_person("Брат", "Иванов", "", "", "Мужской")[0]
    id_map['Племянница'] = model.add_person("Племянница", "Иванова", "", "", "Женский")[0]
    id_map['СынПлемянницы'] = model.add_person("СынПлемянницы", "Иванов", "", "", "Мужской")[0]
    id_map['ВнукПлемянницы'] = model.add_person("ВнукПлемянницы", "Иванов", "", "", "Мужской")[0]
    
    model.add_parent(id_map['Я'], id_map['Родитель'])
    model.add_parent(id_map['Брат'], id_map['Родитель'])
    model.add_parent(id_map['Племянница'], id_map['Брат'])
    model.add_parent(id_map['СынПлемянницы'], id_map['Племянница'])
    model.add_parent(id_map['ВнукПлемянницы'], id_map['СынПлемянницы'])
    
    return id_map


# === ЗАПУСК ТЕСТОВ ===

if __name__ == "__main__":
    results = []
    
    # Тест 1: Базовая семья (центр = Я)
    results.append(("Базовая семья", test_case(
        "Базовая семья",
        setup_basic_family,
        "Я",
        {
            "Отец": "Отец",
            "Мать": "Мать",
            "Брат": "Брат",
            "Сестра": "Сестра",
            "Сын": "Сын",
            "Дочь": "Дочь",
        }
    )))
    
    # Тест 2: Дяди и тёти (центр = Я)
    results.append(("Дяди и тёти", test_case(
        "Дяди и тёти",
        setup_uncle_aunt,
        "Я",
        {
            "Дед": "Дед",
            "Бабушка": "Бабушка",
            "Отец": "Отец",
            "Дядя": "Дядя",
            "Тётя": "Тётя",
            "ДвоюродныйБрат": "Двоюродный брат",
        }
    )))
    
    # Тест 3: Двоюродные братья (центр = Я)
    results.append(("Двоюродные братья", test_case(
        "Двоюродные братья (общий прадед)",
        setup_cousins,
        "Я",
        {
            "Прадед": "Прадед",
            "Дед1": "Дед",
            "Дед2": "Двоюродный дед",
            "Отец": "Отец",
            "Дядя": "Двоюродный дядя",
            "ДвоюродныйБрат": "Троюродный брат",  # Общий прадед, оба в 3-м колене = троюродные
        }
    )))
    
    # Тест 4: Свойственники (центр = Я)
    results.append(("Свойственники", test_case(
        "Свойственники (через жену)",
        setup_inlaws,
        "Я",
        {
            "Жена": "Супруга",
            "Тесть": "Тесть",
            "Теща": "Теща",
            "Шурин": "Шурин",
        }
    )))
    
    # Тест 5: Деды и внуки (центр = Я)
    results.append(("Деды и внуки", test_case(
        "Деды и внуки",
        setup_grandparents,
        "Я",
        {
            "Прадед": "Прадед",
            "Дед": "Дед",
            "Отец": "Отец",
            "Сын": "Сын",
            "Внук": "Внук",
        }
    )))
    
    # Тест 6: Внучатые племянники
    results.append(("Внучатые племянники", test_case(
        "Внучатые племянники",
        setup_grandnephew,
        "Я",
        {
            "Родитель": "Отец",
            "Брат": "Брат",
            "Племянница": "Племянница",
            "СынПлемянницы": "Внучатый племянник",
            "ВнукПлемянницы": "Внучатый племянник 2-го колена",
        }
    )))
    
    # Итоги
    print(f"\n{'='*70}")
    print("ИТОГИ:")
    print(f"{'='*70}")
    for test_name, passed in results:
        status = "OK" if passed else "FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n{'='*70}")
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("ЕСТЬ ОШИБКИ - НУЖНО ИСПРАВИТЬ!")
    print(f"{'='*70}")
