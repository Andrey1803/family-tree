# -*- coding: utf-8 -*-
"""Исправление порядка операций в on_person_double_click_by_id"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_method = '''    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                self.window.destroy()
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                c = self.app.model.get_person(person_id)
                if c:
                    self.app.center_label.config(text=f"Центр: {c.display_name()}")
                self.app.refresh_view()
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
                # СНАЧАЛА обновляем главное окно
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                if person:
                    self.app.center_label.config(text=f"Центр: {person.display_name()}")
                self.app.refresh_view()
                print(f"  model.current_center = {self.app.model.current_center}")
                print(f"  last_selected_person_id = {self.app.last_selected_person_id}")
                print(f"OK - переход выполнен на {person.display_name()}")
                
                # ПОТОМ закрываем окно (после update!)
                self.window.after(100, self.window.destroy)
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()'''

content = content.replace(old_method, new_method)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - порядок исправлен')
