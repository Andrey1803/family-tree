$originalDir = Get-Location
try {
    Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'
    
    # Создаём Python скрипт
    $pythonCode = @'
import sqlite3
import sys
import os

# Меняем рабочую директорию
os.chdir(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.')

print("Working directory:", os.getcwd(), file=sys.stderr)
print("DB exists:", os.path.exists('family_tree.db'), file=sys.stderr)

try:
    conn = sqlite3.connect('family_tree.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Columns:", columns, file=sys.stderr)
    print("photo_full exists:", 'photo_full' in columns, file=sys.stderr)
    conn.close()
except Exception as e:
    print("Error:", e, file=sys.stderr)
'@
    
    # Записываем в файл
    Set-Content -Path "check_final.py" -Value $pythonCode -Encoding UTF8 -NoNewline
    
    # Запускаем через cmd
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c python check_final.py 2>&1"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.WorkingDirectory = (Get-Location).Path
    
    $process = [System.Diagnostics.Process]::Start($psi)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    
    Write-Host "=== OUTPUT ==="
    Write-Host $stdout
    Write-Host $stderr
    
    # Чистим
    if (Test-Path "check_final.py") { Remove-Item "check_final.py" }
}
finally {
    Set-Location $originalDir
}
