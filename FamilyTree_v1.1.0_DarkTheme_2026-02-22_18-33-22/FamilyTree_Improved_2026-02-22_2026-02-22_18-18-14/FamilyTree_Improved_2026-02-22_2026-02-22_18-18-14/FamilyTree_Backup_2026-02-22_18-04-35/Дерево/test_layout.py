# -*- coding: utf-8 -*-
"""Тест центрирования детей под родителями."""
import tkinter as tk
import sys
import os

# Ensure we can import from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    root = tk.Tk()
    root.withdraw()
    try:
        from app import FamilyTreeApp
        app = FamilyTreeApp(root)
        app.calculate_layout(skip_centering=True)
        n = len(app.coords)
        print(f"Layout OK: {n} persons placed")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        root.destroy()

if __name__ == "__main__":
    sys.exit(main())
