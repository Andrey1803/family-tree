# -*- coding: utf-8 -*-
"""Базовые тесты модели данных."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Дерево"))

from models import FamilyTreeModel, Person  # noqa: E402


def test_get_person_string_and_int_key():
    m = FamilyTreeModel()
    m.persons["42"] = Person(name="Иван", surname="Иванов", gender="Мужской")
    m.persons["42"].id = "42"
    assert m.get_person(42) is not None
    assert m.get_person("42").name == "Иван"


def test_add_marriage_duplicate():
    m = FamilyTreeModel()
    m.persons["1"] = Person(name="A", surname="X", gender="Мужской")
    m.persons["2"] = Person(name="B", surname="Y", gender="Женский")
    m.persons["1"].id, m.persons["2"].id = "1", "2"
    ok1, _ = m.add_marriage("1", "2")
    ok2, _ = m.add_marriage("1", "2")
    assert ok1 is True
    assert ok2 is False
