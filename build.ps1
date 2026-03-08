# Сборка приложения "Семейное древо"
$OUT = "$env:USERPROFILE\FamilyTree_build"

Write-Host "Building..."
if (Test-Path $OUT) { Remove-Item -Recurse -Force $OUT }
New-Item -ItemType Directory -Path $OUT | Out-Null

# Запуск PyInstaller
py -3.11 -m PyInstaller build_exe.spec --noconfirm --clean --distpath "$OUT" --workpath "$OUT\build"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed" -ForegroundColor Red
    pause
    exit 1
}

# Копирование папки data (EXE создаётся прямо в $OUT, а не в подпапке)
Write-Host "Copying data folder..."
$dataDest = "$OUT\data"
if (!(Test-Path $dataDest)) { New-Item -ItemType Directory -Path $dataDest | Out-Null }
Copy-Item "data\*.*" -Destination $dataDest -Force

Write-Host "Done: $OUT\Семейное_древо.exe" -ForegroundColor Green
Start-Process explorer.exe "$OUT"
