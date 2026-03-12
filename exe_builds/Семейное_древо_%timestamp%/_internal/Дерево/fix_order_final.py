# -*- coding: utf-8 -*-
"""Исправление порядка - центрируем ДО закрытия окна"""

with open('timeline.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

old_method = '''    def on_person_double_click_by_id(self, person_id):
        """Обработка двойного клика по ID."""
        try:
            print(f"on_person_double_click_by_id: {person_id}")
            person = self.app.model.get_person(person_id)
            if person:
                print(f"  Персона найдена: {person.display_name()}")
                
                # Закрываем окно СРАЗУ
                self.window.destroy()
                
                # СНАЧАЛА устанавливаем центр
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                
                # Обновляем метку
                self.app.center_label.config(text=f"Центр: {person.display_name()}")
                
                # Перерисовываем дерево
                self.app.refresh_view(skip_layout=False)
                
                # Центрируем холст на персоне
                self.app.center_tree_on_person(person_id)
                
                print(f"  current_center={self.app.model.current_center}")
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
                
                # СНАЧАЛА устанавливаем центр и центрируем (ПОКА ОКНО ОТКРЫТО)
                self.app.model.current_center = person_id
                self.app.last_selected_person_id = person_id
                self.app.center_label.config(text=f"Центр: {person.display_name()}")
                
                # Перерисовываем и центрируем
                self.app.refresh_view(skip_layout=False)
                self.app.center_tree_on_person(person_id)
                
                # Закрываем окно ПОСЛЕ центрирования
                self.window.after(100, self.window.destroy)
                
                print(f"  current_center={self.app.model.current_center}")
                print(f"OK - переход выполнен на {person.display_name()}")
            else:
                print(f"Персона {person_id} не найдена")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()'''

content = content.replace(old_method, new_method)

with open('timeline.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - порядок исправлен: центрируем ДО закрытия')
