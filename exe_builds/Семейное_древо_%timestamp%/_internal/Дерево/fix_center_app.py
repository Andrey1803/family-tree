# -*- coding: utf-8 -*-
"""Добавление center_tree_on_person"""

with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Находим существующий метод
old_method = '''    def center_tree_on_person(self, pid):
        \"\"\"Центрирует дерево на персоне (используется из Timeline).\"\"\"
        self.on_person_click(pid)'''

new_method = '''    def center_tree_on_person(self, pid):
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

content = content.replace(old_method, new_method)

with open('app.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - center_tree_on_person добавлен')
