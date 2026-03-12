# Git status check script
$gitPath = "d:\Мои документы\Рабочий стол\hobby\Projects\Family tree"
Set-Location -LiteralPath $gitPath
$output = git status 2>&1
$output | Out-File -FilePath "git_output.txt" -Encoding UTF8
Write-Host "Git status saved to git_output.txt"
