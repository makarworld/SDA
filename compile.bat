@echo off
cd /d "%~dp0"

python -m pip install -q pyinstaller
if errorlevel 1 exit /b 1

python -m PyInstaller --noconfirm --clean --onefile --windowed --name gui --icon icon.ico gui.py
if errorlevel 1 exit /b 1

if exist dist\gui.exe move /y dist\gui.exe .\gui.exe >nul

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q gui.spec 2>nul

echo OK: gui.exe
pause
