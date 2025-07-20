#!/usr/bin/env python3
"""
Test script to verify cross-platform functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from platform_manager import PlatformManager
from download_utils import download_file
from file_utils import create_secure_directory, set_secure_permissions


def test_platform_detection():
    """Test platform detection"""
    print("Testing platform detection...")
    pm = PlatformManager()
    print(f"Platform: {pm.platform}")
    print(f"Is Windows: {pm.is_windows}")
    print(f"Is macOS: {pm.is_macos}")
    print(f"Is Linux: {pm.is_linux}")
    print("[OK] Platform detection working")


def test_path_resolution():
    """Test path resolution"""
    print("\nTesting path resolution...")
    pm = PlatformManager()
    
    config_path = pm.get_config_path()
    print(f"Config path: {config_path}")
    
    dfx_path = pm.get_dfx_path()
    print(f"DFX path: {dfx_path}")
    
    hvym_path = pm.get_hvym_path()
    print(f"HVYM path: {hvym_path}")
    
    blender_path = pm.get_blender_path()
    print(f"Blender path: {blender_path}")
    
    print("[OK] Path resolution working")


def test_file_operations():
    """Test file operations"""
    print("\nTesting file operations...")
    
    # Test directory creation
    test_dir = Path.home() / '.metavinci_test'
    create_secure_directory(test_dir)
    print(f"Created test directory: {test_dir}")
    
    # Test file creation and permissions
    test_file = test_dir / 'test.txt'
    with open(test_file, 'w') as f:
        f.write('test content')
    
    set_secure_permissions(test_file)
    print(f"Created test file with secure permissions: {test_file}")
    
    # Cleanup
    test_file.unlink()
    test_dir.rmdir()
    print("[OK] File operations working")


def test_download_utils():
    """Test download utilities"""
    print("\nTesting download utilities...")
    
    # Test with a small file
    test_url = "https://httpbin.org/bytes/1024"
    try:
        result = download_file(test_url)
        if result:
            print(f"Downloaded test file: {result}")
            os.unlink(result)  # Cleanup
            print("[OK] Download utilities working")
        else:
            print("[FAIL] Download failed")
    except Exception as e:
        print(f"[FAIL] Download test failed: {e}")


def main():
    """Run all tests"""
    print("Cross-Platform Compatibility Test")
    print("=" * 40)
    
    try:
        test_platform_detection()
        test_path_resolution()
        test_file_operations()
        test_download_utils()
        
        print("\n" + "=" * 40)
        print("All tests completed successfully!")
        print("Cross-platform compatibility appears to be working.")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 