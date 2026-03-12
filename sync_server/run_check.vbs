Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Получаем путь к скрипту
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName) & "\check_columns.py"
strWorkingDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Меняем рабочую директорию и запускаем Python
objShell.CurrentDirectory = strWorkingDir
objShell.Run "python check_columns.py", 1, True
