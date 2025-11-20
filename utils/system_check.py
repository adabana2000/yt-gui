"""System requirements checker"""
import subprocess
import sys
from typing import Dict, List, Tuple


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if FFmpeg is installed

    Returns:
        Tuple of (is_installed, version_or_error)
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.split('\n')[0]
        return True, version_line
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return False, str(e)


def check_yt_dlp() -> Tuple[bool, str]:
    """Check if yt-dlp is installed

    Returns:
        Tuple of (is_installed, version_or_error)
    """
    try:
        import yt_dlp
        version = yt_dlp.version.__version__
        return True, f"yt-dlp version {version}"
    except ImportError as e:
        return False, str(e)


def check_all_requirements() -> Dict[str, Tuple[bool, str]]:
    """Check all system requirements

    Returns:
        Dictionary of requirement checks
    """
    checks = {
        'ffmpeg': check_ffmpeg(),
        'yt-dlp': check_yt_dlp(),
    }
    return checks


def print_system_check():
    """Print system check results"""
    print("System Requirements Check")
    print("=" * 50)

    checks = check_all_requirements()

    for name, (installed, info) in checks.items():
        status = "✓" if installed else "✗"
        print(f"{status} {name}: {info}")

    print("=" * 50)

    # Check if all requirements are met
    all_ok = all(installed for installed, _ in checks.values())

    if not all_ok:
        print("\nWarning: Some requirements are not met!")
        print("Please install missing components:")

        if not checks['ffmpeg'][0]:
            print("\nFFmpeg:")
            print("  Windows: choco install ffmpeg")
            print("  macOS: brew install ffmpeg")
            print("  Linux: sudo apt install ffmpeg")

        if not checks['yt-dlp'][0]:
            print("\nyt-dlp:")
            print("  pip install yt-dlp")
    else:
        print("\nAll requirements are met!")

    return all_ok


if __name__ == "__main__":
    sys.exit(0 if print_system_check() else 1)
