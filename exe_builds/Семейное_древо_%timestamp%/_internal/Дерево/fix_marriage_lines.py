# -*- coding: utf-8 -*-
"""Исправление загрузки браков - строки 373-378"""

with open('models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку 373-378 и заменяем
new_lines = []
for i, line in enumerate(lines):
    if i == 372:  # строка 373
        # Заменяем весь цикл загрузки браков
        new_lines.append('            marriages_raw = data.get("marriages", [])\n')
        new_lines.append('            self.marriages = set()\n')
        new_lines.append('            for pair in marriages_raw:\n')
        new_lines.append('                try:\n')
        new_lines.append('                    if isinstance(pair, dict):\n')
        new_lines.append('                        # Новый формат: {"persons": [id1, id2]}\n')
        new_lines.append('                        persons_list = pair.get("persons", [])\n')
        new_lines.append('                        if isinstance(persons_list, (list, tuple)) and len(persons_list) >= 2:\n')
        new_lines.append('                            h_id, w_id = str(persons_list[0]), str(persons_list[1])\n')
        new_lines.append('                            self.marriages.add(tuple(sorted((h_id, w_id))))\n')
        new_lines.append('                    elif isinstance(pair, (list, tuple)) and len(pair) >= 2:\n')
        new_lines.append('                        # Старый формат: [id1, id2]\n')
        new_lines.append('                        h_id, w_id = str(pair[0]), str(pair[1])\n')
        new_lines.append('                        self.marriages.add(tuple(sorted((h_id, w_id))))\n')
        new_lines.append('                except Exception as e:\n')
        new_lines.append('                    print(f"Ошибка загрузки брака {pair}: {e}")\n')
        # Пропускаем следующие 5 строк (старый код)
        skip = 5
    elif i > 372 and skip > 0:
        skip -= 1
        continue
    else:
        new_lines.append(line)

with open('models.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('OK - Исправлена загрузка браков (строки 373-378)')
