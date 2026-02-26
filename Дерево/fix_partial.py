# -*- coding: utf-8 -*-
"""Полное исправление bind с functools.partial"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт functools в начало файла
if 'import functools' not in content:
    content = 'import functools\n' + content

# Находим и полностью переписываем bind
old_bind = '''# Используем person.id напрямую через default argument lambda
                person_id_for_bind = person.id  # Сохраняем ID в отдельную переменную
                self.canvas.tag_bind("person_life", "<Double-Button-1>", lambda e, pid=person_id_for_bind: self.on_person_double_click_by_id(pid))'''

new_bind = '''# Используем functools.partial для правильного замыкания
                self.canvas.tag_bind("person_life", "<Double-Button-1>", 
                                    functools.partial(self.on_person_double_click_by_id, person.id))'''

content = content.replace(old_bind, new_bind)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - functools.partial использован')
