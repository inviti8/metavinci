#!/usr/bin/env python3
"""
Runtime hook for PyInstaller to improve Linux compatibility
"""
import os
import sys

# Set environment variables for better compatibility
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['QT_DEBUG_PLUGINS'] = '0'

# Add current directory to library path for bundled libraries
if hasattr(sys, '_MEIPASS'):
    # Running from PyInstaller bundle
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
    
    # Set library path for bundled Qt libraries
    qt_lib_path = os.path.join(bundle_dir, 'PyQt5', 'Qt', 'lib')
    if os.path.exists(qt_lib_path):
        os.environ['LD_LIBRARY_PATH'] = qt_lib_path + ':' + os.environ.get('LD_LIBRARY_PATH', '')
