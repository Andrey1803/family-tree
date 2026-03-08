# -*- coding: utf-8 -*-
"""Полный тест логики родства."""

import sys
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

from models import FamilyTreeModel
from kinship import calculate_kinship

def test_all_kinship():
    """Проверка всех степеней родства."""
    model = FamilyTreeModel()
    
    # Строим дерево:
    #           Прадед (4)
    #           /       \
    #      Дед (3)    БратДеда (9) -> Двоюродный дядя
    #      /     \
    #  Отец(2)  Тётя(8) -> Тётя
    #    |
    #  Я (1) -- Брат (10)
    #    |
    #  Сын (5) -- ДвоюродныйБрат (11, сын Тёти)
    #    |
    #  Внук (6)
    #    |
    #  Правнук (7)
    
    id_map = {}
    id_map['ME'] = model.add_person("Я", "Тестов", "", "", "Мужской")[0]
    id_map['FATHER'] = model.add_person("Отец", "Тестов", "", "", "Мужской")[0]
    id_map['GRANDFATHER'] = model.add_person("Дед", "Тестов", "", "", "Мужской")[0]
    id_map['GREAT_GRANDFATHER'] = model.add_person("Прадед", "Тестов", "", "", "Мужской")[0]
    id_map['SON'] = model.add_person("Сын", "Тестов", "", "", "Мужской")[0]
    id_map['GRANDSON'] = model.add_person("Внук", "Тестов", "", "", "Мужской")[0]
    id_map['GREAT_GRANDSON'] = model.add_person("Правнук", "Тестов", "", "", "Мужской")[0]
    id_map['AUNT'] = model.add_person("Тётя", "Тестова", "", "", "Женский")[0]  # Сестра отца
    id_map['UNCLE_BROTHER'] = model.add_person("БратДеда", "Тестов", "", "", "Мужской")[0]  # Брат деда
    id_map['BROTHER'] = model.add_person("Брат", "Тестов", "", "", "Мужской")[0]  # Родной брат
    id_map['COUSIN_BROTHER'] = model.add_person("ДвоюродныйБрат", "Тестов", "", "", "Мужской")[0]  # Сын тёти
    
    # Устанавливаем связи
    model.add_parent(id_map['ME'], id_map['FATHER'])
    model.add_parent(id_map['FATHER'], id_map['GRANDFATHER'])
    model.add_parent(id_map['GRANDFATHER'], id_map['GREAT_GRANDFATHER'])
    model.add_parent(id_map['SON'], id_map['ME'])
    model.add_parent(id_map['GRANDSON'], id_map['SON'])
    model.add_parent(id_map['GREAT_GRANDSON'], id_map['GRANDSON'])
    
    # Тётя (сестра отца)
    model.add_parent(id_map['AUNT'], id_map['GRANDFATHER'])
    
    # Брат деда (двоюродный дядя)
    model.add_parent(id_map['UNCLE_BROTHER'], id_map['GREAT_GRANDFATHER'])
    
    # Родной брат
    model.add_parent(id_map['BROTHER'], id_map['FATHER'])
    
    # Двоюродный брат (сын тёти)
    model.add_parent(id_map['COUSIN_BROTHER'], id_map['AUNT'])
    
    # Вычисляем родство
    relationships = calculate_kinship(model, id_map['ME'])
    
    print("=" * 70)
    print("РЕЗУЛЬТАТЫ ТЕСТА ВСЕХ СТЕПЕНЕЙ РОДСТВА:")
    print("=" * 70)
    
    expected = {
        # Прямые предки
        id_map['FATHER']: ("Отец", "Прямой предок 1 поколения"),
        id_map['GRANDFATHER']: ("Дед", "Прямой предок 2 поколения"),
        id_map['GREAT_GRANDFATHER']: ("Прадед", "Прямой предок 3 поколения"),
        
        # Прямые потомки
        id_map['SON']: ("Сын", "Прямой потомок 1 поколения"),
        id_map['GRANDSON']: ("Внук", "Прямой потомок 2 поколения"),
        id_map['GREAT_GRANDSON']: ("Правнук", "Прямой потомок 3 поколения"),
        
        # Боковое родство
        id_map['BROTHER']: ("Брат", "Родной брат (общий родитель)"),
        id_map['AUNT']: ("Тётя", "Сестра отца (общий дед)"),
        id_map['UNCLE_BROTHER']: ("Двоюродный дед", "Брат деда (общий прадед)"),
        id_map['COUSIN_BROTHER']: ("Двоюродный брат", "Сын тёти (общий дед)"),
    }
    
    all_passed = True
    for pid, (expected_rel, description) in expected.items():
        actual_rel = relationships.get(pid, "НЕ НАЙДЕНО")
        status = "OK" if actual_rel == expected_rel else "FAIL"
        if actual_rel != expected_rel:
            all_passed = False
        print(f"{status}: {description}")
        print(f"       Ожидалось: '{expected_rel}', Получено: '{actual_rel}'")
        print()
    
    print("=" * 70)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("ЕСТЬ ОШИБКИ!")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = test_all_kinship()
    sys.exit(0 if success else 1)
