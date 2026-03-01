@echo off
chcp 65001 >nul
title Семейное древо

echo ========================================
echo    Семейное древо - Запуск
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
echo Запуск приложения...
echo.
echo Нажмите любую клавишу для запуска...
pause >nul

REM Запуск приложения
python main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo ОШИБКА при запуске приложения!
    echo ========================================
    echo.
    pause
)
