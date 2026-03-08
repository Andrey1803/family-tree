# -*- coding: utf-8 -*-
"""Создаёт ZIP с исходниками для релиза (без данных и служебных папок)."""
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    from version import __version__
    VERSION = __version__
except ImportError:
    VERSION = "1.0.0"
ZIP_NAME = f"Семейное_древо_{VERSION}_source.zip"

EXCLUDE_DIRS = {"__pycache__", ".git", ".idea", "dist", "build", "venv", ".venv"}
EXCLUDE_FILES = {
    "users.json", "login_remember.json", "palette.json", "window_settings.json"
}
EXCLUDE_PATTERNS = ("family_tree", "user_settings")  # startswith


def should_exclude(path: Path, rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
    name = path.name
    if name in EXCLUDE_FILES:
        return True
    if any(name.startswith(p) for p in EXCLUDE_PATTERNS):
        return True
    return False


def main():
    to_add = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        base = Path(base)
        for f in files:
            if f.endswith(".pyc") or f == ZIP_NAME:
                continue
            full = base / f
            rel = full.relative_to(ROOT).as_posix()
            if should_exclude(full, rel):
                continue
            to_add.append((full, rel))
    out = ROOT / ZIP_NAME
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for full, rel in sorted(to_add, key=lambda x: x[1]):
            zf.write(full, rel)
    print(f"Готово: {out}")


if __name__ == "__main__":
    main()
