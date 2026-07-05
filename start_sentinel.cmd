@echo off
setlocal
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0start_sentinel.ps1"
if errorlevel 1 (
    echo.
    echo Sentinel failed to start.
    pause
)
endlocal
exit /b 0
