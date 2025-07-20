#!/usr/bin/env python3
"""
Test script to verify build dependencies are available
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")
    
    try:
        from platform_manager import PlatformManager
        print("✓ platform_manager.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import platform_manager.py: {e}")
        return False
    
    try:
        from download_utils import download_file
        print("✓ download_utils.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import download_utils.py: {e}")
        return False
    
    try:
        from file_utils import set_secure_permissions
        print("✓ file_utils.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import file_utils.py: {e}")
        return False
    
    try:
        from metavinci import Metavinci
        print("✓ metavinci.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import metavinci.py: {e}")
        return False
    
    return True

def test_file_existence():
    """Test that all required files exist"""
    print("\nTesting file existence...")
    
    required_files = [
        'metavinci.py',
        'platform_manager.py',
        'download_utils.py',
        'file_utils.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"✓ {file_name} exists")
        else:
            print(f"✗ {file_name} missing")
            all_exist = False
    
    return all_exist

def test_build_script_dependencies():
    """Test that build scripts can find all dependencies"""
    print("\nTesting build script dependencies...")
    
    # Test build_cross_platform.py dependencies
    try:
        from build_cross_platform import CrossPlatformBuilder
        builder = CrossPlatformBuilder()
        print("✓ build_cross_platform.py can create builder instance")
    except Exception as e:
        print(f"✗ build_cross_platform.py failed: {e}")
        return False
    
    # Test that all source files are found
    source_files = [
        ('metavinci.py', 'metavinci.py'),
        ('requirements.txt', 'requirements.txt'),
        ('platform_manager.py', 'platform_manager.py'),
        ('download_utils.py', 'download_utils.py'),
        ('file_utils.py', 'file_utils.py'),
    ]
    
    for src, dst in source_files:
        if Path(src).exists():
            print(f"✓ {src} found for build")
        else:
            print(f"✗ {src} missing for build")
            return False
    
    return True

def test_pyinstaller_availability():
    """Test that PyInstaller is available"""
    print("\nTesting PyInstaller availability...")
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} available")
        return True
    except ImportError:
        print("✗ PyInstaller not installed")
        print("Install with: pip install pyinstaller")
        return False

def main():
    """Run all tests"""
    print("Build Dependency Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_file_existence,
        test_build_script_dependencies,
        test_pyinstaller_availability
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! Build should work correctly.")
        print("You can now run: python build_cross_platform.py --platform linux")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 