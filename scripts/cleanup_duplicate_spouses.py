#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Удаляет дубликаты персон 45–48 (ложные «Андрейй» у Натальи) из family_tree JSON."""

import json
import sys
from pathlib import Path

DUP_IDS = {"45", "46", "47", "48"}


def cleanup_tree(data: dict) -> tuple[list[str], list[list[str]]]:
    removed_persons: list[str] = []
    for pid in list(data.get("persons", {}).keys()):
        if pid in DUP_IDS:
            removed_persons.append(pid)
            del data["persons"][pid]

    removed_marriages: list[list[str]] = []
    new_marriages = []
    for m in data.get("marriages", []):
        if isinstance(m, dict) and "persons" in m:
            ps = [str(x) for x in m["persons"]]
        elif isinstance(m, (list, tuple)):
            ps = [str(x) for x in m]
        else:
            new_marriages.append(m)
            continue
        if any(x in DUP_IDS for x in ps):
            removed_marriages.append(ps)
            continue
        new_marriages.append(m)
    data["marriages"] = new_marriages

    for person in data.get("persons", {}).values():
        for field in ("parents", "children", "spouse_ids"):
            if person.get(field):
                person[field] = [x for x in person[field] if str(x) not in DUP_IDS]

    return removed_persons, removed_marriages


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python cleanup_duplicate_spouses.py path/to/family_tree.json")
        return 1
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    removed_p, removed_m = cleanup_tree(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {path}")
    print(f"  removed persons: {removed_p}")
    print(f"  removed marriages: {removed_m}")
    print(f"  persons: {len(data['persons'])}, marriages: {len(data['marriages'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
