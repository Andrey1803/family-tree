@echo off
chcp 65001 >nul
title Семейное древо

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

REM Запуск приложения
start "Семейное древо" python main.py
