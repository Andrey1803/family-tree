# -*- coding: utf-8 -*-
"""Добавление центрирования после on_person_click"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_method = '''    def on_person_double_click_by_id(self, person_id):
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
                
                # === ЦЕНТРИРОВАНИЕ ===
                # Находим координаты персоны и центрируем холст
                if person_id in self.app.coords:
                    x, y = self.app.coords[person_id]
                    # Центрируем холст на персоне
                    canvas_width = self.app.canvas.winfo_width()
                    canvas_height = self.app.canvas.winfo_height()
                    
                    # Вычисляем смещение для центрирования
                    center_x = x - canvas_width // 2
                    center_y = y - canvas_height // 2
                    
                    # Применяем прокрутку
                    self.app.canvas.xview_moveto(center_x / self.app.canvas.bbox("all")[2])
                    self.app.canvas.yview_moveto(center_y / self.app.canvas.bbox("all")[3])
                    
                    print(f"  Холст центрирован на ({x}, {y})")
                # === /ЦЕНТРИРОВАНИЕ ===
                
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

print('OK - центрирование добавлено')
