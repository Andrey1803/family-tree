# -*- coding: utf-8 -*-
"""Добавление working on_person_double_click_by_id"""

with open('timeline.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Находим где заканчивается класс TimelineWindow
insert_idx = len(lines)
for i in range(len(lines)-1, 0, -1):
    if 'def open_timeline(' in lines[i]:
        insert_idx = i
        break

# Вставляем метод перед open_timeline
new_method = '''
    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                print(f"  Персона найдена: {person.display_name()}")
                
                # Устанавливаем центр
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                self.app.center_label.config(text=f"Центр: {person.display_name()}")
                
                # Перерисовываем и центрируем
                self.app.refresh_view(skip_layout=False)
                self.app.center_tree_on_person(person_id)
                
                # Закрываем окно через 100мс
                self.window.after(100, self.window.destroy)
                
                print(f"  current_center={self.app.model.current_center}")
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")

'''

lines.insert(insert_idx, new_method)

with open('timeline.py', 'w', encoding='utf-8', errors='replace') as f:
    f.writelines(lines)

print('OK - метод добавлен')
