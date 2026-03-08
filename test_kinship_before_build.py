# -*- coding: utf-8 -*-
"""Тест логики родства."""

import sys
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

from models import FamilyTreeModel
from kinship import calculate_kinship

def test_kinship():
    """Проверка расчёта родства."""
    model = FamilyTreeModel()
    
    # Создаём тестовое дерево:
    # Я (center) -> Отец -> Дед -> Прадед
    # Я -> Сын -> Внук -> Правнук
    # Я -> Брат
    # Дед -> Брат (Двоюродный дед)
    
    # Добавляем персоны
    id_map = {}
    result = model.add_person("Я", "Тестов", "", "", "Мужской")
    print(f"add_person ME: {result}")
    id_map['ME'] = result[0]
    result = model.add_person("Отец", "Тестов", "", "", "Мужской")
    print(f"add_person FATHER: {result}")
    id_map['FATHER'] = result[0]
    result = model.add_person("Дед", "Тестов", "", "", "Мужской")
    print(f"add_person GRANDFATHER: {result}")
    id_map['GRANDFATHER'] = result[0]
    result = model.add_person("Прадед", "Тестов", "", "", "Мужской")
    print(f"add_person GREAT_GRANDFATHER: {result}")
    id_map['GREAT_GRANDFATHER'] = result[0]
    result = model.add_person("Сын", "Тестов", "", "", "Мужской")
    print(f"add_person SON: {result}")
    id_map['SON'] = result[0]
    result = model.add_person("Внук", "Тестов", "", "", "Мужской")
    print(f"add_person GRANDSON: {result}")
    id_map['GRANDSON'] = result[0]
    result = model.add_person("Правнук", "Тестов", "", "", "Мужской")
    print(f"add_person GREAT_GRANDSON: {result}")
    id_map['GREAT_GRANDSON'] = result[0]
    result = model.add_person("Брат", "Тестов", "", "", "Мужской")
    print(f"add_person BROTHER: {result}")
    id_map['BROTHER'] = result[0]
    result = model.add_person("Дядя", "Тестов", "", "", "Мужской")
    print(f"add_person UNCLE: {result}")
    id_map['UNCLE'] = result[0]
    result = model.add_person("Двоюродный дед", "Тестов", "", "", "Мужской")
    print(f"add_person COUSIN_GRANDFATHER: {result}")
    id_map['COUSIN_GRANDFATHER'] = result[0]
    
    print(f"\npersons keys: {list(model.persons.keys())}")
    
    # Устанавливаем связи (родители)
    print("Установка связей:")
    r = model.add_parent(id_map['ME'], id_map['FATHER'])
    print(f"  ME <- FATHER: {r}")
    r = model.add_parent(id_map['FATHER'], id_map['GRANDFATHER'])
    print(f"  FATHER <- GRANDFATHER: {r}")
    r = model.add_parent(id_map['GRANDFATHER'], id_map['GREAT_GRANDFATHER'])
    print(f"  GRANDFATHER <- GREAT_GRANDFATHER: {r}")
    r = model.add_parent(id_map['SON'], id_map['ME'])
    print(f"  SON <- ME: {r}")
    r = model.add_parent(id_map['GRANDSON'], id_map['SON'])
    print(f"  GRANDSON <- SON: {r}")
    r = model.add_parent(id_map['GREAT_GRANDSON'], id_map['GRANDSON'])
    print(f"  GREAT_GRANDSON <- GRANDSON: {r}")
    
    # Брат (общий отец с ME)
    r = model.add_parent(id_map['BROTHER'], id_map['FATHER'])
    print(f"  BROTHER <- FATHER: {r}")
    
    # Дядя (брат отца, общий дед)
    r = model.add_parent(id_map['UNCLE'], id_map['GRANDFATHER'])
    print(f"  UNCLE <- GRANDFATHER: {r}")
    
    # Двоюродный дед (брат деда, общий прадед)
    r = model.add_parent(id_map['COUSIN_GRANDFATHER'], id_map['GREAT_GRANDFATHER'])
    print(f"  COUSIN_GRANDFATHER <- GREAT_GRANDFATHER: {r}")
    
    # Вычисляем родство относительно ME
    relationships = calculate_kinship(model, id_map['ME'])
    
    # Отладка: проверим ancestors
    from kinship import _get_ancestors
    
    # Проверка связей
    print("\nОТЛАДКА СВЯЗЕЙ:")
    me = model.get_person(id_map['ME'])
    print(f"ME parents: {me.parents if me else 'None'}")
    father = model.get_person(id_map['FATHER'])
    print(f"FATHER parents: {father.parents if father else 'None'}")
    grandfather = model.get_person(id_map['GRANDFATHER'])
    print(f"GRANDFATHER parents: {grandfather.parents if grandfather else 'None'}")
    
    print("\nОТЛАДКА:")
    me_ancestors = _get_ancestors(model, id_map['ME'])
    cousin_ancestors = _get_ancestors(model, id_map['COUSIN_GRANDFATHER'])
    print(f"ME ancestors: {me_ancestors}")
    print(f"COUSIN_GRANDFATHER ancestors: {cousin_ancestors}")
    common = set(me_ancestors.keys()) & set(cousin_ancestors.keys())
    print(f"Common ancestors: {common}")
    for a in common:
        print(f"  {a}: ME level={me_ancestors[a]}, COUSIN level={cousin_ancestors[a]}")
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТА РОДСТВА (относительно 'Я'):")
    print("=" * 60)
    
    expected = {
        id_map['FATHER']: "Отец",
        id_map['GRANDFATHER']: "Дед",
        id_map['GREAT_GRANDFATHER']: "Прадед",
        id_map['SON']: "Сын",
        id_map['GRANDSON']: "Внук",
        id_map['GREAT_GRANDSON']: "Правнук",
        id_map['BROTHER']: "Брат",
        id_map['UNCLE']: "Дядя",
        id_map['COUSIN_GRANDFATHER']: "Двоюродный дядя",  # Брат деда
    }
    
    all_passed = True
    for pid, expected_rel in expected.items():
        actual_rel = relationships.get(pid, "НЕ НАЙДЕНО")
        status = "OK" if actual_rel == expected_rel else "FAIL"
        if actual_rel != expected_rel:
            all_passed = False
        print(f"{status} {expected_rel}: Ожидалось '{expected_rel}', Получено '{actual_rel}'")
    
    print("=" * 60)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("ЕСТЬ ОШИБКИ!")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_kinship()
    sys.exit(0 if success else 1)
