@echo off
cd /d "%~dp0"
echo 🎬 Starting YouTube Automation Scheduler...

if not exist .venv (
    echo ❌ Python virtual environment (.venv) not found!
    echo    Please run: python -m venv .venv
    pause
    exit /b
)

:: Activate venv
call .venv\Scripts\activate

:: Check for .env file
if not exist .env (
    echo ⚠️  .env file not found! Using .env.example settings...
    copy .env.example .env >nul
    echo    Please edit .env with your API keys later.
    timeout /t 5
)

:: Run scheduler loop
python scheduler.py

pause
