@echo off
chcp 65001 >nul
title Очистка структуры проекта

echo ========================================
echo   Очистка структуры проекта
echo ========================================
echo.

REM Создаём папку для старых версий
if not exist "_old_versions" mkdir _old_versions
echo [OK] Создана папка _old_versions

REM Перемещаем старые версии
echo.
echo Перемещение старых версий...
for /d %%d in ("FamilyTree_*") do (
    if exist "%%d" (
        move "%%d" "_old_versions\" >nul 2>&1
        echo   - %%d
    )
)

REM Перемещаем архивы
if exist "_archive" (
    echo.
    echo Перемещение архивов...
    move "_archive" "_old_versions\" >nul 2>&1
    echo   - _archive
)

REM Перемещаем временные файлы Python
echo.
echo Очистка временных файлов Python...
if exist "__pycache__" (
    rmdir /s /q "__pycache__" 2>nul
    echo   - Удалён __pycache__
)

REM Перемещаем файлы данных в data папку
if not exist "data" mkdir data
echo.
echo Перемещение файлов данных...
for %%f in (family_tree_*.json users.json palette.json window_settings.json login_remember.json) do (
    if exist "%%f" (
        move "%%f" "data\" >nul 2>&1
        echo   - %%f
    )
)

echo.
echo ========================================
echo   Готово!
echo ========================================
echo.
echo Структура проекта приведена в порядок.
echo Старые версии перемещены в _old_versions
echo Файлы данных перемещены в data
echo.
pause
