#!/usr/bin/env python3
"""
Master Build Script for JarTool
Automates builds for all platforms: Windows, Linux, macOS
Usage: python build_all.py [platform]
Examples:
    python build_all.py          # Build for current platform
    python build_all.py windows  # Build for Windows
    python build_all.py linux    # Build for Linux
    python build_all.py macos    # Build for macOS
    python build_all.py all      # Build for all platforms (requires proper environment)
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_pip_dependencies():
    """Check and install required pip packages"""
    required = ['PyInstaller', 'PyQt6']
    missing = []
    
    for package in required:
        try:
            __import__(package.lower())
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        response = input("Install now? (y/n): ")
        if response.lower() == 'y':
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        else:
            return False
    else:
        print(f"✅ All pip dependencies installed")
    
    return True


def clean_all():
    """Clean all build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    dirs_to_clean = [
        'build', 'dist', '__pycache__',
        'AppDir', 'appimage-build',
        '*.spec', '*.AppImage', '*.dmg',
        '*.egg-info', '.pytest_cache'
    ]
    
    for pattern in dirs_to_clean:
        if '*' in pattern:
            # Handle glob patterns
            import glob
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"   🗑️  {path}/")
                elif os.path.isfile(path):
                    os.remove(path)
                    print(f"   🗑️  {path}")
        else:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    shutil.rmtree(pattern)
                else:
                    os.remove(pattern)
                print(f"   🗑️  {pattern}")
    
    print("✅ Clean completed")


def build_windows():
    """Build for Windows"""
    print_header("Building for Windows")
    
    if sys.platform != 'win32':
        print("⚠️  Cross-compilation for Windows not supported")
        print("   Run this on Windows or use Wine/VM")
        return False
    
    try:
        subprocess.check_call([sys.executable, 'build_windows.py'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows build failed: {e}")
        return False


def build_linux():
    """Build for Linux"""
    print_header("Building for Linux")
    
    if sys.platform != 'linux':
        print("⚠️  Cross-compilation for Linux not recommended")
        print("   Run this on Linux for best results")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        subprocess.check_call([sys.executable, 'build_linux.py'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Linux build failed: {e}")
        return False


def build_macos():
    """Build for macOS"""
    print_header("Building for macOS")
    
    if sys.platform != 'darwin':
        print("❌ macOS builds require macOS")
        print("   Run this on a Mac or use GitHub Actions")
        return False
    
    try:
        subprocess.check_call([sys.executable, 'build_macos.py'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ macOS build failed: {e}")
        return False


def build_current_platform():
    """Build for current platform"""
    platform = sys.platform
    
    if platform == 'win32':
        return build_windows()
    elif platform == 'linux':
        return build_linux()
    elif platform == 'darwin':
        return build_macos()
    else:
        print(f"❌ Unsupported platform: {platform}")
        return False


def create_distribution_summary():
    """Create summary of all distribution files"""
    print_header("Distribution Summary")
    
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("❌ No dist directory found")
        return
    
    files = list(dist_dir.iterdir())
    
    if not files:
        print("📭 No distribution files found")
        return
    
    print("📦 Distribution files:\n")
    
    total_size = 0
    for file in sorted(files):
        if file.is_file():
            size = file.stat().st_size
            size_mb = size / (1024 * 1024)
            total_size += size
            print(f"   {file.name:40} {size_mb:8.1f} MB")
        elif file.is_dir():
            # Calculate directory size
            size = sum(f.stat().st_size for f in file.rglob('*') if f.is_file())
            size_mb = size / (1024 * 1024)
            total_size += size
            print(f"   {file.name + '/':40} {size_mb:8.1f} MB")
    
    print(f"\n   {'Total size:':40} {total_size / (1024 * 1024):8.1f} MB")


def run_tests():
    """Run test suite before building"""
    print_header("Running Tests")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', 'test/', '-v'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Tests failed")
            print(result.stdout)
            print(result.stderr)
            response = input("Continue with build anyway? (y/n): ")
            return response.lower() == 'y'
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        response = input("Continue with build anyway? (y/n): ")
        return response.lower() == 'y'


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build JarTool for multiple platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              Build for current platform
  %(prog)s windows      Build for Windows only
  %(prog)s linux        Build for Linux only
  %(prog)s macos        Build for macOS only
  %(prog)s all          Build for all platforms (if supported)
  %(prog)s --clean      Clean all build artifacts
        """
    )
    
    parser.add_argument(
        'platform',
        nargs='?',
        default='current',
        choices=['current', 'windows', 'linux', 'macos', 'all'],
        help='Target platform (default: current)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build artifacts and exit'
    )
    
    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='Skip running tests'
    )
    
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency check'
    )
    
    args = parser.parse_args()
    
    # Handle clean option
    if args.clean:
        clean_all()
        return 0
    
    print_header("JarTool Multi-Platform Build System")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"Target: {args.platform}")
    
    # Pre-flight checks
    if not check_python_version():
        return 1
    
    if not args.skip_deps:
        if not check_pip_dependencies():
            return 1
    
    # Run tests
    if not args.no_tests:
        if not run_tests():
            return 1
    
    # Clean previous builds
    clean_all()
    
    # Build based on platform selection
    results = {}
    
    if args.platform == 'current':
        results['current'] = build_current_platform()
    elif args.platform == 'windows':
        results['windows'] = build_windows()
    elif args.platform == 'linux':
        results['linux'] = build_linux()
    elif args.platform == 'macos':
        results['macos'] = build_macos()
    elif args.platform == 'all':
        print("⚠️  Building for all platforms...")
        print("   This requires running on each platform separately")
        print("   or using cross-compilation tools.\n")
        
        # Try each platform
        if sys.platform == 'win32':
            results['windows'] = build_windows()
        elif sys.platform == 'linux':
            results['linux'] = build_linux()
        elif sys.platform == 'darwin':
            results['macos'] = build_macos()
    
    # Summary
    print_header("Build Summary")
    
    for platform, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {platform:12} {status}")
    
    # Show distribution files
    create_distribution_summary()
    
    # Return appropriate exit code
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
