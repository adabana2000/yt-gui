@echo off
REM ============================================================================
REM Windows Build Script for YouTube Downloader
REM ============================================================================
REM This script builds a standalone Windows executable using PyInstaller
REM
REM Requirements:
REM   - Python 3.10 or higher
REM   - PyInstaller installed (pip install pyinstaller)
REM   - All dependencies installed (pip install -r requirements.txt)
REM
REM Usage:
REM   build_windows.bat
REM
REM Output:
REM   dist/YouTubeDownloader.exe
REM ============================================================================

echo ============================================================================
echo YouTube Downloader - Windows Build Script
echo ============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ and add it to PATH
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

REM Check if PyInstaller is installed
echo.
echo [2/5] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyInstaller is not installed
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Install/update dependencies
echo.
echo [3/5] Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Clean previous build
echo.
echo [4/5] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist\YouTubeDownloader.exe del /q dist\YouTubeDownloader.exe

REM Build with PyInstaller
echo.
echo [5/5] Building executable with PyInstaller...
echo This may take several minutes...
pyinstaller --clean --noconfirm youtube-downloader.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Check if executable was created
if not exist dist\YouTubeDownloader.exe (
    echo.
    echo [ERROR] Executable was not created!
    echo Please check the build log above.
    pause
    exit /b 1
)

REM Success!
echo.
echo ============================================================================
echo Build completed successfully!
echo ============================================================================
echo.
echo Executable location: dist\YouTubeDownloader.exe
echo.

REM Get file size
for %%A in (dist\YouTubeDownloader.exe) do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo Executable size: !sizeMB! MB
)

echo.
echo You can now run the application by double-clicking:
echo   dist\YouTubeDownloader.exe
echo.
echo Or distribute the single .exe file to other Windows computers.
echo.
echo Note: First run may be slower as Windows Defender scans the file.
echo ============================================================================
echo.

pause
