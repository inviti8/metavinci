#!/usr/bin/env python3
"""
PyInstaller runtime hook for Linux compatibility
This helps avoid glibc version issues by setting appropriate environment variables
"""

import os
import sys

def setup_linux_compatibility():
    """Set up Linux compatibility environment variables"""
    if sys.platform.startswith('linux'):
        # Set LD_LIBRARY_PATH to prefer bundled libraries
        if hasattr(sys, '_MEIPASS'):
            meipass = sys._MEIPASS
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            if current_ld_path:
                os.environ['LD_LIBRARY_PATH'] = f"{meipass}:{current_ld_path}"
            else:
                os.environ['LD_LIBRARY_PATH'] = meipass
            
            # Set other compatibility variables
            os.environ['PYTHONPATH'] = meipass
            
            # Ensure we can find Qt plugins
            qt_plugins_path = os.path.join(meipass, 'PyQt5', 'Qt', 'plugins')
            if os.path.exists(qt_plugins_path):
                os.environ['QT_PLUGIN_PATH'] = qt_plugins_path
            
            # Set glibc compatibility flags
            os.environ['GLIBC_TUNABLES'] = 'glibc.pthread.rseq=0'
            
            # Try to use bundled Python libraries if available
            python_lib_path = os.path.join(meipass, 'libpython3.11.so.1.0')
            if os.path.exists(python_lib_path):
                os.environ['PYTHONHOME'] = meipass

# Run the setup when this module is imported
setup_linux_compatibility()
