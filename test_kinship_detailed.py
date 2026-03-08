# -*- coding: utf-8 -*-
"""Детальный тест степени родства."""

import sys
sys.path.insert(0, r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\Дерево')

from models import FamilyTreeModel
from kinship import calculate_kinship, _get_kinship

def test_kinship_detailed():
    """Проверка всех степеней родства с подробным выводом."""
    model = FamilyTreeModel()

    # Строим дерево:
    #                   Прадед (4)
    #                   /       \
    #              Дед (3)    БратДеда (9)
    #              /     \
    #          Отец(2)  Тётя(8)
    #            |
    #          Я (1) -- Брат (10)
    #            |
    #          Сын (5)
    #            |
    #          Внук (6)
    #            |
    #          Правнук (7)
    
    # Тётя(8) + МужТёти(11)
    #            |
    #      ДвоюродныйБрат (12)

    id_map = {}
    id_map['ME'] = model.add_person("Я", "Тестов", "", "", "Мужской")[0]
    id_map['FATHER'] = model.add_person("Отец", "Тестов", "", "", "Мужской")[0]
    id_map['MOTHER'] = model.add_person("Мать", "Тестова", "", "", "Женский")[0]
    id_map['GRANDFATHER'] = model.add_person("Дед", "Тестов", "", "", "Мужской")[0]
    id_map['GRANDMOTHER'] = model.add_person("Бабушка", "Тестова", "", "", "Женский")[0]
    id_map['GREAT_GRANDFATHER'] = model.add_person("Прадед", "Тестов", "", "", "Мужской")[0]
    id_map['SON'] = model.add_person("Сын", "Тестов", "", "", "Мужской")[0]
    id_map['DAUGHTER'] = model.add_person("Дочь", "Тестова", "", "", "Женский")[0]
    id_map['GRANDSON'] = model.add_person("Внук", "Тестов", "", "", "Мужской")[0]
    id_map['GRANDDAUGHTER'] = model.add_person("Внучка", "Тестова", "", "", "Женский")[0]
    id_map['GREAT_GRANDSON'] = model.add_person("Правнук", "Тестов", "", "", "Мужской")[0]
    id_map['AUNT'] = model.add_person("Тётя", "Тестова", "", "", "Женский")[0]
    id_map['UNCLE'] = model.add_person("Дядя", "Тестов", "", "", "Мужской")[0]
    id_map['BROTHER'] = model.add_person("Брат", "Тестов", "", "", "Мужской")[0]
    id_map['SISTER'] = model.add_person("Сестра", "Тестова", "", "", "Женский")[0]
    id_map['COUSIN_BROTHER'] = model.add_person("ДвоюродныйБрат", "Тестов", "", "", "Мужской")[0]
    id_map['COUSIN_SISTER'] = model.add_person("ДвоюроднаяСестра", "Тестова", "", "", "Женский")[0]
    id_map['GREAT_UNCLE'] = model.add_person("БратДеда", "Тестов", "", "", "Мужской")[0]
    id_map['WIFE'] = model.add_person("Жена", "Тестова", "", "", "Женский")[0]
    id_map['HUSBAND_AUNT'] = model.add_person("МужТёти", "Петров", "", "", "Мужской")[0]

    # Устанавливаем связи
    # Прямая линия
    model.add_parent(id_map['ME'], id_map['FATHER'])
    model.add_parent(id_map['ME'], id_map['MOTHER'])
    model.add_parent(id_map['FATHER'], id_map['GRANDFATHER'])
    model.add_parent(id_map['FATHER'], id_map['GRANDMOTHER'])
    model.add_parent(id_map['GRANDFATHER'], id_map['GREAT_GRANDFATHER'])
    
    # Потомки
    model.add_parent(id_map['SON'], id_map['ME'])
    model.add_parent(id_map['DAUGHTER'], id_map['ME'])
    model.add_parent(id_map['GRANDSON'], id_map['SON'])
    model.add_parent(id_map['GRANDDAUGHTER'], id_map['DAUGHTER'])
    model.add_parent(id_map['GREAT_GRANDSON'], id_map['GRANDSON'])
    
    # Братья/сёстры и тёти/дяди
    model.add_parent(id_map['BROTHER'], id_map['FATHER'])
    model.add_parent(id_map['SISTER'], id_map['FATHER'])
    model.add_parent(id_map['AUNT'], id_map['GRANDFATHER'])
    model.add_parent(id_map['UNCLE'], id_map['GRANDFATHER'])
    model.add_parent(id_map['GREAT_UNCLE'], id_map['GREAT_GRANDFATHER'])
    
    # Двоюродные
    model.add_parent(id_map['COUSIN_BROTHER'], id_map['AUNT'])
    model.add_parent(id_map['COUSIN_SISTER'], id_map['UNCLE'])
    
    # Супруги
    model.add_marriage(id_map['ME'], id_map['WIFE'])
    model.add_marriage(id_map['AUNT'], id_map['HUSBAND_AUNT'])

    # Вычисляем родство относительно ME
    relationships = calculate_kinship(model, id_map['ME'])
    
    print("=" * 80)
    print("СТЕПЕНЬ РОДСТВА относительно 'Я' (ME)")
    print("=" * 80)
    
    expected = {
        # Прямые предки
        id_map['FATHER']: "Отец",
        id_map['MOTHER']: "Мать",
        id_map['GRANDFATHER']: "Дед",
        id_map['GRANDMOTHER']: "Бабушка",
        id_map['GREAT_GRANDFATHER']: "Прадед",
        
        # Прямые потомки
        id_map['SON']: "Сын",
        id_map['DAUGHTER']: "Дочь",
        id_map['GRANDSON']: "Внук",
        id_map['GRANDDAUGHTER']: "Внучка",
        id_map['GREAT_GRANDSON']: "Правнук",
        
        # Братья/сёстры
        id_map['BROTHER']: "Брат",
        id_map['SISTER']: "Сестра",
        
        # Тёти/дяди
        id_map['AUNT']: "Тётя",
        id_map['UNCLE']: "Дядя",
        
        # Двоюродные
        id_map['COUSIN_BROTHER']: "Двоюродный брат",
        id_map['COUSIN_SISTER']: "Двоюродная сестра",
        
        # Двоюродный дед
        id_map['GREAT_UNCLE']: "Двоюродный дед",
        
        # Супруги
        id_map['WIFE']: "Супруга",
        id_map['HUSBAND_AUNT']: "Дядя",  # Муж тёти
    }
    
    all_passed = True
    for pid, expected_rel in expected.items():
        person = model.get_person(pid)
        actual_rel = relationships.get(pid, "НЕ НАЙДЕНО")
        status = "OK" if actual_rel == expected_rel else "FAIL"
        if actual_rel != expected_rel:
            all_passed = False
        print(f"{status} | {person.name:20s} | Ожидалось: {expected_rel:20s} | Получено: {actual_rel}")
    
    print("=" * 80)
    if all_passed:
        print("OK: ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("FAIL: ЕСТЬ ОШИБКИ!")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = test_kinship_detailed()
    sys.exit(0 if success else 1)
