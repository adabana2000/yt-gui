@echo off
echo YouTube Downloader - Installation Script
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python found
echo.

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: FFmpeg is not installed or not in PATH
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo.
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

:: Create .env file if not exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
)

:: Create directories
if not exist downloads mkdir downloads
if not exist data mkdir data
if not exist logs mkdir logs

echo.
echo ==========================================
echo Installation completed successfully!
echo.
echo To start the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: python main.py
echo.
echo For API mode: python main.py --mode api
echo For CLI mode: python main.py --mode cli --url "YOUR_URL"
echo ==========================================
pause
