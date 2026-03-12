# -*- coding: utf-8 -*-
"""Глубокое исправление замыкания"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и исправляем bind в refresh_timeline
old_bind = '''self.canvas.tag_bind("person_life", "<Double-Button-1>", lambda e, pid=person.id: self.on_person_double_click_by_id(pid))'''

# Используем person.id напрямую через default argument
new_bind = '''# Используем person.id через default argument lambda
                person_id_for_bind = person.id  # Сохраняем ID в отдельную переменную
                self.canvas.tag_bind("person_life", "<Double-Button-1>", lambda e, pid=person_id_for_bind: self.on_person_double_click_by_id(pid))'''

content = content.replace(old_bind, new_bind)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - замыкание исправлено')
