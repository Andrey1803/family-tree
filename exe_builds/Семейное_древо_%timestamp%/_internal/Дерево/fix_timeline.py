# -*- coding: utf-8 -*-
"""Исправление timeline.py"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим и исправляем on_person_double_click
new_lines = []
in_method = False
skip_until_next_def = False

for i, line in enumerate(lines):
    if 'def on_person_double_click(self, person):' in line:
        # Заменяем весь метод
        new_lines.append('    def on_person_double_click(self, person):\n')
        new_lines.append('        """Обработка двойного клика."""\n')
        new_lines.append('        try:\n')
        new_lines.append('            print(f"on_person_double_click: {person.id}")\n')
        new_lines.append('            self.window.destroy()\n')
        new_lines.append('            self.app.model.current_center = person.id\n')
        new_lines.append('            self.app.last_selected_person_id = person.id\n')
        new_lines.append('            c = self.app.model.get_person(person.id)\n')
        new_lines.append('            if c:\n')
        new_lines.append('                self.app.center_label.config(text=f"Центр: {c.display_name()}")\n')
        new_lines.append('            self.app.refresh_view()\n')
        new_lines.append('            print("OK - переход выполнен")\n')
        new_lines.append('        except Exception as e:\n')
        new_lines.append('            print(f"Error: {e}")\n')
        new_lines.append('\n')
        skip_until_next_def = True
        continue
    
    if skip_until_next_def:
        if line.strip().startswith('def ') and 'on_person_double_click' not in line:
            skip_until_next_def = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('OK - on_person_double_click исправлен')
