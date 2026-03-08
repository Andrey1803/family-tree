@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========== Если Permission denied ==========
echo Вариант 1: ESET -^> Настройка -^> Исключения -^> добавить папки выше
echo Вариант 2: Сборка через GitHub - см. СБОРКА_ЧЕРЕЗ_GITHUB.md
echo ===========================================
echo.
echo Сборка (Python 3.11)...
py -3.11 -m pip install -q -r requirements.txt pyinstaller 2>nul
taskkill /F /IM Семейное_древо.exe 2>nul
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
set OUT=%USERPROFILE%\FamilyTree_build
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%" 2>nul
py -3.11 -m PyInstaller build_exe.spec --noconfirm --clean --distpath "%OUT%" --workpath "%OUT%\build"
if %errorlevel% neq 0 (echo Ошибка сборки & pause & exit /b 1)
echo.
echo Готово. Запустите: %OUT%\Семейное_древо\Семейное_древо.exe
start "" "%OUT%\Семейное_древо"
pause
