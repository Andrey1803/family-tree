@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Building...
set OUT=%USERPROFILE%\FamilyTree_build
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%" 2>nul

py -3.11 -m PyInstaller build_exe.spec --noconfirm --clean --distpath "%OUT%" --workpath "%OUT%\build"
if %errorlevel% neq 0 (
    echo Build failed
    pause
    exit /b 1
)

REM Copy data folder to build
echo Copying data folder...
if not exist "%OUT%\Семейное_древо\data" mkdir "%OUT%\Семейное_древо\data"
xcopy /Y /I "data\*.*" "%OUT%\Семейное_древо\data\" 2>nul

echo Done: %OUT%\Семейное_древо\Семейное_древо.exe
pause
