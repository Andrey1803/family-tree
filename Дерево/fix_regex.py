# -*- coding: utf-8 -*-
"""
Минимальное исправление для double-click в Timeline.
Добавляет работающий bind в конец refresh_timeline.
"""

import re

with open('timeline.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 1. Находим где создаётся прямоугольник полосы
rect_pattern = r'(self\.canvas\.create_rectangle\([^)]+tags="person_life"[^)]+\))'

# 2. Добавляем уникальный тег и bind
def fix_rect(match):
    rect_code = match.group(1)
    # Заменяем tags="person_life" на tags=(f"person_{person.id}", "person_life")
    fixed = rect_code.replace(
        'tags="person_life"',
        'tags=(f"person_{person.id}", "person_life")'
    )
    return fixed

content = re.sub(rect_pattern, fix_rect, content)

# 3. Находим где был старый bind и заменяем на новый
old_bind_pattern = r'self\.canvas\.tag_bind\("person_life", "<Double-Button-1>", [^)]+\)'
new_bind = 'self.canvas.tag_bind(f"person_{person.id}", "<Double-Button-1>", lambda e, pid=person.id: self.on_person_double_click_by_id(pid))'

content = re.sub(old_bind_pattern, new_bind, content)

with open('timeline.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - regex исправление применено')
