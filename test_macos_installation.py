#!/usr/bin/env python3
"""
Test script for macOS installation helper
Run this to validate the installation process on macOS
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import requests
        print("✅ requests module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import requests: {e}")
        return False
    
    try:
        from macos_install_helper import MacOSInstallHelper
        print("✅ MacOSInstallHelper imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MacOSInstallHelper: {e}")
        return False
    
    return True

def test_platform_manager():
    """Test the platform manager functionality"""
    print("\nTesting platform manager...")
    
    try:
        from platform_manager import PlatformManager
        pm = PlatformManager()
        
        print(f"✅ Platform: {pm.platform}")
        print(f"✅ Is macOS: {pm.is_macos}")
        print(f"✅ Config path: {pm.get_config_path()}")
        print(f"✅ Bin path: {pm.get_bin_path()}")
        print(f"✅ HVYM path: {pm.get_hvym_path()}")
        
        return True
    except Exception as e:
        print(f"❌ Platform manager test failed: {e}")
        return False

def test_installation_helper():
    """Test the installation helper functionality"""
    print("\nTesting installation helper...")
    
    try:
        from macos_install_helper import MacOSInstallHelper
        helper = MacOSInstallHelper()
        
        # Test directory creation
        print("Testing directory creation...")
        if helper.ensure_directories():
            print("✅ Directories created successfully")
        else:
            print("❌ Directory creation failed")
            return False
        
        # Test status checking
        print("Testing status checking...")
        status = helper.get_installation_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test permission checking
        print("Testing permission checking...")
        issues = helper.check_macos_permissions()
        if issues:
            print("⚠️  Permission issues found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("✅ No permission issues found")
        
        return True
    except Exception as e:
        print(f"❌ Installation helper test failed: {e}")
        return False

def test_main_application_integration():
    """Test the main application integration"""
    print("\nTesting main application integration...")
    
    try:
        # Test the download function
        from metavinci import download_and_install_hvym_cli, get_latest_hvym_release_asset_url
        
        print("Testing URL retrieval...")
        url = get_latest_hvym_release_asset_url()
        print(f"✅ Latest release URL: {url}")
        
        # Test the download function (without actually downloading)
        print("Testing download function structure...")
        from platform_manager import PlatformManager
        pm = PlatformManager()
        bin_dir = pm.get_bin_path()
        print(f"✅ Bin directory: {bin_dir}")
        
        return True
    except Exception as e:
        print(f"❌ Main application integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=== macOS Installation Test Suite ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current directory: {os.getcwd()}")
    
    # Check if we're on macOS
    if sys.platform != "darwin":
        print("⚠️  This test is designed for macOS. Some tests may fail on other platforms.")
    
    tests = [
        ("Import Test", test_imports),
        ("Platform Manager Test", test_platform_manager),
        ("Installation Helper Test", test_installation_helper),
        ("Main Application Integration Test", test_main_application_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The macOS installation should work correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
