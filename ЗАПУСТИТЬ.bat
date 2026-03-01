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
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python найден
echo.

REM Запуск приложения
echo Запуск приложения...
python main.py

if errorlevel 1 (
    echo.
    echo ОШИБКА при запуске приложения!
    pause
)
