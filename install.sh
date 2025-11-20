#!/bin/bash

echo "YouTube Downloader - Installation Script"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: FFmpeg is not installed"
    echo "Please install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt install ffmpeg"
    echo ""
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Create directories
mkdir -p downloads data logs

# Make scripts executable
chmod +x install.sh

echo ""
echo "=========================================="
echo "Installation completed successfully!"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo ""
echo "For API mode: python main.py --mode api"
echo "For CLI mode: python main.py --mode cli --url \"YOUR_URL\""
echo "=========================================="
