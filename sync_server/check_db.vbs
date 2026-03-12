Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Получаем путь к скрипту
strWorkingDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Меняем рабочую директорию и запускаем Python
objShell.CurrentDirectory = strWorkingDir

' Создаём временный скрипт для проверки
Set objFile = objFSO.CreateTextFile("temp_check.py", True, True)
objFile.WriteLine "import sqlite3"
objFile.WriteLine "conn = sqlite3.connect('family_tree.db')"
objFile.WriteLine "cursor = conn.cursor()"
objFile.WriteLine "cursor.execute('PRAGMA table_info(persons)')"
objFile.WriteLine "columns = [row[1] for row in cursor.fetchall()]"
objFile.WriteLine "print('Columns:', columns)"
objFile.WriteLine "print('photo_full exists:', 'photo_full' in columns)"
objFile.WriteLine "conn.close()"
objFile.Close

' Запускаем Python
objShell.Run "python temp_check.py > check_result.txt 2>&1", 0, True
WScript.Sleep 2000

' Читаем результат
If objFSO.FileExists("check_result.txt") Then
    Set objResult = objFSO.OpenTextFile("check_result.txt", 1)
    WScript.Echo objResult.ReadAll
    objResult.Close
    objFSO.DeleteFile "check_result.txt"
End If

objFSO.DeleteFile "temp_check.py"
