# -*- coding: utf-8 -*-
"""
Скопировать main.py и Дерево/ в web/desktop_bundle/ для скачивания с веб-версии.
Запуск: из корня проекта: python web/sync_desktop_bundle.py
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(WEB, "desktop_bundle")
TREE_SRC = os.path.join(ROOT, "Дерево")
MAIN_PY = os.path.join(ROOT, "main.py")


def main():
    os.makedirs(BUNDLE, exist_ok=True)
    tree_dst = os.path.join(BUNDLE, "Дерево")
    if os.path.isdir(tree_dst):
        shutil.rmtree(tree_dst)
    shutil.copytree(TREE_SRC, tree_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(MAIN_PY, os.path.join(BUNDLE, "main.py"))
    print("desktop_bundle готов:", BUNDLE)


if __name__ == "__main__":
    main()
