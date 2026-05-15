# -*- coding: utf-8 -*-
"""Исправляет битую строку «Неизвестная» в tree.js."""
import re
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "web" / "static" / "js" / "tree.js"
text = path.read_text(encoding="utf-8")
pat = (
    r'(function generateNameFromPatronymic\(patronymic, gender\) \{\s*'
    r'if \(!patronymic \|\| !patronymic\.trim\(\)\) return gender === "Мужской" \? "Неизвестный" : )"[^"]*";'
)
text2, n = re.subn(pat, r'\1"Неизвестная";', text, count=1)
if n != 1:
    raise SystemExit(f"Pattern not found or multiple matches: {n}")
path.write_text(text2, encoding="utf-8")
print("OK: fixed generateNameFromPatronymic")
