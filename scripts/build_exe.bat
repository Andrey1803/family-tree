@echo off
chcp 65001 >nul
cd /d "%~dp0.."
pip install pyinstaller pillow
pyinstaller build_exe.spec
echo.
echo Готово: dist\Семейное_древо.exe
pause
