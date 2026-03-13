import os

# Переходим в директорию скрипта
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Проверяем dist
dist_files = os.listdir('dist')
result = []
result.append("Files in dist: " + str(dist_files))

# Проверяем EXE
exe_name = 'Семейное_древо.exe'
if exe_name in dist_files:
    size = os.path.getsize(exe_name)
    result.append(f"EXE found: {exe_name}")
    result.append(f"Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
else:
    result.append(f"EXE {exe_name} NOT found!")

# Записываем в файл
with open('check_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
