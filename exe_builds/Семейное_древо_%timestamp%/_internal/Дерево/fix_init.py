# -*- coding: utf-8 -*-
"""Исправление __init__ в timeline.py"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем __init__
old_init = '''    def __init__(self, parent, model):
        self.parent = parent
        self.model = model'''

new_init = '''    def __init__(self, app, model):
        self.app = app  # FamilyTreeApp
        self.model = model'''

content = content.replace(old_init, new_init)

# Также исправляем создание окна
old_window = '''        self.window = tk.Toplevel(parent)'''
new_window = '''        self.window = tk.Toplevel(app.root)'''

content = content.replace(old_window, new_window)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - __init__ исправлен')
