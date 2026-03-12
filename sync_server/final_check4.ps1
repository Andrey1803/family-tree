$originalDir = Get-Location
try {
    Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'
    
    # Создаём скрипт для проверки
    $checkScript = @'
import sqlite3
import os
import sys

# Меняем рабочую директорию на директорию скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Подключаемся к БД
conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]

# Записываем результат в файл
with open('db_check_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"DB exists: {os.path.exists('family_tree.db')}\n")
    f.write(f"Columns: {columns}\n")
    f.write(f"photo_full exists: {'photo_full' in columns}\n")

conn.close()
print("Check completed!")
'@
    
    $checkScript | Out-File -FilePath "temp_check.py" -Encoding UTF8 -NoNewline
    
    # Запускаем Python скрипт
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "temp_check.py"
    $psi.WorkingDirectory = (Get-Location).Path
    $psi.UseShellExecute = $false
    $process = [System.Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    
    # Читаем результат
    if (Test-Path "db_check_result.txt") {
        Write-Host "=== RESULT ==="
        Get-Content "db_check_result.txt" -Encoding UTF8
    } else {
        Write-Host "Result file not created"
    }
    
    # Чистим
    if (Test-Path "temp_check.py") { Remove-Item "temp_check.py" }
}
finally {
    Set-Location $originalDir
}
