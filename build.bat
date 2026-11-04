@echo off
title AutoTyper Build Script
cd /d "%~dp0"

echo [1/3] Building standalone AutoTyper.exe...
venv\Scripts\pyinstaller.exe --onefile --noconsole --name AutoTyper main.py

echo [2/3] Building AutoTyper_Setup.exe Installer...
venv\Scripts\pyinstaller.exe --onefile --noconsole --name AutoTyper_Setup --add-data "dist/AutoTyper.exe;." installer.py

echo [3/3] Build finished! Files available in dist/
dir dist\*.exe
pause
