# -*- coding: utf-8 -*-
"""Исправление - вызываем refresh_view с skip_layout=False"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_method = '''    def on_person_double_click_by_id(self, person_id):
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
                
                # Принудительно обновляем дерево
                self.app.refresh_view()
                self.app.canvas.update_idletasks()
                
                print(f"  model.current_center = {self.app.model.current_center}")
                print(f"  last_selected_person_id = {self.app.last_selected_person_id}")
                print(f"OK - переход выполнен на {person.display_name()}")
                
                # ПОТОМ закрываем окно (через 200мс чтобы update прошёл)
                self.window.after(200, self.window.destroy)
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
                
                # Принудительно обновляем дерево с перерасчётом layout
                self.app.refresh_view(skip_layout=False)
                self.app.canvas.update_idletasks()
                
                print(f"  model.current_center = {self.app.model.current_center}")
                print(f"  last_selected_person_id = {self.app.last_selected_person_id}")
                print(f"OK - переход выполнен на {person.display_name()}")
                
                # ПОТОМ закрываем окно (через 200мс чтобы update прошёл)
                self.window.after(200, self.window.destroy)
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()'''

content = content.replace(old_method, new_method)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - refresh_view(skip_layout=False)')
