@echo off
chcp 65001 >nul
cd /d "%~dp0.."
REM Удаляем старую папку onedir (если осталась)
if exist "dist\Семейное_древо" rmdir /s /q "dist\Семейное_древо"
pip install pyinstaller pillow
pyinstaller build_exe.spec --clean
echo.
echo Готово: dist\Семейное_древо.exe (один файл)
pause
