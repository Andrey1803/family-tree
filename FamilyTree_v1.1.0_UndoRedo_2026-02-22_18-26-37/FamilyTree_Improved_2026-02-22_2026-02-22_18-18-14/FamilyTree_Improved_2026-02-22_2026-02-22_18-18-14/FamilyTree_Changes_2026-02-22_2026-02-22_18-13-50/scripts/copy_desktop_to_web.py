# -*- coding: utf-8 -*-
"""Копирует исходники desktop в web/desktop_src для скачивания с веб-версии."""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "web", "desktop_src")
TREE_SRC = os.path.join(ROOT, "Дерево")

os.makedirs(os.path.join(DST, "Дерево"), exist_ok=True)
shutil.copy2(os.path.join(ROOT, "main.py"), DST)
for name in os.listdir(TREE_SRC):
    if name == "__pycache__":
        continue
    src_p = os.path.join(TREE_SRC, name)
    dst_p = os.path.join(DST, "Дерево", name)
    if os.path.isfile(src_p):
        if not name.endswith(".pyc"):
            shutil.copy2(src_p, dst_p)
    elif os.path.isdir(src_p):
        if name != "__pycache__":
            if os.path.exists(dst_p):
                shutil.rmtree(dst_p)
            shutil.copytree(src_p, dst_p, ignore=lambda d, files: [f for f in files if f.endswith(".pyc")])
print("Desktop sources copied to web/desktop_src")
