$fso = New-Object -ComObject Scripting.FileSystemObject
$folder = $fso.GetFolder("d:\Мои документы\Рабочий стол\hobby\Projects\Family tree")
Write-Host $folder.ShortPath
