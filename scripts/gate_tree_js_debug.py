# -*- coding: utf-8 -*-
"""Удаляет console.log('[DEBUG]...') из tree.js."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "web" / "static" / "js" / "tree.js"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
out = [ln for ln in lines if "console.log('[DEBUG]" not in ln and 'console.log("[DEBUG]' not in ln]
removed = len(lines) - len(out)
path.write_text("".join(out), encoding="utf-8")
print(f"Removed {removed} DEBUG console.log lines from tree.js")
