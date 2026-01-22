@echo off
REM Startup script for the RAG API (Windows)

echo Starting Islamic Finance RAG API...
echo.

REM Check if .env exists
if not exist .env (
    echo Warning: .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env and set your OPENAI_API_KEY
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the server
echo.
echo Starting server...
python main.py

pause
