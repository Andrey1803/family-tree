# -*- coding: utf-8 -*-
"""Детальная отладка центрирования"""

with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

old_method = '''    def center_tree_on_person(self, pid):
        \"\"\"Центрирует дерево на персоне (используется из Timeline).\"\"\"
        # Устанавливаем центр
        self.model.current_center = pid
        self.last_selected_person_id = pid
        
        # Обновляем метку
        person = self.model.get_person(pid)
        if person:
            self.center_label.config(text=f"Центр: {person.display_name()}")
        
        # Перерисовываем дерево
        self.refresh_view(skip_layout=False)
        
        # Центрируем холст после отрисовки
        self.canvas.update_idletasks()
        
        # Находим координаты персоны и центрируем
        if str(pid) in self.coords:
            x, y = self.coords[str(pid)]
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Вычисляем позицию для центрирования
            scroll_x = (x - canvas_width // 2) / max(1, self.canvas.bbox("all")[2])
            scroll_y = (y - canvas_height // 2) / max(1, self.canvas.bbox("all")[3])
            
            # Ограничиваем диапазон [0, 1]
            scroll_x = max(0, min(1, scroll_x))
            scroll_y = max(0, min(1, scroll_y))
            
            self.canvas.xview_moveto(scroll_x)
            self.canvas.yview_moveto(scroll_y)
            print(f"  Холст центрирован на персоне {pid} ({x}, {y})")
        else:
            print(f"  Координаты персоны {pid} не найдены")'''

new_method = '''    def center_tree_on_person(self, pid):
        \"\"\"Центрирует дерево на персоне (используется из Timeline).\"\"\"
        print(f"  [center_tree_on_person] pid={pid}")
        
        # Устанавливаем центр
        self.model.current_center = pid
        self.last_selected_person_id = pid
        print(f"  current_center установлен: {self.model.current_center}")
        
        # Обновляем метку
        person = self.model.get_person(pid)
        if person:
            self.center_label.config(text=f"Центр: {person.display_name()}")
            print(f"  Метка обновлена: {person.display_name()}")
        
        # Перерисовываем дерево
        print(f"  Вызов refresh_view...")
        self.refresh_view(skip_layout=False)
        
        # Центрируем холст после отрисовки
        self.canvas.update_idletasks()
        print(f"  update_idletasks выполнен")
        
        # Проверяем coords
        print(f"  self.coords keys: {list(self.coords.keys())[:10]}...")
        print(f"  Ищем pid={pid} в coords...")
        
        # Находим координаты персоны и центрируем
        pid_str = str(pid)
        if pid_str in self.coords:
            x, y = self.coords[pid_str]
            print(f"  Координаты найдены: ({x}, {y})")
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            print(f"  Размер холста: {canvas_width}x{canvas_height}")
            
            bbox = self.canvas.bbox("all")
            if bbox:
                print(f"  Bbox: {bbox}")
                # Вычисляем позицию для центрирования
                scroll_x = (x - canvas_width // 2) / max(1, bbox[2])
                scroll_y = (y - canvas_height // 2) / max(1, bbox[3])
                
                print(f"  scroll_x={scroll_x}, scroll_y={scroll_y}")
                
                # Ограничиваем диапазон [0, 1]
                scroll_x = max(0, min(1, scroll_x))
                scroll_y = max(0, min(1, scroll_y))
                
                print(f"  После ограничения: scroll_x={scroll_x}, scroll_y={scroll_y}")
                
                self.canvas.xview_moveto(scroll_x)
                self.canvas.yview_moveto(scroll_y)
                print(f"  Холст центрирован на персоне {pid} ({x}, {y})")
            else:
                print(f"  Bbox не найден!")
        else:
            print(f"  Координаты персоны {pid} НЕ НАЙДЕНЫ в self.coords!")
            print(f"  Доступные ключи: {list(self.coords.keys())[:20]}")'''

content = content.replace(old_method, new_method)

with open('app.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - детальная отладка добавлена')
