$originalDir = Get-Location
try {
    Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'
    
    # Создаём простой скрипт для проверки
    $checkScript = @'
import sqlite3
conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
result = f"Columns: {columns}\nphoto_full exists: {'photo_full' in columns}"
with open('check_output.txt', 'w', encoding='utf-8') as f:
    f.write(result)
conn.close()
'@
    
    # Записываем скрипт в файл
    Set-Content -Path "temp_check.py" -Value $checkScript -Encoding UTF8 -NoNewline
    
    # Запускаем Python через cmd
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c python temp_check.py" -Wait -NoNewWindow
    
    # Читаем результат
    if (Test-Path "check_output.txt") {
        Write-Host "=== RESULT ==="
        Get-Content "check_output.txt" -Encoding UTF8
    } else {
        Write-Host "Result file not created. Checking for errors..."
        if (Test-Path "temp_check.py") {
            Write-Host "temp_check.py exists"
        }
    }
    
    # Чистим
    if (Test-Path "temp_check.py") { Remove-Item "temp_check.py" }
    if (Test-Path "check_output.txt") { Remove-Item "check_output.txt" }
}
finally {
    Set-Location $originalDir
}
