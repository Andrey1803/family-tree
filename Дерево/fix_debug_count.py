# -*- coding: utf-8 -*-
"""Проверка сколько персон на Timeline"""

with open('timeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем отладку в начало refresh_timeline
old_refresh = '''    def refresh_timeline(self):
        """Обновляет временную шкалу."""
        try:
            # Очищаем canvas от всех полос и шкалы
            self.canvas.delete("person_life")
            self.canvas.delete("year_scale")
            
            persons = self.get_filtered_persons()'''

new_refresh = '''    def refresh_timeline(self):
        """Обновляет временную шкалу."""
        try:
            # Очищаем canvas от всех полос и шкалы
            self.canvas.delete("person_life")
            self.canvas.delete("year_scale")
            
            persons = self.get_filtered_persons()
            print(f"Timeline: ВСЕГО персон={len(persons)}")
            for i, p in enumerate(persons[:10]):  # Первые 10
                print(f"  [{i}] ID={p.id} {p.display_name()} birth={p.birth_date}")
            if len(persons) > 10:
                print(f"  ... и ещё {len(persons)-10} персон")'''

content = content.replace(old_refresh, new_refresh)

with open('timeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - добавлена отладка количества персон')
