# -*- coding: utf-8 -*-
"""Перезапись refresh_timeline"""

# Новый метод refresh_timeline
new_refresh_timeline = '''    def refresh_timeline(self):
        """Обновляет временную шкалу."""
        try:
            # Очищаем canvas
            self.canvas.delete("person_life")
            self.canvas.delete("year_scale")
            self.canvas.delete("significant_event")
            
            persons = self.get_filtered_persons()
            print(f"Timeline: ВСЕГО персон={len(persons)}")
            
            if not persons:
                self.canvas.create_text(500, 200, text="Нет персон", font=("Segoe UI", 14), fill="#64748b", tags="message")
                return
            
            # Фильтруем персоны с датами
            persons_with_dates = [p for p in persons if self.parse_date(p.birth_date)]
            
            if not persons_with_dates:
                self.canvas.create_text(500, 200, text=f"Нет дат рождения\\nПерсон: {len(persons)}", font=("Segoe UI", 14), fill="#64748b", justify="center", tags="message")
                return
            
            persons = persons_with_dates
            
            # Диапазон лет
            years = []
            for p in persons:
                birth_year = self.parse_date(p.birth_date)
                death_year = self.parse_date(p.death_date) if p.is_deceased else None
                if birth_year: years.append(birth_year)
                if death_year: years.append(death_year)
            
            if not years: return
            min_year = min(years) - 5
            max_year = max(years) + 5
            
            # Настройки
            scale = self.scale_var.get()
            base_pixels_per_year = 20 / scale
            pixels_per_year = base_pixels_per_year * self.current_scale
            
            # Сортировка
            persons.sort(key=lambda p: self.parse_date(p.birth_date) or 9999)
            
            # Отрисовка
            row_height = 40
            y_offset = 60
            
            self.draw_year_scale(min_year, max_year, pixels_per_year, y_offset - 50)
            
            for i, person in enumerate(persons):
                birth_year = self.parse_date(person.birth_date)
                death_year = self.parse_date(person.death_date) if person.is_deceased else 2026
                
                if not birth_year: continue
                
                x_start = int((birth_year - min_year) * pixels_per_year)
                width = max(50, int((death_year - birth_year) * pixels_per_year))
                y = y_offset + i * row_height
                color = "#60a5fa" if person.gender == "Мужской" else "#f472b6"
                
                # УНИКАЛЬНЫЙ тег для каждой полосы
                person_tag = f"person_{person.id}"
                
                # Полоса
                self.canvas.create_rectangle(
                    x_start, y, x_start + width, y + row_height - 4,
                    fill=color, outline="#1e293b", width=1,
                    tags=(person_tag, "person_life")
                )
                
                # Имя
                text = f"{person.surname} {person.name}"
                max_text_width = width - 60
                while len(text) > 3 and len(text) * 7 > max_text_width:
                    text = text[:-1]
                if len(text) < len(f"{person.surname} {person.name}"):
                    text = text[:-3] + "..."
                
                if width > 30:
                    self.canvas.create_text(x_start + 5, y + (row_height - 4) // 2, text=text, font=("Segoe UI", 8, "bold"), fill="#ffffff", anchor="w", tags=person_tag)
                
                # Даты
                if width > 80:
                    self.canvas.create_text(x_start + width - 5, y + (row_height - 4) // 2, text=f"{birth_year}-{death_year}", font=("Segoe UI", 7), fill="#ffffff", anchor="e", tags=person_tag)
                
                # === ВАЖНО: Bind с ПРАВИЛЬНЫМ замыканием ===
                # Сохраняем person.id в отдельную переменную ДО lambda
                pid = person.id
                self.canvas.tag_bind(person_tag, "<Double-Button-1>", lambda e, stored_pid=pid: self.on_person_double_click_by_id(stored_pid))
            
            # События
            self.draw_significant_events(persons, min_year, pixels_per_year, y_offset, row_height)
            
            # Прокрутка
            total_height = y_offset + len(persons) * row_height
            total_width = int((max_year - min_year) * pixels_per_year) + 100
            self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
            
        except Exception as e:
            print(f"Timeline: ошибка при отрисовке: {e}")
            import traceback
            traceback.print_exc()
'''

with open('timeline.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Находим старый refresh_timeline и заменяем
import re
pattern = r'    def refresh_timeline\(self\):.*?(?=\n    def [a-z])'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content[:match.start()] + new_refresh_timeline + "\n" + content[match.end():]
    with open('timeline.py', 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    print('OK - refresh_timeline переписан')
else:
    print('ERROR - не найдено refresh_timeline')
