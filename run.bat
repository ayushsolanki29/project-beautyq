@echo off
title BeautyQ - Run Server
cd /d "%~dp0"

set PORT=8000

:: Find first free port from 8000 to 8010
:check_port
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo Port %PORT% is busy, trying next...
    set /a PORT+=1
    if %PORT% GTR 8010 (
        echo ERROR: No free port between 8000-8010. Close other apps and retry.
        pause
        exit /b 1
    )
    goto check_port
)

if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo ============================================
echo   BeautyQ running on port %PORT%
echo ============================================
echo   Open: http://127.0.0.1:%PORT%/
echo   Admin: http://127.0.0.1:%PORT%/myadmin/
echo ============================================
echo.

:: Wait for server then open browser (run in background)
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:%PORT%/"

python manage.py runserver 127.0.0.1:%PORT%
pause
