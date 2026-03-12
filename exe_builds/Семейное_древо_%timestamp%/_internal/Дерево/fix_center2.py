# -*- coding: utf-8 -*-
"""Исправление центрирования - используем force_refresh"""

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

new_method = '''    def on_person_double_click_by_id(self, person_id):
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
                
                # Перерисовываем дерево С ЦЕНТРИРОВАНИЕМ
                # refresh_view() сам отцентрирует на current_center
                self.app.refresh_view(skip_layout=False)
                
                # Даём время на отрисовку
                self.app.canvas.update_idletasks()
                
                # Теперь центрируем холст на персоне
                self.app.center_tree_on_person(person_id)
                
                print(f"  current_center={self.app.model.current_center}")
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

print('OK - центрирование через center_tree_on_person')
