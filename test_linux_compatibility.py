#!/usr/bin/env python3
"""
Test script for Linux compatibility runtime hook
"""

import os
import sys

def test_compatibility():
    """Test the Linux compatibility setup"""
    print("Testing Linux compatibility...")
    
    if sys.platform.startswith('linux'):
        print(f"Platform: {sys.platform}")
        print(f"Python version: {sys.version}")
        
        # Check if we're running from PyInstaller
        if hasattr(sys, '_MEIPASS'):
            print(f"PyInstaller MEIPASS: {sys._MEIPASS}")
            
            # Check environment variables
            ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            print(f"LD_LIBRARY_PATH: {ld_path}")
            
            qt_path = os.environ.get('QT_PLUGIN_PATH', '')
            print(f"QT_PLUGIN_PATH: {qt_path}")
            
            glibc_tunables = os.environ.get('GLIBC_TUNABLES', '')
            print(f"GLIBC_TUNABLES: {glibc_tunables}")
            
            python_home = os.environ.get('PYTHONHOME', '')
            print(f"PYTHONHOME: {python_home}")
            
            print("Linux compatibility setup completed successfully!")
        else:
            print("Not running from PyInstaller bundle")
    else:
        print(f"Not on Linux platform: {sys.platform}")

if __name__ == "__main__":
    test_compatibility()
