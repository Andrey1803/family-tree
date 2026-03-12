$originalDir = Get-Location
try {
    Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'
    
    # Получаем полный путь к БД через Get-Item
    $dbFile = Get-Item 'family_tree.db'
    $dbPath = $dbFile.FullName
    
    # Создаём скрипт для проверки с абсолютным путём
    $checkScript = @"
import sqlite3
import os
db_path = r'$dbPath'
print(f"DB path: {db_path}")
print(f"DB exists: {os.path.exists(db_path)}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Колонки:", columns)
print("photo_full есть:", 'photo_full' in columns)
conn.close()
"@
    
    $checkScript | Out-File -FilePath "temp_check.py" -Encoding UTF8 -NoNewline
    
    # Запускаем Python скрипт
    $pythonProcess = Start-Process -FilePath "python" -ArgumentList "temp_check.py" -WorkingDirectory (Get-Location).Path -Wait -NoNewWindow -PassThru -RedirectStandardOutput "output.txt" -RedirectStandardError "error.txt"
    
    # Читаем вывод
    if (Test-Path "output.txt") {
        Get-Content "output.txt" -Encoding UTF8
    }
    if (Test-Path "error.txt") {
        Get-Content "error.txt" -Encoding UTF8
    }
    
    # Чистим
    if (Test-Path "temp_check.py") { Remove-Item "temp_check.py" }
    if (Test-Path "output.txt") { Remove-Item "output.txt" }
    if (Test-Path "error.txt") { Remove-Item "error.txt" }
}
finally {
    Set-Location $originalDir
}
