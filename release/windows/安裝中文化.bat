@echo off
rem XWVM zh-TW {{VERSION}} - Windows installer (double-click to run)
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0files\install_windows.ps1" -LanguagePack "%~dp0files\zh-TW-v1"
echo.
pause
