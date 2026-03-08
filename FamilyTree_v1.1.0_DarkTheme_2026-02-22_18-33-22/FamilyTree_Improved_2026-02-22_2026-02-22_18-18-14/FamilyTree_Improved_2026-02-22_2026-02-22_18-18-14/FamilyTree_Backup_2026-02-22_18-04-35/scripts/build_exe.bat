@echo off
cd /d "%~dp0.."

if exist "dist\Семейное_древо" rmdir /s /q "dist\Семейное_древо"

pip install pyinstaller pillow
python -m PyInstaller build_exe.spec --clean

echo.
echo Build complete. See dist\Семейное_древо\Семейное_древо.exe
pause
