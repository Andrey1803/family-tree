@echo off
chcp 65001 >nul
title Сборка Семейное древо в EXE

echo ========================================
echo   Сборка Семейное древо в EXE
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ========================================
    echo ОШИБКА: Python не найден!
    echo ========================================
    echo.
    echo Установите Python с https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python найден
echo.

REM Проверка наличия PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Установка PyInstaller...
    pip install pyinstaller pillow
    echo [OK] PyInstaller установлен
    echo.
)

REM Очистка старых сборок
echo [INFO] Очистка старых сборок...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Семейное_древо" rmdir /s /q "Семейное_древо"
echo [OK] Очистка завершена
echo.

REM Создание папки для сборок
if not exist "exe_builds" mkdir "exe_builds"
echo [OK] Папка exe_builds создана
echo.

REM Сборка
echo ========================================
echo   Начало сборки...
echo ========================================
echo.

pyinstaller build_exe.spec

if errorlevel 1 (
    echo.
    echo ========================================
    echo ОШИБКА при сборке!
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Сборка завершена успешно!
echo ========================================
echo.

REM Перемещение результата в exe_builds
if exist "dist\Семейное_древо" (
    set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    set TIMESTAMP=%TIMESTAMP: =0%
    
    echo [INFO] Перемещение в exe_builds/Семейное_дрено_%TIMESTAMP%...
    move "dist\Семейное_древо" "exe_builds\Семейное_древо_%TIMESTAMP%"
    
    echo.
    echo ========================================
    echo   Готово!
    echo ========================================
    echo.
    echo EXE файл находится в папке:
    echo   exe_builds\Семейное_древо_%TIMESTAMP%\
    echo.
    echo Для запуска откройте папку и запустите:
    echo   Семейное_древо.exe
    echo.
) else (
    echo ========================================
    echo ОШИБКА: Файл не найден!
    echo ========================================
    echo.
)

pause
