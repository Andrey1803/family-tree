# -*- coding: utf-8 -*-
"""Оборачивает отладочные print в app.py в if constants.DEBUG_LAYOUT."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "Дерево" / "app.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
tags = ("[DEBUG]", "[REFRESH]", "[MARRIAGE_LINE]", "[APP.__INIT__]")
out = []
for line in lines:
    stripped = line.lstrip()
    if stripped.startswith("print(") and any(t in line for t in tags):
        indent = line[: len(line) - len(stripped)]
        if "DEBUG_LAYOUT" not in line:
            out.append(f"{indent}if constants.DEBUG_LAYOUT:\n")
            out.append(f"{indent}    {stripped}")
            continue
    out.append(line)
path.write_text("".join(out), encoding="utf-8")
print("Gated debug prints in app.py")
