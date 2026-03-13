import os
# Используем относительный путь
exe_path = os.path.join('dist', 'Семейное_древо.exe')
result = []
if os.path.exists(exe_path):
    size = os.path.getsize(exe_path)
    result.append(f'EXE найден: {exe_path}')
    result.append(f'Размер: {size:,} байт ({size/1024/1024:.2f} MB)')
else:
    result.append('EXE файл НЕ найден!')
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        result.append(f'Содержимое dist/: {os.listdir(dist_dir)}')

with open('check_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
