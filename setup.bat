@echo off
title BeautyQ - Full Setup and Run
color 0D
cd /d "%~dp0"

echo ============================================
echo   BeautyQ Salon Booking System - Setup
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found. Install from https://www.python.org/
        pause
        exit /b 1
    )
    set PYTHON=py -3
) else (
    set PYTHON=python
)

if not exist "venv\Scripts\activate.bat" (
    echo [1/5] Creating virtual environment...
    %PYTHON% -m venv venv
) else (
    echo [1/5] Virtual environment OK.
)

echo [2/5] Activating venv...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt

if not exist ".env" (
    echo [3b] Creating .env from template...
    copy .env.example .env
)

echo [4/5] Database migrations...
python manage.py migrate

echo [5/5] Starting server (see run.bat if port busy)...
echo.
call run.bat
