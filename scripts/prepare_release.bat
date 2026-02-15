@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo === Подготовка к релизу v1.0 ===
echo.
echo 1. Проверка зависимостей...
pip show pyinstaller >nul 2>&1 || pip install pyinstaller
pip show pillow >nul 2>&1 || pip install pillow
echo.
echo 2. Сборка .exe...
pyinstaller -y build_exe.spec
if errorlevel 1 (
    echo Ошибка сборки.
    pause
    exit /b 1
)
echo.
echo Готово: dist\Семейное_древо.exe
echo.
echo Следующие шаги:
echo - Скопировать dist\Семейное_древо.exe в папку для распространения
echo - Обновить version.py и CHANGELOG.md с датой
echo - Создать ZIP с исходниками (исключить: dist, build, __pycache__, данные)
echo.
pause
