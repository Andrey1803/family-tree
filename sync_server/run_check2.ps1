$scriptPath = "d:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server\check_db2.py"
$workingDir = "d:\Мои документы\Рабочий стол\hobby\Projects\Family tree\sync_server"

Start-Process -FilePath "python" -ArgumentList $scriptPath -WorkingDirectory $workingDir -Wait -NoNewWindow
