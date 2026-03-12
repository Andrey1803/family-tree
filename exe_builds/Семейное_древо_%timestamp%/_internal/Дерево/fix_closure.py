# -*- coding: utf-8 -*-
"""Исправление замыкания lambda в timeline.py"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем bind - передаём person.id вместо person
old_bind = '''self.canvas.tag_bind("person_life", "<Double-Button-1>", lambda e, p=person: self.on_person_double_click(p))'''
new_bind = '''self.canvas.tag_bind("person_life", "<Double-Button-1>", lambda e, pid=person.id: self.on_person_double_click_by_id(pid))'''

content = content.replace(old_bind, new_bind)

# Добавляем новый метод
old_method = '''    def on_person_double_click(self, person):
        """Обработка двойного клика."""
        try:
            print(f"on_person_double_click: {person.id}")
            self.window.destroy()
            self.app.model.current_center = person.id
            self.app.last_selected_person_id = person.id
            c = self.app.model.get_person(person.id)
            if c:
                self.app.center_label.config(text=f"Центр: {c.display_name()}")
            self.app.refresh_view()
            print("OK - переход выполнен")
        except Exception as e:
            print(f"Error: {e}")'''

new_method = '''    def on_person_double_click_by_id(self, person_id):
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
            traceback.print_exc()

    def on_person_double_click(self, person):
        """Обработка двойного клика (старый метод)."""
        self.on_person_double_click_by_id(person.id)'''

content = content.replace(old_method, new_method)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - замыкание исправлено')
