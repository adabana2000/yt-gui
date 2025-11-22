#!/bin/bash
# ============================================================================
# Windows Build Script for YouTube Downloader (Linux/Mac version)
# ============================================================================
# This script builds a standalone Windows executable using PyInstaller
# on Linux or macOS (cross-compilation)
#
# Requirements:
#   - Python 3.10 or higher
#   - PyInstaller installed (pip install pyinstaller)
#   - All dependencies installed (pip install -r requirements.txt)
#   - Wine (for testing the .exe on Linux/Mac - optional)
#
# Usage:
#   chmod +x build_windows.sh
#   ./build_windows.sh
#
# Output:
#   dist/YouTubeDownloader.exe
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "YouTube Downloader - Windows Build Script (Cross-platform)"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
echo "[1/5] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

python3 --version

# Check if PyInstaller is installed
echo ""
echo "[2/5] Checking PyInstaller..."
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} PyInstaller is not installed"
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Install/update dependencies
echo ""
echo "[3/5] Installing/updating dependencies..."
pip3 install -r requirements.txt

# Clean previous build
echo ""
echo "[4/5] Cleaning previous build..."
rm -rf build/
rm -rf dist/YouTubeDownloader.exe

# Build with PyInstaller
echo ""
echo "[5/5] Building executable with PyInstaller..."
echo "This may take several minutes..."
pyinstaller --clean --noconfirm youtube-downloader.spec

# Check if executable was created
if [ ! -f "dist/YouTubeDownloader.exe" ]; then
    echo ""
    echo -e "${RED}[ERROR]${NC} Executable was not created!"
    echo "Please check the build log above."
    exit 1
fi

# Success!
echo ""
echo "============================================================================"
echo -e "${GREEN}Build completed successfully!${NC}"
echo "============================================================================"
echo ""
echo "Executable location: dist/YouTubeDownloader.exe"
echo ""

# Get file size
size=$(stat -f%z "dist/YouTubeDownloader.exe" 2>/dev/null || stat -c%s "dist/YouTubeDownloader.exe" 2>/dev/null)
sizeMB=$((size / 1048576))
echo "Executable size: ${sizeMB} MB"

echo ""
echo "Transfer the executable to a Windows computer to run it."
echo ""
echo "Optional: Test with Wine (if installed):"
echo "  wine dist/YouTubeDownloader.exe"
echo ""
echo "Note: Cross-compiled executables may trigger antivirus warnings."
echo "      Building on a native Windows machine is recommended for distribution."
echo "============================================================================"
echo ""
