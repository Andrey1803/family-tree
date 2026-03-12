# -*- coding: utf-8 -*-
"""Исправление bind - используем lambda с default argument"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Удаляем всё, что связано с functools
if 'import functools' in content:
    content = content.replace('import functools\n', '')

# Находим и заменяем bind
old = '''                # Bind с правильным замыканием
                def make_callback(pid):
                    def callback(event):
                        self.on_person_double_click_by_id(pid)
                    return callback
                self.canvas.tag_bind(person_tag, "<Double-Button-1>", make_callback(person.id))'''

new = '''                # Bind с замыканием через default argument
                self.canvas.tag_bind(person_tag, "<Double-Button-1>",
                                    lambda e, pid=person.id: self.on_person_double_click_by_id(pid))'''

content = content.replace(old, new)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - lambda с default argument')
