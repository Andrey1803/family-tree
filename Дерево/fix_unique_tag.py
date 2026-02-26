# -*- coding: utf-8 -*-
"""Исправление - отдельный тег для каждой полосы"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Исправляем создание прямоугольника - добавляем уникальный тег
old_rect = '''                # Полоса
                self.canvas.create_rectangle(
                    x_start, y, x_start + width, y + row_height - 4,
                    fill=color, outline="#1e293b", width=1,
                    tags="person_life"
                )'''

new_rect = '''                # Полоса с уникальным тегом
                person_tag = f"person_life_{person.id}"
                self.canvas.create_rectangle(
                    x_start, y, x_start + width, y + row_height - 4,
                    fill=color, outline="#1e293b", width=1,
                    tags=(person_tag, "person_life")  # Уникальный + общий тег
                )'''

content = content.replace(old_rect, new_rect)

# 2. Исправляем bind - используем уникальный тег
old_bind = '''                # Используем functools.partial для правильного замыкания
                self.canvas.tag_bind("person_life", "<Double-Button-1>", 
                                    functools.partial(self.on_person_double_click_by_id, person.id))'''

new_bind = '''                # Bind на уникальный тег полосы
                self.canvas.tag_bind(person_tag, "<Double-Button-1>", 
                                    functools.partial(self.on_person_double_click_by_id, person.id))'''

content = content.replace(old_bind, new_bind)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - уникальный тег для каждой полосы')
