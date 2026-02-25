# -*- coding: utf-8 -*-
"""Тест логики формирования units и layout (без GUI)."""
import sys
import os

# Добавляем путь к модулям
_project_root = os.path.dirname(os.path.abspath(__file__))
_tree_dir = os.path.join(_project_root, "Дерево")
if _tree_dir not in sys.path:
    sys.path.insert(0, _tree_dir)

os.chdir(_project_root)


def test_units_with_mixed_id_types():
    """Проверка: units формируются корректно при разных типах id (int/str)."""
    from models import FamilyTreeModel, Person, GENDER_MALE, GENDER_FEMALE

    model = FamilyTreeModel()
    # Добавляем персон — модель может использовать int id
    p1_id = model.add_person("Иван", "Иванов", gender=GENDER_MALE)[0]
    p2_id = model.add_person("Мария", "Иванова", gender=GENDER_FEMALE)[0]
    model.add_marriage(p1_id, p2_id)

    # Симулируем что marriages возвращает id в другом формате (например из JSON)
    marriages = list(model.get_marriages())
    assert len(marriages) == 1, "Должен быть один брак"
    h_id, w_id = marriages[0]

    # Ключи в persons могут отличаться (int vs str) — _key_in_filtered должен найти
    filtered_persons = model.persons
    _norm_id = lambda p: str(p) if p is not None else None
    _key_in_filtered = lambda pid: next(
        (k for k in filtered_persons if _norm_id(k) == _norm_id(pid)), None
    ) if pid is not None else None

    h_key = _key_in_filtered(h_id)
    w_key = _key_in_filtered(w_id)
    assert h_key is not None, f"h_key должен быть найден для {h_id}"
    assert w_key is not None, f"w_key должен быть найден для {w_id}"

    # unit_key должен быть устойчив к порядку
    p1, p2 = h_key, w_key
    n1, n2 = _norm_id(p1), _norm_id(p2)
    unit_key = f"{min(n1, n2)}_{max(n1, n2)}"
    assert "_" in unit_key, "unit_key должен содержать оба id"

    print("[OK] test_units_with_mixed_id_types")


def _mk_empty_tree_file():
    """Создаёт временный файл с валидным пустым деревом."""
    import tempfile
    import json
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        json.dump({"persons": {}, "marriages": [], "current_center": None}, f, ensure_ascii=False)
        return f.name


def test_layout_with_empty_tree():
    """Проверка: layout не падает на пустом дереве."""
    import tkinter as tk
    from app import FamilyTreeApp

    tmp_file = _mk_empty_tree_file()
    try:
        root = tk.Tk()
        root.withdraw()
        app = FamilyTreeApp(root, data_file=tmp_file, username="Test")
        app.model.persons.clear()
        app.model.marriages.clear()
        app.model.current_center = None

        app.calculate_layout(skip_centering=True)
        assert app.coords == {}, "Координаты должны быть пустыми"
        assert app.units == {}, "Units должны быть пустыми"
        root.destroy()
    finally:
        try:
            os.unlink(tmp_file)
        except OSError:
            pass
    print("[OK] test_layout_with_empty_tree")


def test_layout_with_one_person():
    """Проверка: layout с одной персоной."""
    import tkinter as tk
    from app import FamilyTreeApp
    from models import GENDER_MALE

    tmp_file = _mk_empty_tree_file()
    try:
        root = tk.Tk()
        root.withdraw()
        app = FamilyTreeApp(root, data_file=tmp_file, username="Test")
        app.model.persons.clear()
        app.model.marriages.clear()
        pid = app.model.add_person("Один", "Тест", gender=GENDER_MALE)[0]
        app.model.current_center = pid

        app.calculate_layout(skip_centering=True)
        assert len(app.coords) >= 1, "Должна быть хотя бы одна персона"
        assert len(app.units) == 0, "Units пусты (нет браков)"
        root.destroy()
    finally:
        try:
            os.unlink(tmp_file)
        except OSError:
            pass
    print("[OK] test_layout_with_one_person")


def test_layout_with_married_couple():
    """Проверка: layout с парой, units содержат ключи из coords."""
    import tkinter as tk
    from app import FamilyTreeApp
    from models import GENDER_MALE, GENDER_FEMALE

    tmp_file = _mk_empty_tree_file()
    try:
        root = tk.Tk()
        root.withdraw()
        app = FamilyTreeApp(root, data_file=tmp_file, username="Test")
        app.model.persons.clear()
        app.model.marriages.clear()
        p1 = app.model.add_person("М", "М", gender=GENDER_MALE)[0]
        p2 = app.model.add_person("Ж", "Ж", gender=GENDER_FEMALE)[0]
        app.model.add_marriage(p1, p2)
        app.model.current_center = p1

        app.calculate_layout(skip_centering=True)
        assert len(app.coords) >= 2, "Должны быть обе персоны"
        assert len(app.units) == 1, "Должен быть один unit"

        unit_members = list(app.units.values())[0]
        for mid in unit_members:
            assert mid in app.coords, f"Член unit {mid} должен быть в coords"

        root.destroy()
    finally:
        try:
            os.unlink(tmp_file)
        except OSError:
            pass
    print("[OK] test_layout_with_married_couple")


def run_all():
    test_units_with_mixed_id_types()
    test_layout_with_empty_tree()
    test_layout_with_one_person()
    test_layout_with_married_couple()
    print("\nВсе тесты пройдены.")


if __name__ == "__main__":
    run_all()
