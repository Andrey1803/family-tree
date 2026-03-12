# -*- coding: utf-8 -*-
"""Проверка что происходит в on_person_click"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_method = '''    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                # Закрываем окно СРАЗУ
                self.window.destroy()
                
                # Вызываем on_person_click - он точно работает!
                self.app.on_person_click(person_id)
                
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()'''

new_method = '''    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                print(f"  Персона найдена: {person.display_name()}")
                print(f"  ДО: current_center={self.app.model.current_center}")
                
                # Закрываем окно
                self.window.destroy()
                
                # Вызываем on_person_click
                print(f"  Вызов on_person_click({person_id})...")
                self.app.on_person_click(person_id)
                
                print(f"  ПОСЛЕ: current_center={self.app.model.current_center}")
                print(f"  ПОСЛЕ: last_selected={self.app.last_selected_person_id}")
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()'''

content = content.replace(old_method, new_method)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - добавлена детальная отладка')
