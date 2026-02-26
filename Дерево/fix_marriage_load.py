# -*- coding: utf-8 -*-
"""Исправление загрузки браков"""

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим загрузку браков и исправляем
old_load = '''            marriages_raw = data.get("marriages", [])
            self.marriages = {}
            for item in marriages_raw:
                # Поддержка старого формата (список) и нового (словарь)
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    # Старый формат: [id1, id2]
                    h_id, w_id = str(item[0]), str(item[1])
                    self.marriages[tuple(sorted((h_id, w_id)))] = {"date": ""}
                elif isinstance(item, dict):
                    # Новый формат: {"persons": [id1, id2], "date": "ДД.ММ.ГГГГ"}
                    persons_list = item.get("persons", [])
                    marriage_date = item.get("date", "")
                    if len(persons_list) == 2:
                        p1, p2 = str(persons_list[0]), str(persons_list[1])
                        self.marriages[tuple(sorted((p1, p2)))] = {"date": marriage_date}'''

new_load = '''            marriages_raw = data.get("marriages", [])
            self.marriages = {}
            for item in marriages_raw:
                try:
                    # Поддержка старого формата (список) и нового (словарь)
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        # Старый формат: [id1, id2]
                        h_id, w_id = str(item[0]), str(item[1])
                        self.marriages[tuple(sorted((h_id, w_id)))] = {"date": ""}
                    elif isinstance(item, dict):
                        # Новый формат: {"persons": [id1, id2], "date": "ДД.ММ.ГГГГ"}
                        # ИЛИ {"persons": {"0": id1, "1": id2}, ...}
                        persons_data = item.get("persons", [])
                        if isinstance(persons_data, dict):
                            # Словарь с ключами "0", "1"
                            p1 = str(persons_data.get("0", persons_data.get("1", "")))
                            p2 = str(persons_data.get("1", persons_data.get("0", "")))
                        elif isinstance(persons_data, (list, tuple)) and len(persons_data) == 2:
                            # Список
                            p1, p2 = str(persons_data[0]), str(persons_data[1])
                        else:
                            continue
                        marriage_date = item.get("date", "")
                        if p1 and p2:
                            self.marriages[tuple(sorted((p1, p2)))] = {"date": marriage_date}
                except Exception as e:
                    print(f"Ошибка загрузки брака {item}: {e}")'''

content = content.replace(old_load, new_load)

with open('models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Исправлена загрузка браков')
