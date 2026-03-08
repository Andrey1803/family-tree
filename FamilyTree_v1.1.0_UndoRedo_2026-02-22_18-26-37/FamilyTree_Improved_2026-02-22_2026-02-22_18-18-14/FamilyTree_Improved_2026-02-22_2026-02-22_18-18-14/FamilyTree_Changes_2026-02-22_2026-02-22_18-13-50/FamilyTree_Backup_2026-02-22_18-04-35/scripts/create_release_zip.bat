@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo Создание ZIP с исходниками...
python "%~dp0create_release_zip.py"
pause
