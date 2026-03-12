# -*- coding: utf-8 -*-
"""Исправление вызова open_timeline в app.py"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем вызов
old_call = '''open_timeline(self.root, self.model)'''
new_call = '''open_timeline(self, self.model)'''

content = content.replace(old_call, new_call)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - вызов исправлен')
