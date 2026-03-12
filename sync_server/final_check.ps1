$originalDir = Get-Location
Set-Location -LiteralPath 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server'

# Создаём скрипт для проверки
$checkScript = @'
import sqlite3
conn = sqlite3.connect('family_tree.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(persons)")
columns = [row[1] for row in cursor.fetchall()]
print("Колонки:", columns)
print("photo_full есть:", 'photo_full' in columns)
conn.close()
'@

$checkScript | Out-File -FilePath "temp_check.py" -Encoding utf8
python temp_check.py
Remove-Item temp_check.py

Set-Location $originalDir
