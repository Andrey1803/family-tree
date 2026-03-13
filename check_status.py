import os
import subprocess

# Переходим в директорию проекта
project_dir = r'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree'
os.chdir(project_dir)

# Git status
print("=" * 60)
print("GIT STATUS")
print("=" * 60)
result = subprocess.run(['git', 'status'], capture_output=True, text=True, encoding='utf-8')
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Проверка EXE файла
print("\n" + "=" * 60)
print("EXE FILE CHECK")
print("=" * 60)
dist_path = os.path.join(project_dir, 'dist')
exe_name = 'Семейное_древо.exe'
exe_path = os.path.join(dist_path, exe_name)

print(f"Dist folder exists: {os.path.isdir(dist_path)}")
if os.path.isdir(dist_path):
    print(f"Files in dist: {os.listdir(dist_path)}")
    
print(f"EXE exists: {os.path.exists(exe_path)}")
if os.path.exists(exe_path):
    size = os.path.getsize(exe_path)
    print(f"EXE size: {size} bytes ({size / 1024 / 1024:.2f} MB)")
else:
    print("EXE NOT FOUND!")
