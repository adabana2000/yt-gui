# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for YouTube Downloader
This creates a standalone Windows executable with all dependencies bundled.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

# Project root
project_root = Path('.')

# Collect all data files
datas = []

# Add any additional data files here if needed
# datas.append(('path/to/data', 'destination/folder'))

# Hidden imports - packages that PyInstaller might miss
hiddenimports = [
    # Core dependencies
    'fastapi',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',

    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.sql',

    # Alembic
    'alembic',
    'alembic.runtime.migration',

    # yt-dlp and extractors
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.extractor.youtube',

    # Cryptography
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.kdf',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',

    # Browser cookies
    'browser_cookie3',

    # PySide6
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',

    # Google auth
    'google.auth',
    'google.auth.transport',
    'google_auth_oauthlib',

    # APScheduler
    'apscheduler',
    'apscheduler.schedulers',
    'apscheduler.schedulers.background',
    'apscheduler.triggers',
    'apscheduler.triggers.cron',

    # Other
    'aiohttp',
    'aiofiles',
    'redis',
    'pydantic',
    'pydantic_settings',
    'prometheus_client',
    'websockets',
]

# Collect all yt-dlp extractors
hiddenimports.extend(collect_submodules('yt_dlp.extractor'))

# Binaries to exclude (these are usually bundled incorrectly)
binaries = []

# Analysis
a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Exclude tkinter if not used
        'matplotlib',  # Exclude if not used
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ (Python ZIP archive)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment and set icon path if you have an icon file
    # icon='resources/icon.ico',
    version_file=None,  # Can add version info file here
)

# Optional: Create a COLLECT for folder-based distribution
# Uncomment if you prefer a folder with multiple files instead of single .exe
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YouTubeDownloader',
)
"""
