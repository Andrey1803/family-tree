$originalDir = Get-Location
try {
    Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'
    
    # Создаём скрипт для проверки
    $checkScript = @'
import sqlite3
import os
import sys

# Меняем рабочую директорию на директорию скрипта
os.chdir(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd())

print(f"Working directory: {os.getcwd()}", file=sys.stderr)
print(f"DB exists: {os.path.exists('family_tree.db')}", file=sys.stderr)

conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print(f"RESULT: {columns}", file=sys.stderr)
print(f"photo_full exists: {'photo_full' in columns}", file=sys.stderr)
conn.close()
'@
    
    $checkScript | Out-File -FilePath "temp_check.py" -Encoding UTF8 -NoNewline
    
    # Запускаем Python скрипт с перенаправлением вывода
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "temp_check.py"
    $psi.WorkingDirectory = (Get-Location).Path
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    
    $process = [System.Diagnostics.Process]::Start($psi)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    
    Write-Host "=== STDOUT ==="
    Write-Host $stdout
    Write-Host "=== STDERR ==="
    Write-Host $stderr
    
    # Чистим
    if (Test-Path "temp_check.py") { Remove-Item "temp_check.py" }
}
finally {
    Set-Location $originalDir
}
