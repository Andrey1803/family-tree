# -*- coding: utf-8 -*-
"""Полная перезапись bind с правильным замыканием"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next_bind = False

for i, line in enumerate(lines):
    # Пропускаем старый bind с partial
    if 'functools.partial' in line:
        continue
    if 'tag_bind(person_tag' in line:
        continue
    
    # Находим где создаётся прямоугольник и добавляем bind после него
    if 'tags=(person_tag, "person_life")' in line:
        new_lines.append(line)
        # Добавляем правильный bind с замыканием через default argument
        new_lines.append('                \n')
        new_lines.append('                # Bind с правильным замыканием\n')
        new_lines.append('                def make_callback(pid):\n')
        new_lines.append('                    def callback(event):\n')
        new_lines.append('                        self.on_person_double_click_by_id(pid)\n')
        new_lines.append('                    return callback\n')
        new_lines.append('                self.canvas.tag_bind(person_tag, "<Double-Button-1>", make_callback(person.id))\n')
        continue
    
    new_lines.append(line)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('OK - bind переписан с closure factory')
