"""
Metavinci - Network Daemon for Heavymeta

This application now supports threaded loading windows for better performance.
The loading windows run in background threads to keep the UI responsive during
long-running operations.

Threading Features:
- LoadingWorker: Base class for background operations
- threaded_loading_window(): Creates loading window with background work
- threaded_animated_loading_window(): Creates animated loading window with background work
- Custom workers for specific operations:
  * HvymInstallWorker: For hvym CLI installation
  * PintheonInstallWorker: For Pintheon installation
  * PressInstallWorker: For Press installation

Usage Example:
    # For simple operations
    loading_window, worker = self.threaded_loading_window('Loading...', my_work_function, arg1, arg2)
    
    # For animated operations  
    animated_window, worker = self.threaded_animated_loading_window('Loading...', my_work_function, gif_path, arg1, arg2)
    
    # For custom operations
    worker = HvymInstallWorker(self.HVYM)
    loading_window = LoadingWindow(self, 'Installing...')
    worker.success.connect(lambda msg: self._on_success(loading_window, worker, msg))
    worker.start()
    
    # The windows and workers are automatically cleaned up when work completes
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QWidgetAction, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QComboBox, QDialogButtonBox, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp, QVBoxLayout, QPushButton, QDialog, QDesktopWidget, QFileDialog, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QSize, QTimer, QByteArray, QThread, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QIcon, QPixmap, QImageReader
from pathlib import Path
import subprocess
import os
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
from tinydb import TinyDB, Query
import tinydb_encrypted_jsonstorage as enc_json
import shutil
from biscuit_auth import KeyPair,PrivateKey, PublicKey,BiscuitBuilder,Fact,Authorizer,Biscuit
from cryptography.fernet import Fernet
import json
import re
from datetime import datetime, timedelta, timezone
import time
import threading
import sys
from platform_manager import PlatformManager
from download_utils import download_and_execute_script, download_and_extract_zip
from file_utils import set_secure_permissions, create_secure_directory, ensure_config_directory
from hosts_utils import ensure_hosts_entry
import platform
import urllib.request
import tempfile
import os
import tarfile
import zipfile
import shutil
import requests
import logging
import subprocess
import shlex
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union, Callable
import certifi
import webbrowser
import traceback

# Try to import optional dependencies
try:
    import patoolib
    HAS_PATOOL = True
except ImportError:
    HAS_PATOOL = False

# Constants
EXTRACT_RETRY_ATTEMPTS = 2
EXTRACT_RETRY_DELAY = 1  # seconds

# Import compiled Qt resources if present (built by pyrcc5)
try:
    import resources_rc  # noqa: F401
except Exception:
    resources_rc = None

class LoadingWorker(QThread):
    """
    A QThread-based worker for handling loading operations in the background.
    """
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    success = pyqtSignal(str)  # For success messages
    
    def __init__(self, work_function, *args, **kwargs):
        super().__init__()
        self.work_function = work_function
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        """Execute the work function in the background thread."""
        try:
            if self.args and self.kwargs:
                result = self.work_function(*self.args, **self.kwargs)
            elif self.args:
                result = self.work_function(*self.args)
            elif self.kwargs:
                result = self.work_function(**self.kwargs)
            else:
                result = self.work_function()
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class HvymInstallWorker(LoadingWorker):
    """Custom worker for hvym installation."""
    
    def __init__(self, hvym_path):
        super().__init__(self._install_hvym_worker)
        self.hvym_path = hvym_path
    
    def _install_hvym_worker(self):
        """Worker function for installing hvym in background thread."""
        try:
            bin_dir = os.path.dirname(str(self.hvym_path))
            if not os.path.exists(bin_dir):
                os.makedirs(bin_dir, exist_ok=True)
            hvym_path = download_and_install_hvym_cli(bin_dir)
            print(f"hvym installed at {hvym_path}")
            
            # Emit success signal with message
            self.success.emit(f"hvym installed at {hvym_path}")
            
        except Exception as e:
            print(e)
            # Emit error signal
            self.error.emit(f"Error installing hvym: {e}")


class PintheonInstallWorker(LoadingWorker):
    """Custom worker for Pintheon installation."""
    
    def __init__(self, hvym_path):
        super().__init__(self._install_pintheon_worker)
        self.hvym_path = hvym_path
    
    def _install_pintheon_worker(self):
        """Worker function for installing Pintheon in background thread."""
        try:
            # Prepare environment with certifi-backed CA bundle for hvym's requests
            import certifi
            env = os.environ.copy()
            env["REQUESTS_CA_BUNDLE"] = certifi.where()

            # Align PATH and Docker environment with main app behavior (important for macOS Finder launches)
            if platform.system().lower() == 'darwin':
                default_paths = [
                    '/usr/local/bin',
                    '/opt/homebrew/bin',
                    '/usr/bin', '/bin', '/usr/sbin', '/sbin',
                    '/Applications/Docker.app/Contents/Resources/bin'
                ]
                current_path_parts = env.get('PATH', '').split(':') if env.get('PATH') else []
                for p in default_paths:
                    if p not in current_path_parts:
                        current_path_parts.append(p)
                env['PATH'] = ':'.join(current_path_parts)

                # Locale
                env.setdefault('LC_ALL', 'en_US.UTF-8')
                env.setdefault('LANG', 'en_US.UTF-8')

                # Prefer user's Docker Desktop socket if present
                try:
                    docker_sock_home = Path.home() / '.docker' / 'run' / 'docker.sock'
                    default_sock = Path('/var/run/docker.sock')
                    if 'DOCKER_HOST' not in env and docker_sock_home.exists() and not default_sock.exists():
                        env['DOCKER_HOST'] = f'unix://{docker_sock_home}'
                except Exception:
                    pass

            # Ensure PyInstaller runtime can create its temp directories (fixes PYI-16001/16006)
            try:
                # Use a temp directory without spaces to avoid PyInstaller issues on macOS
                tmp_base = Path.home() / '.metavinci_tmp'
                tmp_base.mkdir(parents=True, exist_ok=True)
                env['TMPDIR'] = str(tmp_base)
                env['TEMP'] = str(tmp_base)
                env['TMP'] = str(tmp_base)
            except Exception:
                pass

            # Always run from user's HOME to keep Docker bind paths stable on macOS
            home_dir = str(Path.home())

            # Run the hvym pintheon setup command (list-form, no shell) to handle spaces in path
            setup_cmd = [str(self.hvym_path), 'pintheon-setup']
            result = subprocess.run(setup_cmd, capture_output=True, text=True, cwd=home_dir, env=env)

            if result.returncode == 0:
                # On macOS, remove quarantine from Pinggy binary if present
                if platform.system().lower() == 'darwin':
                    try:
                        pinggy_path = Path.home() / '.local' / 'share' / 'pinggy' / 'pinggy'
                        if pinggy_path.exists():
                            subprocess.run(['xattr', '-d', 'com.apple.quarantine', str(pinggy_path)],
                                           capture_output=True, check=False)
                    except Exception:
                        pass

                # Update hosts file with local.pintheon.com entry
                self.progress.emit("Updating hosts file...")
                if not ensure_hosts_entry('local.pintheon.com'):
                    logging.warning("Failed to update hosts file. You may need to add '127.0.0.1 local.pintheon.com' manually.")
                    self.progress.emit("Warning: Could not update hosts file. Some features may not work.")
                else:
                    logging.info("Successfully updated hosts file with local.pintheon.com entry")
                    self.progress.emit("Hosts file updated successfully")

                # Verify Pintheon image exists
                check_cmd = [str(self.hvym_path), 'pintheon-image-exists']
                check_result = subprocess.run(check_cmd, capture_output=True, text=True, cwd=home_dir, env=env)

                if check_result.returncode == 0 and check_result.stdout.strip() == 'True':
                    self.success.emit("Pintheon installed successfully")
                else:
                    detail = check_result.stderr.strip() or check_result.stdout.strip()
                    self.error.emit(f"Pintheon installation completed but verification failed: {detail}")
            else:
                detail = result.stderr.strip() or result.stdout.strip()
                self.error.emit(f"Pintheon installation failed: {detail}")
            
        except Exception as e:
            print(e)
            # Emit error signal
            self.error.emit(f"Error installing Pintheon: {e}")


class PressInstallWorker(LoadingWorker):
    """Custom worker for Press installation using direct executable downloads."""
    
    def __init__(self, platform_manager):
        super().__init__(self._install_press_worker)
        self.platform_manager = platform_manager
    
    def _install_press_worker(self):
        """Worker function for installing Press in background thread."""
        try:
            # Check if hvym_press is supported on current architecture
            if not self.platform_manager.is_hvym_press_supported():
                raise Exception("hvym_press is not supported on this architecture")
            
            # Get the press path and bin directory
            press_path = self.platform_manager.get_press_path()
            bin_dir = press_path.parent
            
            # Ensure bin directory exists
            if not bin_dir.exists():
                bin_dir.mkdir(parents=True, exist_ok=True)
            
            # Use the direct download and installation method
            installed_path = download_and_install_hvym_press_cli(str(bin_dir))
            
            if installed_path:
                self.success.emit("Press installed successfully")
            else:
                self.error.emit("Press installation failed")
            
        except Exception as e:
            print(e)
            # Emit error signal
            self.error.emit(f"Error installing Press: {e}")


class HvymPressInstallWorker(LoadingWorker):
    """Custom worker for hvym_press installation using direct downloads."""
    
    def __init__(self, press_path):
        super().__init__(self._install_hvym_press_worker)
        self.press_path = press_path
    
    def _install_hvym_press_worker(self):
        """Worker function for installing hvym_press in background thread."""
        try:
            # Check if hvym_press is supported on current architecture
            platform_manager = PlatformManager()
            if not platform_manager.is_hvym_press_supported():
                raise Exception("hvym_press is not supported on this architecture")
            
            bin_dir = os.path.dirname(str(self.press_path))
            if not os.path.exists(bin_dir):
                os.makedirs(bin_dir, exist_ok=True)
            
            press_path = download_and_install_hvym_press_cli(bin_dir)
            print(f"hvym_press installed at {press_path}")
            
            # Emit success signal with message
            self.success.emit(f"hvym_press installed at {press_path}")
            
        except Exception as e:
            print(e)
            # Emit error signal
            self.error.emit(f"Error installing hvym_press: {e}")


class WindowThread(QThread):
    result_ready = pyqtSignal(int)

    def __init__(self):
        super().__init__()


class LoadingWindow(QWidget):
    """
    A non-blocking loading indicator window without title bar.
    """
    def __init__(self, parent, prompt):
        super().__init__(parent)
        # Use window flags for a top-level window that stays on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setFixedSize(400, 150)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create and configure label
        self.label = QLabel(prompt)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Center the window
        self.center_window()
        
        # Ensure window is visible and on top
        self.raise_()
        self.activateWindow()
        
    def center_window(self):
        """Center the window on screen using the same method as the main window."""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())





class AnimatedLoadingWindow(QSplashScreen):
    """
    A non-blocking animated loading indicator window with GIF animation.
    Uses QSplashScreen for better cross-platform compatibility and performance.
    """
    def __init__(self, parent, prompt, gif_path):
        # Initialize with a default pixmap (will be updated by the movie)
        super().__init__(QPixmap(1, 1))
        
        # Store prompt for later use
        self._prompt = prompt
        self._gif_path = gif_path
        
        # Set window flags for a top-level window that stays on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Set up the movie
        self._setup_movie()
        
        # Show the initial message
        self.update_text(prompt)
        
        # Ensure window is visible and on top
        self.raise_()
        self.activateWindow()
    
    def _setup_movie(self):
        """Set up the movie with error handling and proper sizing."""
        try:
            self.movie = QMovie(self._gif_path)
            if not self.movie.isValid():
                raise Exception(f"Invalid GIF file: {self._gif_path}")
                
            # Connect the frame changed signal
            self.movie.frameChanged.connect(self._update_pixmap)
            
            # Start the animation
            self.movie.start()
            
            # Set initial size based on the first frame
            first_frame = self.movie.currentPixmap()
            if not first_frame.isNull():
                self.setFixedSize(first_frame.size())
            
            # Center on screen
            self._center_on_screen()
            
        except Exception as e:
            print(f"Error loading animation: {e}")
            # Fallback to a simple message if GIF loading fails
            self.showMessage(
                self._prompt,
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.white
            )
            self.setFixedSize(300, 200)
    
    def _update_pixmap(self, frame_number=None):
        """Update the splash screen with the current frame."""
        try:
            if hasattr(self, 'movie') and self.movie.state() == QMovie.Running:
                current_pixmap = self.movie.currentPixmap()
                if not current_pixmap.isNull():
                    # Set the pixmap and mask for transparency
                    self.setPixmap(current_pixmap)
                    self.setMask(current_pixmap.mask())
        except Exception as e:
            print(f"Error updating pixmap: {e}")
    
    def _center_on_screen(self):
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def update_text(self, text):
        """Update the loading text."""
        self.showMessage(text, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    # Backward compatibility methods
    def start_animation(self):
        """Start the animation (for backward compatibility)."""
        if hasattr(self, 'movie'):
            self.movie.start()
    
    def stop_animation(self):
        """Stop the animation (for backward compatibility)."""
        if hasattr(self, 'movie'):
            self.movie.stop()
        self.close()
    
    def set_animation_speed(self, speed_percent):
        """Set animation speed (for backward compatibility)."""
        if hasattr(self, 'movie'):
            self.movie.setSpeed(speed_percent)
        
    # Deprecated methods (kept for backward compatibility)
    def size_window_to_gif(self):
        """Deprecated: Window sizing is now handled automatically."""
        pass
        
    def _on_movie_frame_changed(self, frame_index: int):
        """Deprecated: Frame handling is now done in _update_pixmap."""
        pass
        
    def center_window(self):
        """Deprecated: Use _center_on_screen instead."""
        self._center_on_screen()
    
    def ensure_animation_running(self):
        """Deprecated: Not needed with QSplashScreen."""
        pass


def get_latest_hvym_release_asset_url():
    api_url = "https://api.github.com/repos/inviti8/heavymeta-cli-dev/releases/latest"
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    assets = {asset['name']: asset['browser_download_url'] for asset in data['assets']}
    system = platform.system().lower()
    if system == "linux":
        asset_name = "hvym-linux.tar.gz"
    elif system == "darwin":
        # Architecture-aware macOS asset selection
        machine = (platform.machine() or '').lower()
        arch_suffix = 'arm64' if 'arm' in machine or 'aarch64' in machine else 'amd64'
        preferred = f"hvym-macos-{arch_suffix}.tar.gz"
        # Try preferred first; fall back to legacy name if needed
        if preferred in assets:
            asset_name = preferred
        else:
            asset_name = "hvym-macos.tar.gz"
    elif system == "windows":
        asset_name = "hvym-windows.zip"
    else:
        raise Exception("Unsupported platform")
    url = assets.get(asset_name)
    if not url:
        raise Exception(f"Asset {asset_name} not found in latest release")
    return url

def _extract_with_tar(archive_path: str, extract_dir: str) -> bool:
    """Extract .tar.gz file using Python's tarfile module."""
    logging.info(f"Attempting Python tarfile extraction of {archive_path} to {extract_dir}")
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            logging.info(f"Archive members: {len(tar.getmembers())} files")
            # Log first few files for debugging
            for i, member in enumerate(tar.getmembers()[:5]):
                logging.info(f"  - {member.name} ({member.size} bytes)")
            if len(tar.getmembers()) > 5:
                logging.info(f"  ... and {len(tar.getmembers()) - 5} more files")
                
            tar.extractall(path=extract_dir)
            
        # Verify extraction
        extracted = list(Path(extract_dir).rglob('*'))
        logging.info(f"Extracted {len(extracted)} files to {extract_dir}")
        if extracted:
            for f in extracted[:5]:  # Log first 5 extracted files
                logging.info(f"  - {f} ({f.stat().st_size} bytes)")
            if len(extracted) > 5:
                logging.info(f"  ... and {len(extracted) - 5} more files")
        
        return True
    except (tarfile.TarError, EOFError, OSError) as e:
        logging.error(f"tarfile extraction failed: {str(e)}", exc_info=True)
        return False

def _extract_with_zip(archive_path: str, extract_dir: str) -> bool:
    """Extract .zip file using Python's zipfile module."""
    logging.info(f"Attempting Python zipfile extraction of {archive_path} to {extract_dir}")
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            logging.info(f"Archive contains {len(file_list)} files")
            for i, name in enumerate(file_list[:5]):  # Log first 5 files
                info = zip_ref.getinfo(name)
                logging.info(f"  - {name} ({info.file_size} bytes, compressed: {info.compress_size} bytes)")
            if len(file_list) > 5:
                logging.info(f"  ... and {len(file_list) - 5} more files")
                
            zip_ref.extractall(extract_dir)
            
        # Verify extraction
        extracted = list(Path(extract_dir).rglob('*'))
        logging.info(f"Extracted {len(extracted)} files to {extract_dir}")
        if extracted:
            for f in extracted[:5]:  # Log first 5 extracted files
                try:
                    logging.info(f"  - {f} ({f.stat().st_size} bytes)")
                except Exception as e:
                    logging.error(f"  - {f} (error getting size: {e})")
            if len(extracted) > 5:
                logging.info(f"  ... and {len(extracted) - 5} more files")
                
        return True
    except (zipfile.BadZipFile, OSError) as e:
        logging.error(f"zipfile extraction failed: {str(e)}", exc_info=True)
        return False

def _extract_with_system_tar(archive_path: str, extract_dir: str) -> bool:
    """Extract .tar.gz using system tar command."""
    logging.info(f"Attempting system tar extraction of {archive_path} to {extract_dir}")
    try:
        # First check if tar is available
        tar_check = subprocess.run(['which', 'tar'], capture_output=True, text=True)
        if tar_check.returncode != 0:
            logging.warning("System tar command not found")
            return False
            
        # Get archive listing first
        list_cmd = ['tar', 'tzf', archive_path]
        list_result = subprocess.run(list_cmd, capture_output=True, text=True)
        
        if list_result.returncode == 0:
            files = list_result.stdout.splitlines()
            logging.info(f"Archive contains {len(files)} files")
            for f in files[:5]:  # Log first 5 files
                logging.info(f"  - {f}")
            if len(files) > 5:
                logging.info(f"  ... and {len(files) - 5} more files")
        
        # Perform the actual extraction
        cmd = ['tar', 'xzvf', archive_path, '-C', extract_dir]
        logging.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"System tar extraction successful. Output:\n{result.stdout}")
            return True
            
        logging.error(f"System tar command failed with code {result.returncode}")
        logging.error(f"STDERR: {result.stderr}")
        logging.error(f"STDOUT: {result.stdout}")
        return False
        
    except Exception as e:
        logging.error(f"System tar command execution failed: {str(e)}", exc_info=True)
        return False

def _extract_with_system_unzip(archive_path: str, extract_dir: str) -> bool:
    """Extract .zip using system unzip command."""
    try:
        cmd = ['unzip', '-o', archive_path, '-d', extract_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        logging.warning(f"System unzip command failed: {result.stderr}")
        return False
    except Exception as e:
        logging.warning(f"System unzip command execution failed: {e}")
        return False

def _extract_with_patool(archive_path: str, extract_dir: str) -> bool:
    """Extract archive using patoolib if available."""
    if not HAS_PATOOL:
        return False
    try:
        patoolib.extract_archive(archive_path, outdir=extract_dir)
        return True
    except Exception as e:
        logging.warning(f"patoolib extraction failed: {e}")
        return False

def extract_archive(archive_path: str, extract_dir: str) -> bool:
    """
    Extract an archive using multiple methods with fallbacks.
    
    Args:
        archive_path: Path to the archive file
        extract_dir: Directory to extract files to
        
    Returns:
        bool: True if extraction succeeded, False otherwise
    """
    # Log start of extraction
    logging.info(f"=== Starting archive extraction ===")
    logging.info(f"Archive: {archive_path}")
    logging.info(f"Extract to: {extract_dir}")
    logging.info(f"File exists: {os.path.exists(archive_path)}")
    
    if not os.path.exists(archive_path):
        logging.error(f"Archive not found: {archive_path}")
        return False
    
    try:
        file_size = os.path.getsize(archive_path)
        logging.info(f"File size: {file_size} bytes")
        if file_size == 0:
            logging.error(f"Archive is empty: {archive_path}")
            return False
    except Exception as e:
        logging.error(f"Failed to get file size: {e}")
        return False
    
    # Create extract directory if it doesn't exist
    try:
        os.makedirs(extract_dir, exist_ok=True)
        logging.info(f"Created extract directory: {extract_dir}")
    except Exception as e:
        logging.error(f"Failed to create extract directory {extract_dir}: {e}")
        return False
    
    # Check if we can write to the extract directory
    test_file = os.path.join(extract_dir, '.write_test')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        logging.error(f"Cannot write to extract directory {extract_dir}: {e}")
        return False
    
    # Try different extraction methods based on file extension
    if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        logging.info("Detected .tar.gz archive")
        methods = [
            ('Python tarfile', _extract_with_tar),
            ('System tar', _extract_with_system_tar),
            ('patoolib', _extract_with_patool) if HAS_PATOOL else None
        ]
    elif archive_path.endswith('.zip'):
        logging.info("Detected .zip archive")
        methods = [
            ('Python zipfile', _extract_with_zip),
            ('System unzip', _extract_with_system_unzip),
            ('patoolib', _extract_with_patool) if HAS_PATOOL else None
        ]
    else:
        logging.error(f"Unsupported archive format: {archive_path}")
        return False
    
    # Filter out None values (unavailable methods)
    methods = [m for m in methods if m is not None]
    logging.info(f"Available extraction methods: {[m[0] for m in methods]}")
    
    # Try each method with retries
    for attempt in range(EXTRACT_RETRY_ATTEMPTS):
        if attempt > 0:
            logging.warning(f"Retry {attempt + 1}/{EXTRACT_RETRY_ATTEMPTS} for {archive_path}")
            time.sleep(EXTRACT_RETRY_DELAY)
        
        for name, method in methods:
            logging.info(f"\n=== Trying extraction with {name} (attempt {attempt + 1}/{EXTRACT_RETRY_ATTEMPTS}) ===")
            try:
                success = method(archive_path, extract_dir)
                if success:
                    # Verify extraction
                    extracted_files = list(Path(extract_dir).rglob('*'))
                    logging.info(f"Extraction successful. Found {len(extracted_files)} files in {extract_dir}")
                    if extracted_files:
                        for f in extracted_files[:5]:
                            try:
                                logging.info(f"  - {f} ({f.stat().st_size} bytes)")
                            except:
                                logging.info(f"  - {f} (error getting size)")
                        if len(extracted_files) > 5:
                            logging.info(f"  ... and {len(extracted_files) - 5} more files")
                    return True
                logging.warning(f"Extraction with {name} returned False")
            except Exception as e:
                logging.error(f"Extraction with {name} failed with exception: {str(e)}", exc_info=True)
    
    # If we get here, all methods failed
    logging.error(f"=== All extraction methods failed for {archive_path} ===")
    
    # Log directory contents for debugging
    try:
        logging.info("\n=== Directory Contents ===")
        for root, dirs, files in os.walk(extract_dir):
            level = root.replace(extract_dir, '').count(os.sep)
            indent = '  ' * level
            logging.info(f"{indent}{os.path.basename(root)}/")
            subindent = '  ' * (level + 1)
            for f in files[:10]:  # Limit to first 10 files per directory
                try:
                    size = os.path.getsize(os.path.join(root, f))
                    logging.info(f"{subindent}{f} ({size} bytes)")
                except:
                    logging.info(f"{subindent}{f} (error getting size)")
            if len(files) > 10:
                logging.info(f"{subindent}... and {len(files) - 10} more files")
    except Exception as e:
        logging.error(f"Failed to list directory contents: {e}")
    
    return False

def download_and_install_hvym_cli(dest_dir: str) -> str:
    """
    Download and install the latest hvym CLI for the current platform.
    
    Args:
        dest_dir: Directory where the hvym binary should be installed
        
    Returns:
        str: Path to the installed hvym binary
        
    Raises:
        Exception: If download, extraction, or installation fails
    """
    logger = logging.getLogger()
    logger.info("=" * 80)
    logger.info("Starting hvym CLI installation")
    logger.info(f"Destination directory: {dest_dir}")
    
    # Ensure the destination directory and its parent exist with correct permissions
    try:
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(dest_dir)
        logger.info(f"Ensuring parent directory exists: {parent_dir}")
        os.makedirs(parent_dir, mode=0o755, exist_ok=True)
        
        # Create the destination directory with proper permissions
        logger.info(f"Ensuring destination directory exists: {dest_dir}")
        os.makedirs(dest_dir, mode=0o755, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(dest_dir, '.write_test')
        logger.info(f"Testing write permissions with file: {test_file}")
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("Write permissions verified")
        except Exception as e:
            error_msg = f"Cannot write to destination directory {dest_dir}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"Cannot create or write to destination directory {dest_dir}: {e}"
        logger.error(error_msg)
        
        # Try to create with sudo if permission denied on Linux
        if "Permission denied" in str(e) and platform.system().lower() == "linux":
            logger.warning("Permission denied, trying with sudo...")
            try:
                # Create parent directory with sudo if needed
                if not os.path.exists(parent_dir):
                    logger.info(f"Creating parent directory with sudo: {parent_dir}")
                    subprocess.run(
                        ['sudo', 'mkdir', '-p', parent_dir],
                        check=True
                    )
                
                # Set ownership and permissions
                logger.info(f"Setting ownership and permissions for {parent_dir}")
                uid = os.getuid()
                gid = os.getgid()
                subprocess.run(
                    ['sudo', 'chown', f"{uid}:{gid}", parent_dir],
                    check=True
                )
                subprocess.run(
                    ['sudo', 'chmod', '755', parent_dir],
                    check=True
                )
                
                # Create destination directory
                os.makedirs(dest_dir, mode=0o755, exist_ok=True)
                logger.info("Successfully created directory with elevated permissions")
                
            except Exception as sudo_e:
                error_msg = f"Failed to create directory even with sudo: {sudo_e}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            raise Exception(error_msg)

    # Use macOS-specific installation helper if on macOS
    if platform.system().lower() == "darwin":
        try:
            logger.info("macOS detected, attempting to use macOS installation helper")
            from macos_install_helper import MacOSInstallHelper
            helper = MacOSInstallHelper()
            hvym_path = helper.install_hvym_cli()
            if hvym_path:
                logger.info(f"Successfully installed hvym using macOS helper: {hvym_path}")
                return hvym_path
            else:
                logger.warning("macOS installation helper returned no path, falling back to standard method")
                raise Exception("macOS installation helper failed")
        except ImportError as e:
            logger.warning("macOS installation helper not available, falling back to standard method")
            logger.debug(f"Import error: {e}")
        except Exception as e:
            logger.warning(f"macOS installation helper error: {e}, falling back to standard method")
            logger.debug(f"Error details: {traceback.format_exc()}")
    
    # Standard installation method for other platforms
    logger.info("Using standard installation method")
    
    try:
        # Get the download URL
        logger.info("Getting latest release URL")
        url = get_latest_hvym_release_asset_url()
        logger.info(f"Latest release URL: {url}")
        
        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Using temporary directory: {tmpdir}")
            
            # Download the file
            asset = os.path.basename(url)
            archive_path = os.path.join(tmpdir, asset)
            logger.info(f"Downloading {url} to {archive_path}")
            
            try:
                # Use requests + certifi for robust SSL verification
                with requests.get(
                    url, 
                    stream=True, 
                    timeout=30, 
                    verify=certifi.where(), 
                    headers={"User-Agent": "Metavinci/1.0"}
                ) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    logger.info(f"Download size: {total_size} bytes")
                    
                    with open(archive_path, 'wb') as f:
                        downloaded = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = (downloaded / total_size) * 100
                                    if percent % 10 == 0:  # Log every 10% to avoid flooding logs
                                        logger.debug(f"Download progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
                    
                    logger.info(f"Download completed: {os.path.getsize(archive_path)} bytes")
                
                # Verify download
                if not os.path.exists(archive_path) or os.path.getsize(archive_path) == 0:
                    raise Exception("Downloaded file is empty or missing")
                
                # Extract the archive
                logger.info(f"Extracting archive: {archive_path}")
                if not extract_archive(archive_path, tmpdir):
                    raise Exception("Failed to extract archive")
                
                # Find the binary in the extracted files (flexible matching for architecture-specific names)
                logger.info("Looking for binary in extracted files...")
                system = platform.system().lower()
                
                found_binary = None
                for root, _, files in os.walk(tmpdir):
                    for file in files:
                        # Skip archive files themselves
                        if file.endswith('.tar.gz') or file.endswith('.zip'):
                            continue
                        # Match any file starting with 'hvym' (handles hvym, hvym-macos, hvym-macos-arm64, etc.)
                        if file.startswith('hvym') and not file.endswith('.exe.config'):
                            file_path = os.path.join(root, file)
                            # Verify it's a file and not a directory
                            if os.path.isfile(file_path):
                                found_binary = file_path
                                logger.info(f"Found binary: {file} at {file_path}")
                                break
                    if found_binary:
                        break
                
                if not found_binary:
                    raise Exception(f"Could not find hvym binary in the downloaded archive")
                
                # Set executable permissions
                os.chmod(found_binary, 0o755)
                
                # Create destination directory if it doesn't exist
                os.makedirs(dest_dir, exist_ok=True, mode=0o755)
                
                # Move binary to destination (keep the original filename)
                binary_filename = os.path.basename(found_binary)
                dest_path = os.path.join(dest_dir, binary_filename)
                shutil.move(found_binary, dest_path)
                logger.info(f"Moved binary to: {dest_path}")
                
                # Remove macOS quarantine attribute if present
                if system == 'darwin':
                    try:
                        subprocess.run(['xattr', '-d', 'com.apple.quarantine', dest_path],
                                     capture_output=True, check=False)
                        logger.info("Removed macOS quarantine attribute")
                    except Exception as e:
                        logger.debug(f"Could not remove quarantine attribute: {e}")
                
                # Verify the binary works
                try:
                    result = subprocess.run(
                        [dest_path, 'version'],
                        capture_output=True,
                        text=True,
                        timeout=20
                    )
                    logger.info(f"Binary version check: {result.stdout.strip()}")
                    return dest_path
                except Exception as e:
                    logger.error(f"Binary test failed: {e}")
                    raise Exception(f"Downloaded binary is not working: {e}")
                
                # If we get here, no binary was found
                # Prepare error message with system information
                system_info = (
                    f"System: {platform.system()} {platform.release()} {platform.machine()}\n"
                    f"Python: {platform.python_version()}\n"
                    f"Archive: {os.path.basename(archive_path)} ({os.path.getsize(archive_path) if os.path.exists(archive_path) else 0} bytes)"
                )
                
                raise Exception(
                    f"Could not find {binary_name} in the downloaded archive.\n\n"
                    f"{system_info}\n\n"
                    "Please check if the downloaded archive is valid and contains the expected files."
                )
                
            except Exception as e:
                # Log the detailed error
                logger.error(f"Download or extraction failed: {e}")
                logger.debug(f"Error details: {traceback.format_exc()}")
                
                # Prepare system information for the error message
                system_info = (
                    f"System: {platform.system()} {platform.release()} {platform.machine()}\n"
                    f"Python: {platform.python_version()}"
                )
                
                if os.path.exists(archive_path):
                    system_info += f"\nArchive: {os.path.basename(archive_path)} ({os.path.getsize(archive_path)} bytes)"
                
                raise Exception(
                    f"Installation failed: {str(e)}\n\n"
                    f"{system_info}\n\n"
                    "Please check your internet connection and try again. "
                    "If the problem persists, please contact support with the above information."
                )
                
    except Exception as e:
        # This is a fallback for any other unhandled exceptions
        logger.error(f"Unexpected installation error: {e}")
        logger.debug(f"Error details: {traceback.format_exc()}")
        
        system_info = (
            f"System: {platform.system()} {platform.release()} {platform.machine()}\n"
            f"Python: {platform.python_version()}"
        )
        
        raise Exception(
            f"Unexpected error during installation: {str(e)}\n\n"
            f"{system_info}\n\n"
            "This could be due to:\n"
            "1. Corrupted download (try again)\n"
            "2. Missing extraction tools (install 'unzip' or 'tar')\n"
            "3. Permission issues (check write access to temp directory)\n\n"
            "Please try again or contact support if the problem persists."
        )


def get_latest_hvym_press_release_asset_url():
    """Get the latest hvym_press release asset URL for the current platform."""
    api_url = "https://api.github.com/repos/inviti8/hvym_press/releases/latest"
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    assets = {asset['name']: asset['browser_download_url'] for asset in data['assets']}
    system = platform.system().lower()
    if system == "linux":
        asset_name = "hvym_press-linux"
    elif system == "darwin":
        # Architecture-aware macOS asset selection
        machine = (platform.machine() or '').lower()
        arch_suffix = 'arm64' if 'arm' in machine or 'aarch64' in machine else 'amd64'
        # Note: hvym_press is not supported on Apple Silicon
        if arch_suffix == 'arm64':
            raise Exception("hvym_press is not supported on macOS Apple Silicon (ARM64)")
        asset_name = "hvym_press-macos"
    elif system == "windows":
        asset_name = "hvym_press-windows.exe"
    else:
        raise Exception("Unsupported platform")
    url = assets.get(asset_name)
    if not url:
        raise Exception(f"Asset {asset_name} not found in latest release")
    return url


def download_and_install_hvym_press_cli(dest_dir):
    """Download and install the latest hvym_press CLI for the current platform."""
    # Check if hvym_press is supported on current architecture
    platform_manager = PlatformManager()
    if not platform_manager.is_hvym_press_supported():
        raise Exception("hvym_press is not supported on this architecture")
    
    # Use macOS-specific installation helper if on macOS
    if platform.system().lower() == "darwin":
        try:
            from macos_install_helper import MacOSInstallHelper
            helper = MacOSInstallHelper()
            press_path = helper.install_hvym_press_cli()
            if press_path:
                return press_path
            else:
                raise Exception("macOS installation helper failed")
        except ImportError:
            print("macOS installation helper not available, falling back to standard method")
        except Exception as e:
            print(f"macOS installation helper error: {e}, falling back to standard method")
    
    # Standard installation method for other platforms
    url = get_latest_hvym_press_release_asset_url()
    print(f"Downloading {url} ...")
    
    # Get the expected executable name for the current platform
    system = platform.system().lower()
    if system == "linux":
        executable_name = "hvym_press-linux"
    elif system == "darwin":
        executable_name = "hvym_press-macos"
    elif system == "windows":
        executable_name = "hvym_press-windows.exe"
    else:
        raise Exception("Unsupported platform")
    
    # Download the executable directly
    with tempfile.TemporaryDirectory() as tmpdir:
        executable_path = os.path.join(tmpdir, executable_name)
        
        # Use requests + certifi for robust SSL verification
        import certifi
        import requests
        with requests.get(url, stream=True, timeout=30, verify=certifi.where(), headers={"User-Agent": "Metavinci/1.0"}) as r:
            r.raise_for_status()
            with open(executable_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        # Move the executable to the destination directory
        dst_path = os.path.join(dest_dir, executable_name)
        shutil.move(executable_path, dst_path)
        
        # Set executable permissions for Unix systems
        if platform.system().lower() != "windows":
            os.chmod(dst_path, 0o755)
        
        print(f"hvym_press installed at {dst_path}")
        return dst_path


class Metavinci(QMainWindow):
    """
        Network Daemon for Heavymeta
    """
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
        self.setWindowFlag(Qt.FramelessWindowHint)
                # Initialize platform manager
        self.platform_manager = PlatformManager()
        # Ensure Qt plugin paths include imageformats so QMovie can load GIFs on macOS/Linux
        try:
            import PyQt5, os as _os
            plugin_base = _os.path.join(_os.path.dirname(PyQt5.__file__), 'Qt', 'plugins')
            img_plugins = _os.path.join(plugin_base, 'imageformats')
            for _p in (plugin_base, img_plugins):
                if _p and _p not in QCoreApplication.libraryPaths():
                    QCoreApplication.addLibraryPath(_p)
        except Exception:
            pass
        # Set up basic paths first
        self.HOME = os.path.expanduser('~')
        self.PATH = self.platform_manager.get_config_path()
        
        # Build a stable subprocess environment, especially for macOS (Finder launches have a minimal PATH)
        self.proc_env = self._build_subprocess_env()
        
        # Initialize file logging after paths are set
        self._init_logging()
        self.BIN_PATH = self.platform_manager.get_bin_path()
        self.KEYSTORE = self.PATH / 'keystore.enc'
        self.ENC_KEY = self.PATH / 'encryption_key.key'
        self.DFX = self.platform_manager.get_dfx_path()
        self.HVYM = self.platform_manager.get_hvym_path()
        
        # Log the initial HVYM path
        if hasattr(self, '_log_hvym_path'):
            self._log_hvym_path()
            
        self.DIDC = self.platform_manager.get_didc_path()
        self.PRESS = self.platform_manager.get_press_path()
        self.BLENDER_PATH = self.platform_manager.get_blender_path()
        
        # Backward compatibility: if on macOS and arch-specific hvym not present, fall back to legacy filename
        try:
            if platform.system().lower() == 'darwin' and not self.HVYM.is_file():
                legacy_hvym = self.BIN_PATH / 'hvym-macos'
                if legacy_hvym.is_file():
                    self.HVYM = legacy_hvym
                    # Log again if we changed the HVYM path
                    if hasattr(self, '_log_hvym_path'):
                        self._log_hvym_path()
        except Exception as e:
            self.logger.warning(f"Error during macOS compatibility check: {e}")
        self.BLENDER_VERSIONS = []
        self.BLENDER_VERSION = None
        self.ADDON_INSTALL_PATH = self.BLENDER_PATH / str(self.BLENDER_VERSION) / 'scripts' / 'addons'
        self.ADDON_PATH = self.ADDON_INSTALL_PATH / 'heavymeta_standard'
        self.FILE_PATH = Path(__file__).parent
        self.HVYM_IMG = os.path.join(self.FILE_PATH, 'images', 'metavinci.png')
        self.LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'hvym_logo_64.png')
        self.PINTHEON_IMG = os.path.join(self.FILE_PATH, 'images', 'pintheon_logo.png')
        
        # Show splash screen during initialization (main thread only)
        splash = None
        if QThread.currentThread() == QApplication.instance().thread():
            splash = self.splash_window()
        self.LOGO_IMG_ACTIVE = os.path.join(self.FILE_PATH, 'images', 'hvym_logo_64_active.png')
        # Always use filesystem path for loading gif to ensure consistency in both dev and built environments
        self.LOADING_GIF = os.path.join(self.FILE_PATH, 'images', 'loading.gif')
        self.UPDATE_IMG = os.path.join(self.FILE_PATH, 'images', 'update.png')
        self.INSTALL_IMG = os.path.join(self.FILE_PATH, 'images', 'install.png')
        self.ICP_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_logo.png')
        self.STELLAR_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'stellar_logo.png')
        self.ADD_IMG = os.path.join(self.FILE_PATH, 'images', 'add.png')
        self.REMOVE_IMG = os.path.join(self.FILE_PATH, 'images', 'remove.png')
        self.TEST_IMG = os.path.join(self.FILE_PATH, 'images', 'test.png')
        self.SELECT_IMG = os.path.join(self.FILE_PATH, 'images', 'select.png')
        self.REMOVE_IMG = os.path.join(self.FILE_PATH, 'images', 'remove.png')
        self.OFF_IMG = os.path.join(self.FILE_PATH, 'images', 'switch_off.png')
        self.ON_IMG = os.path.join(self.FILE_PATH, 'images', 'switch_on.png')
        self.COG_IMG = os.path.join(self.FILE_PATH, 'images', 'cog.png')
        self.WEB_IMG = os.path.join(self.FILE_PATH, 'images', 'web.png')
        self.STYLE_SHEET = os.path.join(self.FILE_PATH, 'data', 'style.qss')
        self.DB_SRC = os.path.join(self.FILE_PATH, 'data', 'db.json')
        self.DB_PATH = self.BIN_PATH /'db.json'
        if not self.DB_PATH.exists():
            # Ensure the bin directory exists
            ensure_config_directory(self.BIN_PATH)
            shutil.copyfile(self.DB_SRC, str(self.DB_PATH))
        self.DB = TinyDB(str(self.DB_PATH))
        self.QUERY = Query()
        # self.user_pid = str(_run('dfx identity get-principal')).strip()
        self.user_pid = 'disabled'
        self.DB.update({'INITIALIZED': True, 'principal': self.user_pid}, self.QUERY.type == 'app_data')
        self.INITIALIZED = (len(self.DB.search(self.QUERY.INITIALIZED == True)) > 0)
        self.INSTALL_STATS = None
        self.DOCKER_INSTALLED = False
        self.PINTHEON_INSTALLED = False
        self.TUNNEL_TOKEN = ''

        # Only check Docker and Pintheon status if hvym is installed
        if self.HVYM.is_file():
            self.INSTALL_STATS = self.hvym_install_stats()
            self.DOCKER_INSTALLED = self.INSTALL_STATS['docker_installed']
            self.PINTHEON_INSTALLED = self.INSTALL_STATS['pintheon_image_exists']
            self.TUNNEL_TOKEN = self.INSTALL_STATS['pinggy_token']
        else:
            self.DOCKER_INSTALLED = False
            self.PINTHEON_INSTALLED = False
            self.TUNNEL_TOKEN = ''

        self.PINTHEON_NETWORK = 'testnet'
        self.PINTHEON_ACTIVE = False
        self.win_icon = QIcon(self.HVYM_IMG)
        self.icon = QIcon(self.LOGO_IMG)
        self.pintheon_icon = QIcon(self.PINTHEON_IMG)
        self.update_icon = QIcon(self.UPDATE_IMG)
        self.install_icon = QIcon(self.INSTALL_IMG)
        self.ic_icon = QIcon(self.ICP_LOGO_IMG)
        self.stellar_icon = QIcon(self.STELLAR_LOGO_IMG)
        self.add_icon = QIcon(self.ADD_IMG)
        self.remove_icon = QIcon(self.REMOVE_IMG)
        self.test_icon = QIcon(self.TEST_IMG)
        self.select_icon = QIcon(self.SELECT_IMG)
        self.press_icon = QIcon(self.OFF_IMG)
        self.pintheon_icon = QIcon(self.OFF_IMG)
        self.tunnel_icon = QIcon(self.OFF_IMG)
        self.tunnel_token_icon = QIcon(self.SELECT_IMG)
        self.cog_icon = QIcon(self.COG_IMG)
        self.web_icon = QIcon(self.WEB_IMG)
        self.publik_key = None
        self.private_key = None
        self.refresh_interval = 8 * 60 * 60  # 8 hours in seconds

        self.setMinimumSize(QSize(64, 64))             # Set sizes
        self.setWindowTitle("Metavinci")  # Set a title
        self.central_widget = QWidget(self) 
        self.central_widget.setWindowIcon(self.win_icon)                # Create a central widget
        self.setCentralWidget(self.central_widget)           # Set the central widget
        self.setWindowIcon(self.win_icon)          # Set the icon
        # label = QLabel("", self)
        # label.setPixmap(QPixmap(self.LOGO_IMG))
        # label.adjustSize() 

        if self.BLENDER_PATH.exists():
            for file in os.listdir(str(self.BLENDER_PATH)):
                d = os.path.join(str(self.BLENDER_PATH), file)
                if os.path.isdir(d):
                    self.BLENDER_VERSIONS.append(file)

        idx=0
        for ver in self.BLENDER_VERSIONS:
            if self.BLENDER_VERSION == None:
                self.BLENDER_VERSION = ver
            if idx > 0:
                if float(ver) > float(self.BLENDER_VERSIONS[idx-1]):
                    self.BLENDER_VERSION = ver
                    self.ADDON_INSTALL_PATH = self.BLENDER_PATH / str(self.BLENDER_VERSION) / 'scripts' / 'addons'
                    self.ADDON_PATH = self.ADDON_INSTALL_PATH / 'heavymeta_standard'
            idx += 1
     
        # Add a checkbox, which will depend on the behavior of the program when the window is closed
        #self.check_box = QCheckBox('Minimize to Tray')
        #grid_layout.addWidget(self.check_box, 1, 0)
        #grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0)
    
        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
     
        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''

        stellar_new_account_action = QAction(self.add_icon, "New Account", self)
        stellar_new_account_action.triggered.connect(self.new_stellar_account)

        stellar_change_account_action = QAction(self.select_icon, "Change Account", self)
        stellar_change_account_action.triggered.connect(self.change_stellar_account)

        stellar_remove_account_action = QAction(self.remove_icon, "Remove Account", self)
        stellar_remove_account_action.triggered.connect(self.remove_stellar_account)

        stellar_testnet_account_action = QAction(self.add_icon, "Testnet Account", self)
        stellar_testnet_account_action.triggered.connect(self.new_stellar_testnet_account)

        self.install_hvym_action = QAction(self.install_icon, "Install hvym", self)
        self.install_hvym_action.triggered.connect(self._install_hvym)

        self.update_hvym_action = QAction(self.update_icon, "Update hvym", self)
        self.update_hvym_action.triggered.connect(self._update_hvym)

        self.open_tunnel_action = QAction(self.tunnel_icon, "Open Tunnel", self)
        self.open_tunnel_action.triggered.connect(self._open_tunnel)
        self.open_tunnel_action.setVisible(self.PINTHEON_ACTIVE)

        self.set_tunnel_token_action = QAction(self.cog_icon, "Set Pinggy Token", self)
        self.set_tunnel_token_action.triggered.connect(self._set_tunnel_token)
        self.set_tunnel_token_action.setVisible(False)

        self.set_tunnel_tier_action = QAction(self.cog_icon, "Set Pinggy Tier", self)
        self.set_tunnel_tier_action.triggered.connect(self._set_tunnel_tier)
        self.set_tunnel_tier_action.setVisible(False)

        self.set_pintheon_network_action = QAction(self.cog_icon, "Set Network", self)
        self.set_pintheon_network_action.triggered.connect(self._set_pintheon_network)
        self.set_pintheon_network_action.setVisible(False)

        self.run_pintheon_action = QAction(self.pintheon_icon, "Start Pintheon", self)
        self.run_pintheon_action.triggered.connect(self._start_pintheon)

        self.stop_pintheon_action = QAction(self.pintheon_icon, "Stop Pintheon", self)
        self.stop_pintheon_action.triggered.connect(self._stop_pintheon)

        self.open_pintheon_action = QAction(self.web_icon, "Open Admin", self)
        self.open_pintheon_action.triggered.connect(self._open_pintheon)

        self.open_homepage_action = QAction(self.web_icon, "Open Homepage", self)
        self.open_homepage_action.triggered.connect(self._open_homepage)
        
        # Set initial visibility based on PINTHEON_ACTIVE state
        self.run_pintheon_action.setVisible(not self.PINTHEON_ACTIVE)
        self.stop_pintheon_action.setVisible(self.PINTHEON_ACTIVE)
        self.open_pintheon_action.setVisible(self.PINTHEON_ACTIVE)
        self.open_homepage_action.setVisible(self.PINTHEON_ACTIVE)

        self.install_pintheon_action = QAction(self.install_icon, "Install Pintheon", self)
        self.install_pintheon_action.triggered.connect(self._install_pintheon)

        self.run_press_action = QAction(self.press_icon, "Run press", self)
        self.run_press_action.triggered.connect(self.run_press)

        self.install_press_action = QAction(self.install_icon, "Install press", self)
        self.install_press_action.triggered.connect(self._install_press)

        self.update_press_action = QAction(self.update_icon, "Update press", self)
        self.update_press_action.triggered.connect(self._update_press)

        self.install_addon_action = QAction(self.install_icon, "Install Blender Addon", self)
        self.install_addon_action.triggered.connect(self._install_blender_addon)

        self.update_addon_action = QAction(self.update_icon, "Update Blender Addon", self)
        self.update_addon_action.triggered.connect(self._update_blender_addon)

        update_tools_action = QAction(self.update_icon, "Update All Tools", self)
        update_tools_action.triggered.connect(self.update_tools)

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(qApp.quit)

        test_action = QAction("TEST", self)
        test_action.triggered.connect(self.test_process)
        
        test_animated_action = QAction("TEST ANIMATED", self)
        test_animated_action.triggered.connect(self.test_animated_process)

        tray_menu = QMenu()

        self.tray_tools_menu = tray_menu.addMenu("Tools")

        # self.tray_tools_menu.addAction(test_animated_action)


        self.tray_tools_update_menu = self.tray_tools_menu.addMenu("Installations")
        self.tray_tools_update_menu.addAction(self.install_hvym_action)
        self.tray_tools_update_menu.addAction(self.update_hvym_action)
        self.tray_tools_update_menu.addAction(self.install_press_action)
        self.tray_tools_update_menu.addAction(self.update_press_action)
        self.update_press_action.setVisible(False)
        self.install_press_action.setVisible(False)

        self.tray_tools_update_menu.addAction(self.install_pintheon_action)
        self.install_pintheon_action.setVisible(False)
        self.run_pintheon_action.setVisible(False)
        self.stop_pintheon_action.setVisible(False)
        self.open_pintheon_action.setVisible(False)
        self.open_homepage_action.setVisible(False)
        self.open_tunnel_action.setVisible(False)

        if self.PRESS.is_file():
            self.update_press_action.setVisible(True)
            self.install_press_action.setVisible(False)
            self.tray_press_menu = self.tray_tools_menu.addMenu("Press")
            self.tray_press_menu.addAction(self.run_press_action)
        else:
            self.update_press_action.setVisible(False)
            self.install_press_action.setVisible(True)

        if not self.HVYM.is_file():
            self.install_hvym_action.setVisible(True)
            self.update_hvym_action.setVisible(False)
        else:
            self.install_hvym_action.setVisible(False)
            self.update_hvym_action.setVisible(True)
            self._refresh_pintheon_ui_state()
            

        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.setStyleSheet(Path(str(self.STYLE_SHEET)).read_text())
        
        # Close splash screen and hide main window when initialization is complete
        QApplication.processEvents()  # Ensure splash is displayed
        time.sleep(0.5)  # Show splash for half a second
        if splash is not None:
            splash.close()
        self.hide()

    def _setup_pintheon_menu(self):  
        network_name = 'testnet'
        
        if self.PINTHEON_NETWORK and 'mainnet' in self.PINTHEON_NETWORK:
            network_name = 'mainnet'

        if self.PINTHEON_INSTALLED and (not hasattr(self, 'tray_pintheon_menu') or self.tray_pintheon_menu is None):
            self.tray_pintheon_menu = self.tray_tools_menu.addMenu("Pintheon "+network_name)
            self.tray_pintheon_menu.setIcon(self.pintheon_icon)

            self.pintheon_settings_menu = self.tray_pintheon_menu.addMenu("Settings")
            self.pintheon_settings_menu.addAction(self.set_tunnel_token_action)
            self.pintheon_settings_menu.addAction(self.set_tunnel_tier_action)
            # self.pintheon_settings_menu.addAction(self.set_pintheon_network_action)
            self.pintheon_settings_menu.setEnabled(False)

            self.tray_pintheon_menu.addAction(self.run_pintheon_action)
            self.tray_pintheon_menu.addAction(self.stop_pintheon_action)
            self.tray_pintheon_menu.addAction(self.open_tunnel_action)

            self.pintheon_interface_menu = self.tray_pintheon_menu.addMenu("Interface")
            self.pintheon_interface_menu.addAction(self.open_pintheon_action)
            self.pintheon_interface_menu.addAction(self.open_homepage_action)
            self.pintheon_interface_menu.setEnabled(False)
            self.install_hvym_action.setVisible(False)
            self.update_hvym_action.setVisible(True)
            self.tray_pintheon_menu.setVisible(True)

    def _setup_press_menu(self):
        if not hasattr(self, 'tray_press_menu') or self.tray_press_menu is None:
            self.tray_press_menu = self.tray_tools_menu.addMenu("Press")
            self.tray_press_menu.setIcon(self.press_icon)
            self.tray_press_menu.addAction(self.run_press_action)
            self.tray_press_menu.setVisible(True)
        

    def _init_logging(self):
        # Configure basic logging to console first
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Set up root logger with console handler
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers to avoid duplicate logs
        logger.handlers = []
        logger.addHandler(console_handler)
        
        # Now try to set up file logging
        try:
            # Ensure logs directory exists with proper permissions
            logs_dir = self.PATH / 'logs'
            try:
                logs_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
                # Verify directory was created and is writable
                test_file = logs_dir / '.write_test'
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                logger.warning(f"Could not create or write to logs directory {logs_dir}: {e}")
                if platform.system().lower() == 'linux':
                    try:
                        logger.info("Attempting to create logs directory with elevated permissions...")
                        import subprocess
                        subprocess.run(['sudo', 'mkdir', '-p', str(logs_dir)], check=True)
                        subprocess.run(['sudo', 'chmod', '755', str(logs_dir)], check=True)
                        subprocess.run(['sudo', 'chown', f"{os.getuid()}:{os.getgid()}", str(logs_dir)], check=True)
                        logger.info("Successfully created logs directory with elevated permissions")
                    except Exception as sudo_e:
                        logger.error(f"Failed to create logs directory even with sudo: {sudo_e}")
                        # Continue without file logging
                        self.logger = logger
                        return
            
            # Set up file handler with rotation (10MB per file, keep 5 backups)
            log_file = logs_dir / 'metavinci.log'
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    str(log_file),  # Convert to string for Python 3.6 compatibility
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.info(f"File logging initialized at {log_file.absolute()}")
            except Exception as e:
                logger.error(f"Failed to initialize file logging: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing logging: {e}")
        
        # Log startup information
        logger.info("=" * 80)
        logger.info("Metavinci starting...")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Installation directory: {self.PATH}")
        logger.info(f"Log file: {log_file.absolute() if 'log_file' in locals() else 'Not available'}")
        
        # Log important paths and permissions
        try:
            logger.info(f"User ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
            logger.info(f"Group ID: {os.getgid() if hasattr(os, 'getgid') else 'N/A'}")
            if hasattr(os, 'groups'):
                logger.info(f"User groups: {os.getgroups()}")
            
            # Log directory permissions
            for path in [self.PATH, logs_dir if 'logs_dir' in locals() else None]:
                if path and path.exists():
                    try:
                        stat_info = os.stat(str(path))
                        logger.info(f"Directory permissions for {path}: {oct(stat_info.st_mode)[-3:]}")
                        logger.info(f"Directory owner: {stat_info.st_uid}:{stat_info.st_gid}")
                    except Exception as e:
                        logger.warning(f"Could not get permissions for {path}: {e}")
        except Exception as e:
            logger.warning(f"Could not log system information: {e}")
        
        # Store logger reference
        self.logger = logger
        
        # Add a method to log HVYM path after it's initialized
        def log_hvym_path():
            if hasattr(self, 'HVYM') and self.HVYM is not None:
                try:
                    self.logger.info(f"HVYM path: {self.HVYM}")
                    if hasattr(self.HVYM, 'exists') and callable(self.HVYM.exists):
                        exists = self.HVYM.exists()
                        self.logger.info(f"HVYM exists: {exists}")
                        if not exists:
                            self.logger.warning("HVYM binary not found at expected location")
                except Exception as e:
                    self.logger.warning(f"Error checking HVYM path: {e}")
        
        # Store the method for later use
        self._log_hvym_path = log_hvym_path
        
        # Log environment variables that might affect the application
        for var in ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'LC_ALL', 'LD_LIBRARY_PATH']:
            if var in os.environ:
                logger.debug(f"ENV {var}: {os.environ[var]}")
        
        # HVYM path will be logged when it's initialized
        logger.debug("Logging system initialized")

    def _build_subprocess_env(self):
        """Create a robust environment for subprocesses to work when launched from Applications on macOS."""
        env = os.environ.copy()
        if platform.system().lower() == 'darwin':
            # Ensure PATH contains locations where docker and homebrew binaries are typically installed
            default_paths = [
                '/usr/local/bin',                 # Intel Homebrew + Docker symlink
                '/opt/homebrew/bin',              # Apple Silicon Homebrew
                '/usr/bin', '/bin', '/usr/sbin', '/sbin',
                '/Applications/Docker.app/Contents/Resources/bin'  # Docker Desktop internal CLI
            ]
            current_path_parts = env.get('PATH', '').split(':') if env.get('PATH') else []
            for p in default_paths:
                if p not in current_path_parts:
                    current_path_parts.append(p)
            env['PATH'] = ':'.join(current_path_parts)

            # Certs for robust HTTPS (some macOS launches miss proper SSL bundle)
            try:
                import certifi
                env['REQUESTS_CA_BUNDLE'] = certifi.where()
            except Exception:
                pass

            # Avoid PyInstaller temp dir issues and spaces by using a known temp directory
            try:
                tmp_base = Path.home() / '.metavinci_tmp'
                tmp_base.mkdir(parents=True, exist_ok=True)
                env['TMPDIR'] = str(tmp_base)
                env['TEMP'] = str(tmp_base)
                env['TMP'] = str(tmp_base)
            except Exception:
                pass

            # Ensure a sane locale
            env.setdefault('LC_ALL', 'en_US.UTF-8')
            env.setdefault('LANG', 'en_US.UTF-8')

            # Prefer user's Docker Desktop socket if present
            try:
                docker_sock_home = Path.home() / '.docker' / 'run' / 'docker.sock'
                default_sock = Path('/var/run/docker.sock')
                if 'DOCKER_HOST' not in env and docker_sock_home.exists() and not default_sock.exists():
                    env['DOCKER_HOST'] = f'unix://{docker_sock_home}'
            except Exception:
                pass
        return env

    def init_post(self):
        self.user_pid = str(self._run('dfx identity get-principal')).strip()
        self.DB.update({'INITIALIZED': True, 'principal': self.user_pid}, self.QUERY.type == 'app_data')
        self._installation_check()
        self._check_press_installation()
        msg = QMessageBox(self)
        msg.setWindowTitle("!")
        msg.setText("Metavinci must restart now...")
        msg.exec_()
        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def restart(self):
        self.open_msg_dialog("Metavinci must close now, restart it after close...")
        self.close()

    def open_dir_dialog(self, prompt):
        self.show()
        dir_name = QFileDialog.getExistingDirectory(self, prompt)
        if dir_name:
            path = Path(dir_name)
            return str(path)
        
        self.hide()

    def loading_indicator_start(self, prompt):
        self.loading = self.loading_window(prompt)
        time.sleep(0.5)
        QApplication.processEvents()
        return self.loading
    
    def loading_indicator_stop(self):
        self.loading.close()
        self.hide()
    
    def loading_window(self, prompt):
        """
        Creates and shows a non-blocking loading indicator window.
        
        Args:
            prompt (str): Text to display in the loading window
            
        Returns:
            LoadingWindow: The window object with a close() method
        """
        self.show()
        
        loading_window = LoadingWindow(self, prompt)
        loading_window.show()
        loading_window.raise_()
        loading_window.activateWindow()
        QApplication.processEvents()

        
        return loading_window
    
    def splash_window(self, image_path=None):
        """
        Creates and shows a splash screen window using QSplashScreen.
        
        Args:
            image_path (str): Path to the splash image (defaults to METAVINCI_IMG)
            
        Returns:
            QSplashScreen: The splash screen object with a close() method
        """
        # Use default image if none provided
        if image_path is None:
            image_path = self.HVYM_IMG
        
        # Load the splash image
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Warning: Could not load splash image: {image_path}")
            # Create a fallback pixmap with text
            pixmap = QPixmap(300, 150)
            pixmap.fill(Qt.transparent)
        
        # Create the splash screen
        splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
        
        # Show the splash screen
        splash.show()
        
        # Force Qt to process events to ensure splash is displayed
        QApplication.processEvents()
        
        return splash
    
    def animated_loading_window(self, prompt, gif_path=None):
        """
        Creates and shows a non-blocking animated loading indicator window.
        
        Args:
            prompt (str): Text to display in the loading window
            gif_path (str): Path to the GIF file (defaults to LOADING_GIF)
            
        Returns:
            AnimatedLoadingWindow: The window object with start_animation() and stop_animation() methods
        """
        self.show()

        # Use default GIF if none provided
        if gif_path is None:
            gif_path = self.LOADING_GIF
        
        animated_window = AnimatedLoadingWindow(self, prompt, gif_path)
        
        animated_window.show()
        
        animated_window.raise_()
        animated_window.activateWindow()
        
        # Start the animation
        animated_window.start_animation()
        
        # Force Qt to process events to ensure window is displayed
        QApplication.processEvents()

        return animated_window
        
    def open_file_dialog(self, prompt, filter="*.key"):
        self.show
        filename, ok = QFileDialog.getOpenFileName(
            self,
            prompt, 
            self.HOME, 
            filter
        )
        if filename:
            path = Path(filename)
            return str(path)

        self.hide()
        
    def open_confirm_dialog(self, prompt):
        self.show()
        result = False
        response = QMessageBox.question(self, '?', prompt, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if response == QMessageBox.Yes:
            result = True

        self.hide()
        return result

    def open_msg_dialog(self, prompt):
        msg = QMessageBox(self)
        msg.setWindowTitle("!")
        msg.setText(prompt)
        msg.raise_()
        msg.exec_()
    
    def open_option_dialog(self, prompt, options):
        self.show()
        result = False
        dlg =  QFileDialog(self)
        label = QLabel(prompt)
        combo = QComboBox()
        combo.addItems(["option1", "option2", "option3"])
        box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            centerButtons=True,
        )

        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)

        lay = QGridLayout(self)
        lay.addWidget(label, 0, 0)
        lay.addWidget(combo, 0, 1)
        lay.addWidget(box, 1, 0, 1, 2)

        dlg.resize(640, 240)

        response = box.Ok

        if response == QDialogButtonBox.Ok:
            result = True

        self.hide()
        return result

    # Task function for generating and storing the app keypair using biscuit-python
    def generate_store_keypair(self):
        encryption_key_path = self.open_dir_dialog("Select Directory to Store Encryption Key")

        if encryption_key_path == None:
            return
        else:
            encryption_key_path = os.path.join(encryption_key_path, 'encryption_key.key')
            print(encryption_key_path)
            print(os.path.isfile(encryption_key_path))
        
        try:
            # Generate keypair using biscuit-python
            keypair = KeyPair()

            serialized_keys = {
                "private_key": keypair.private_key.to_hex(),
                "public_key": keypair.public_key.to_hex()
            }
            
            # print("key generated & stored : ",serialized_keys)
            # locate .metavinci directory in user's home directory
            if not self.PATH.exists():
                create_secure_directory(self.PATH)  # Create directory with secure permissions

            # # Generate a symmetric encryption key
            encryption_key = Fernet.generate_key()
            cipher_suite = Fernet(encryption_key)

            serialized_keys_str = json.dumps(serialized_keys)
            encrpted_keys = cipher_suite.encrypt(serialized_keys_str.encode())

            keystore_path = str(self.KEYSTORE)

            if os.path.isfile(encryption_key_path):
                overwrite = self.open_confirm_dialog(f"File {encryption_key_path} already exists, do you want to overwrite it?")
                if overwrite == True:
                    # # # Write the encryption key
                    with open(encryption_key_path, 'wb') as encrypt_key_file:
                        encrypt_key_file.write(encryption_key)

            if self.KEYSTORE.is_file():
                overwrite = self.open_confirm_dialog(f"File {keystore_path} already exists, do you want to overwrite it?")
                if overwrite == True:
                    # # # Write the private key securely (restrict access to owner)
                    with open(keystore_path, 'wb') as keystore_file:
                        keystore_file.write(encrpted_keys)
                    set_secure_permissions(keystore_path)

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error generating and storing app keypair.")

    def import_keys(self):
        encryption_key_path = self.open_file_dialog("Load encryption key.")

        print(encryption_key_path)

        if encryption_key_path == None:
            return
        
        try:
            # locate .metavinci directory in user's home directory
            if not self.PATH.exists():
                create_secure_directory(self.PATH)
            
            # Read the encrypted keys
            keystore_path = str(self.KEYSTORE)
            encryption_key_path = str(self.ENC_KEY)

            if not os.path.exists(keystore_path) or not os.path.exists(encryption_key_path):
                self.open_msg_dialog("No keypair found to import.")
                return
            
            with open(encryption_key_path, 'rb') as encrypt_key_file:
                encryption_key = encrypt_key_file.read()
            cipher_suite = Fernet(encryption_key)

            with open(keystore_path, 'rb') as keystore_file:
                encrypted_keys = keystore_file.read()

            decrypted_keys = cipher_suite.decrypt(encrypted_keys)
            serialized_keys = json.loads(decrypted_keys)

            # print("key imported : ",serialized_keys)
            self.private_key = PrivateKey.from_hex(serialized_keys['private_key'])
            self.public_key = PublicKey.from_hex(serialized_keys['public_key'])

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error importing app keypair.")

    def generate_store_token(self):
        try:
            builder = BiscuitBuilder()
            
            account_name = self._subprocess('dfx identity whoami').strip()
            oro_balance = 1000

            # Add facts to the token
            builder.add_fact(Fact(f'account_name("{account_name}")'))
            builder.add_fact(Fact(f'account_principal("{self.user_pid}")'))
            builder.add_fact(Fact(f'account_oro_balance({oro_balance})'))

            # Add expiration timestamp as a fact
            expiration_time = (datetime.now(tz=timezone.utc) + timedelta(hours=8)).timestamp()
            print(expiration_time)
            builder.add_fact(Fact(f'Timestamp("{expiration_time}")'))

            # Build and serialize the token
            token = builder.build(self.private_key)
            serialized_token = bytes(token.to_bytes())
            token_path = os.path.join(self.PATH, 'auth_token.enc')

            # Write the token securely (restrict access to owner)
            with open(token_path, 'wb') as token_file:
                token_file.write(serialized_token)
            set_secure_permissions(token_path)

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error generating and storing token.")

    def authorize_token(self):
        try:
            s_token = self.get_serialized_token()
            tkn = Biscuit.from_bytes(s_token, self.public_key)
            authorizer = Authorizer("""
                                    allow if account_principal({p});
                                    """,{ "p": f'{self.user_pid}'})
            authorizer.add_token(tkn)
            idx = authorizer.authorize()
            print("token authorized (index): ",idx)
            return True
        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error authorizing token.")
            return False

    def get_serialized_token(self):
        try:
            token_path = os.path.join(self.PATH, 'auth_token.enc')
            if not os.path.exists(token_path):
                self.open_msg_dialog("No token found.")
                return
            
            with open(token_path, 'rb') as token_file:
                serialized_token = token_file.read()
            
            return serialized_token

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error fetching token.")

    def authorization_loop(self):
        while True:
            # print("Generating new token and authorizing...")
            # self.generate_store_token()
            authorized = self.authorize_token()
            if authorized:
                print("Token authorized. Sleeping for 8 hours...")
            else:
                print("Token authorization failed. Retrying in 10 seconds...")
            time.sleep(self.refresh_interval if authorized else 10)

    def _subprocess(self, command, cwd=None, non_blocking=False, **kwargs):
        """
        Run a subprocess command.
        
        Args:
            command: Command to run (string for shell, list for exec)
            cwd: Working directory for the command
            non_blocking: If True, run the process in the background
            **kwargs: Additional arguments for subprocess.Popen
            
        Returns:
            If non_blocking=True, returns the Popen object
            If non_blocking=False, returns the command output or None on failure
        """
        try:
            # Support both string (shell) and list (exec) command forms
            is_list = isinstance(command, (list, tuple))
            
            if hasattr(self, 'logger'):
                cmd_str = ' '.join(command) if is_list else command
                self.logger.info(f"RUN (exec): {cmd_str} | cwd={cwd} | non_blocking={non_blocking}")
            
            if non_blocking:
                # For non-blocking, use Popen and return the process object
                if is_list:
                    process = subprocess.Popen(
                        command,
                        cwd=cwd,
                        env=self.proc_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        **kwargs
                    )
                else:
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=cwd,
                        env=self.proc_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        **kwargs
                    )
                # Store the process if needed for later management
                if not hasattr(self, '_background_processes'):
                    self._background_processes = []
                self._background_processes.append(process)
                return process
            else:
                # Original blocking behavior
                if is_list:
                    result = subprocess.run(list(command), capture_output=True, text=True, cwd=cwd, env=self.proc_env, **kwargs)
                    if hasattr(self, 'logger'):
                        self.logger.info(f"RET={result.returncode}\nSTDOUT=\n{result.stdout}\nSTDERR=\n{result.stderr}")
                    if result.returncode == 0:
                        return result.stdout
                    return None
                else:
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, cwd=cwd, env=self.proc_env, **kwargs)
                    text = output.decode('utf-8')
                    if hasattr(self, 'logger'):
                        self.logger.info(f"RET=0\nSTDOUT=\n{text}")
                    return text
                    
        except subprocess.CalledProcessError as e:
            try:
                if hasattr(self, 'logger'):
                    out = e.output.decode('utf-8', errors='replace') if isinstance(e.output, (bytes, bytearray)) else str(e.output)
                    self.logger.error(f"NONZERO (shell): code={e.returncode}\nOUTPUT=\n{out}")
            except Exception:
                pass
            return None
        except Exception:
            try:
                if hasattr(self, 'logger'):
                    self.logger.exception(f"Subprocess error for command={command}")
            except Exception:
                pass
            return None
        
    def _subprocess_hvym(self, command, non_blocking=False):
        # Run hvym from its install directory to preserve any relative resource lookups
        hvym_path = Path(self.HVYM)
        cli_dir = str(hvym_path.parent)
        return self._subprocess(command, cwd=cli_dir, non_blocking=non_blocking)
    
    def _run(self, command):
        try:
            # Use platform-specific shell command
            shell_cmd = self.platform_manager.get_shell_command(command)
            output = subprocess.run(shell_cmd, capture_output=True, text=True)
            return output.stdout
        except Exception as e:
            return None
        
    def run_press(self, non_blocking=True):
        return self._subprocess([str(self.PRESS)], non_blocking=non_blocking)

    def splash(self):
        return self._subprocess_hvym([str(self.HVYM), 'splash'])
    
    def new_stellar_account(self):
        return self._subprocess_hvym([str(self.HVYM), 'stellar-new-account'])

    def change_stellar_account(self):
        return self._subprocess_hvym([str(self.HVYM), 'stellar-set-account'])

    def remove_stellar_account(self):
        return self._subprocess_hvym([str(self.HVYM), 'stellar-remove-account'])
    
    def new_stellar_testnet_account(self):
        return self._subprocess_hvym([str(self.HVYM), 'stellar-new-testnet-account'])

    def hvym_check(self):
        return self._subprocess_hvym([str(self.HVYM), 'check'])
    
    def hvym_setup_pintheon(self):
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-setup'])

    def hvym_pintheon_exists(self):
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-image-exists'])

    def hvym_tunnel_token_exists(self):
        return self._subprocess_hvym([str(self.HVYM), 'pinggy-token'])
    
    def hvym_start_pintheon(self):
        # Only run the CLI; UI updates must occur on main thread after completion
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-start'])
    
    def hvym_open_pintheon(self):
        # Only run the CLI; UI updates must occur on main thread after completion
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-open'])
    
    def hvym_stop_pintheon(self):
        # Only run the CLI; UI updates must occur on main thread after completion
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-stop'])
    
    def hvym_open_tunnel(self):
        # Update the pintheon icon variable
        self.tunnel_icon = QIcon(self.OFF_IMG)

        # Update the menu action icons
        self.open_tunnel_action.setIcon(self.tunnel_icon)

        return self._subprocess_hvym([str(self.HVYM), 'pintheon-tunnel-open'], non_blocking=True)
    
    def hvym_set_tunnel_token(self):
        return self._subprocess_hvym([str(self.HVYM), 'pinggy-set-token'])

    def hvym_set_tunnel_tier(self):
        return self._subprocess_hvym([str(self.HVYM), 'pinggy-set-tier'])

    def hvym_get_tunnel_tier(self):
        return self._subprocess_hvym([str(self.HVYM), 'pinggy-tier'])
    
    def hvym_set_pintheon_network(self):
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-set-network'])
    
    def hvym_get_pintheon_network(self):
        return self._subprocess_hvym([str(self.HVYM), 'pintheon-network'])

    def hvym_is_tunnel_open(self):
        return self._subprocess_hvym([str(self.HVYM), 'is-pintheon-tunnel-open'])
    
    def hvym_docker_installed(self):
        return self._subprocess_hvym([str(self.HVYM), 'docker-installed'])

    def hvym_install_stats(self):
        import json
        result = self._subprocess_hvym([str(self.HVYM), 'installation-stats'])
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback to raw output if JSON parsing fails
                return result
        return None

    def update_tools(self):
        update = self.open_confirm_dialog('You want to update Heavymeta Tools?')
        if update == True:
            self._update_blender_addon(self.BLENDER_VERSION)
            if self.HVYM.is_file():
                self._update_cli()
                self._subprocess_hvym(f'{str(self.HVYM)} update-npm-modules')
            if self.PRESS.is_file():
                self._update_press()

    def threaded_loading_window(self, prompt, work_function, *args, **kwargs):
        """
        Creates a loading window that runs work in a background thread.
        
        Args:
            prompt (str): Text to display in the loading window
            work_function (callable): Function to execute in background thread
            *args, **kwargs: Arguments to pass to work_function
            
        Returns:
            tuple: (loading_window, worker_thread) - both need to be kept in scope
        """
        self.show()
        
        # Create the loading window
        loading_window = LoadingWindow(self, prompt)
        loading_window.show()
        loading_window.raise_()
        loading_window.activateWindow()
        QApplication.processEvents()
        
        # Create and configure the worker thread
        worker = LoadingWorker(work_function, *args, **kwargs)
        
        # Connect signals (marshal callbacks onto main thread)
        worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_loading_finished(loading_window, worker)))
        worker.error.connect(lambda error_msg: self._on_loading_error(loading_window, worker, error_msg))
        worker.success.connect(lambda success_msg: self._on_loading_success(loading_window, worker, success_msg))
        
        # Start the worker thread
        worker.start()
        
        return loading_window, worker
    
    def threaded_animated_loading_window(self, prompt, work_function, gif_path=None, *args, **kwargs):
        """
        Creates an animated loading window that runs work in a background thread.
        
        Args:
            prompt (str): Text to display in the loading window
            work_function (callable): Function to execute in background thread
            gif_path (str): Path to the GIF file (defaults to LOADING_GIF)
            *args, **kwargs: Arguments to pass to work_function
            
        Returns:
            tuple: (animated_window, worker_thread) - both need to be kept in scope
        """
        self.show()

        # Use default GIF if none provided
        if gif_path is None:
            gif_path = self.LOADING_GIF
        
        # Create the animated loading window
        animated_window = AnimatedLoadingWindow(self, prompt, gif_path)
        animated_window.show()
        animated_window.raise_()
        animated_window.activateWindow()
        animated_window.start_animation()
        QApplication.processEvents()
        
        # Create and configure the worker thread
        worker = LoadingWorker(work_function, *args, **kwargs)
        
        # Connect signals (marshal callbacks onto main thread)
        worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(animated_window, worker)))
        worker.error.connect(lambda error_msg: self._on_animated_loading_error(animated_window, worker, error_msg))
        worker.success.connect(lambda success_msg: self._on_animated_loading_success(animated_window, worker, success_msg))
        
        # Start the worker thread
        worker.start()
        
        return animated_window, worker
    
    def _on_loading_finished(self, loading_window, worker):
        """Handle completion of threaded loading operation."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
    
    def _on_loading_error(self, loading_window, worker, error_msg):
        """Handle error in threaded loading operation."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        self.open_msg_dialog(f"Error: {error_msg}")
    
    def _on_loading_success(self, loading_window, worker, success_msg):
        """Handle success in threaded loading operation."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        self.open_msg_dialog(success_msg)
    
    def _on_animated_loading_finished(self, animated_window, worker):
        """Handle completion of threaded animated loading operation."""
        animated_window.stop_animation()
        animated_window.close()
        self.hide()
        worker.deleteLater()
    
    def _on_animated_loading_error(self, animated_window, worker, error_msg):
        """Handle error in threaded animated loading operation."""
        animated_window.stop_animation()
        animated_window.close()
        self.hide()
        worker.deleteLater()
        self.open_msg_dialog(f"Error: {error_msg}")
    
    def _on_animated_loading_success(self, animated_window, worker, success_msg):
        """Handle success in threaded animated loading operation."""
        animated_window.stop_animation()
        animated_window.close()
        self.hide()
        worker.deleteLater()
        self.open_msg_dialog(success_msg)
    
    def _simulate_work(self, duration=10):
        """Simulate work for testing purposes."""
        for i in range(duration):
            time.sleep(1)  # Simulate work
            # Emit progress if needed
            # self.progress.emit(f"Working... {i+1}/{duration}")
    
    def _simulate_animated_work(self, duration=100):
        """Simulate work for animated testing purposes."""
        for i in range(duration):
            time.sleep(0.1)  # Simulate work
            # Emit progress if needed
            # self.progress.emit(f"Working... {i+1}/{duration}")
    
    def test_process(self):
        """Test the threaded loading window functionality."""
        # Use the new threaded method
        loading_window, worker = self.threaded_loading_window('TESTING', self._simulate_work, 10)
        
        # The loading window and worker will be automatically cleaned up when the work is done
        # No need to manually close or hide - the signal handlers will do that
    
    def test_animated_process(self):
        """Test the threaded animated loading window functionality."""
        # Use the new threaded method
        animated_window, worker = self.threaded_animated_loading_window('ANIMATED TESTING', self._simulate_animated_work, None, 100)
        
        # The animated window and worker will be automatically cleaned up when the work is done
        # No need to manually close or hide - the signal handlers will do that

    def _installation_check(self):
        if not self.HVYM.is_file():
            print('Install the cli')
            self._install_hvym()
        else:
            print('hvym is installed')
            check = self.hvym_check()
            if check != None and check.strip() == 'ONE-TWO':
                print('hvym is on path')

    def _check_press_installation(self):
        """Check if hvym_press is installed and update tray actions accordingly."""
        try:
            if self.PRESS.is_file():
                print('hvym_press is installed')
                # Update UI to reflect press availability
                self._update_ui_on_press_installed()
            else:
                print('hvym_press is not installed')
                # Ensure install action is visible if supported on current architecture
                if self.platform_manager.is_hvym_press_supported():
                    if hasattr(self, 'install_press_action'):
                        self.install_press_action.setVisible(True)
                    if hasattr(self, 'update_press_action'):
                        self.update_press_action.setVisible(False)
                # Hide run action if it exists
                if hasattr(self, 'run_press_action'):
                    self.run_press_action.setVisible(False)
        except Exception as e:
            print(f"Error checking press installation: {e}")

    def _refresh_startup_ui_state(self):
        """Refresh all UI states after startup to ensure tray menu accuracy."""
        try:
            # Refresh press UI state
            self._refresh_press_ui_state()
                
        except Exception as e:
            print(f"Error refreshing startup UI state: {e}")

    def _install_hvym(self):
        install = self.open_confirm_dialog('Install Heavymeta cli?')
        if install == True:
            # Create custom worker
            worker = HvymInstallWorker(self.HVYM)

            # Create animated loading window
            loading_window = AnimatedLoadingWindow(self, 'INSTALLING HVYM', self.LOADING_GIF)
            loading_window.show()
            loading_window.raise_()
            loading_window.activateWindow()
            loading_window.start_animation()
            QApplication.processEvents()

            # Connect signals
            worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(loading_window, worker)))
            worker.error.connect(lambda error_msg: self._on_animated_loading_error(loading_window, worker, error_msg))
            worker.success.connect(lambda success_msg: QTimer.singleShot(0, lambda: self._on_hvym_install_success(loading_window, worker, success_msg)))

            # Start the worker thread
            worker.start()

            # Store references to prevent garbage collection
            self._current_loading_window = loading_window
            self._current_worker = worker
    
    def _on_hvym_install_success(self, loading_window, worker, success_msg):
        """Handle successful hvym installation."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        
        # Update UI to reflect hvym availability
        self._update_ui_on_hvym_installed()
        # Show success message
        self.open_msg_dialog(success_msg)


    def _update_hvym(self):
        update = self.open_confirm_dialog('Update Heavymeta cli?')
        if update == True:
            # Create custom worker
            worker = HvymInstallWorker(self.HVYM)  # Reuse the same worker class
            
            # Create animated loading window
            loading_window = AnimatedLoadingWindow(self, 'UPDATING HVYM', self.LOADING_GIF)
            loading_window.show()
            loading_window.raise_()
            loading_window.activateWindow()
            loading_window.start_animation()
            QApplication.processEvents()
            
            # Connect signals
            worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(loading_window, worker)))
            worker.error.connect(lambda error_msg: self._on_animated_loading_error(loading_window, worker, error_msg))
            worker.success.connect(lambda success_msg: QTimer.singleShot(0, lambda: self._on_hvym_update_success(loading_window, worker, success_msg)))
            
            # Start the worker thread
            worker.start()
            
            # Store references to prevent garbage collection
            self._current_loading_window = loading_window
            self._current_worker = worker
    
    def _on_hvym_update_success(self, loading_window, worker, success_msg):
        """Handle successful hvym update."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        
        # Ensure UI remains consistent after update
        self._update_ui_on_hvym_installed()
        # Show success message
        self.open_msg_dialog(success_msg)

    def _delete_hvym(self):
        """Delete the hvym CLI binary and clean up related files."""
        try:
            if self.HVYM.is_file():
                self.HVYM.unlink()
                print(f"Removed hvym binary: {self.HVYM}")
            
            # For macOS, also clean up directories if empty
            if platform.system().lower() == "darwin":
                try:
                    from macos_install_helper import MacOSInstallHelper
                    helper = MacOSInstallHelper()
                    helper.uninstall_hvym_cli()
                except ImportError:
                    print("macOS installation helper not available for cleanup")
                except Exception as e:
                    print(f"Error during macOS cleanup: {e}")
            
            return True
        except Exception as e:
            print(f"Error deleting hvym: {e}")
            return False

    def _install_blender_addon(self, version):
        install = self.open_confirm_dialog('Install Heavymeta Blender Addon?')
        if install is True:
            if self.BLENDER_PATH.exists() and self.ADDON_INSTALL_PATH.exists():
                # Run install on a background thread; keep animation running until finished
                def _install_blender_addon_worker_fn():
                    try:
                        if not self.ADDON_PATH.exists():
                            url = 'https://github.com/inviti8/heavymeta_standard/archive/refs/heads/main.zip'
                            ok = download_and_extract_zip(url, str(self.ADDON_INSTALL_PATH))
                            if not ok:
                                raise Exception('Failed to download/extract Blender Addon')
                        return True
                    except Exception as e:
                        return e

                # Create animated loading window
                loading_window = AnimatedLoadingWindow(self, 'INSTALLING BLENDER ADDON', self.LOADING_GIF)
                loading_window.show()
                loading_window.raise_()
                loading_window.activateWindow()
                loading_window.start_animation()
                QApplication.processEvents()

                # Create worker
                worker = LoadingWorker(_install_blender_addon_worker_fn)

                # On success/error, stop animation and notify
                def _on_success(_msg):
                    loading_window.stop_animation()
                    loading_window.close()
                    self.hide()
                    self.open_msg_dialog('Blender Addon installed. Please restart Daemon.')

                def _on_error(err_msg):
                    loading_window.stop_animation()
                    loading_window.close()
                    self.hide()
                    self.open_msg_dialog(err_msg or 'Failed to install Blender Addon')

                def _on_finished():
                    # finished already handled by success/error handlers
                    pass

                # Connect signals
                worker.finished.connect(lambda: QTimer.singleShot(0, _on_finished))
                worker.error.connect(lambda emsg: _on_error(emsg))
                worker.success.connect(lambda _msg: _on_success(_msg))

                # Start the worker
                worker.start()
                # Keep references
                self._current_loading_window = loading_window
                self._current_worker = worker
            else:
                self.open_msg_dialog('Blender not found. Please install blender first')

    def _update_blender_addon(self, version):
        self._delete_blender_addon(version)
        self._install_blender_addon(version)

    def _delete_blender_addon(self, version):
        for item in self.ADDON_INSTALL_PATH.iterdir():
                if item.name != '.git' and item.name != 'README.md' and item.name != 'install.sh':
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)

        shutil.rmtree(str(self.ADDON_INSTALL_PATH))

    def _install_pintheon(self):
        install = self.open_confirm_dialog('Install Pintheon?')
        if install == True:
            # Create custom worker
            worker = PintheonInstallWorker(self.HVYM)
            
            # Create animated loading window
            loading_window = AnimatedLoadingWindow(self, 'INSTALLING PINTHEON', self.LOADING_GIF)
            loading_window.show()
            loading_window.raise_()
            loading_window.activateWindow()
            loading_window.start_animation()
            QApplication.processEvents()
            
            # Connect signals
            worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(loading_window, worker)))
            worker.error.connect(lambda error_msg: self._on_animated_loading_error(loading_window, worker, error_msg))
            worker.success.connect(lambda success_msg: QTimer.singleShot(0, lambda: self._on_pintheon_install_success(loading_window, worker, success_msg)))
            
            # Start the worker thread
            worker.start()
            
            # Store references to prevent garbage collection
            self._current_loading_window = loading_window
            self._current_worker = worker
    
    def _on_pintheon_install_success(self, loading_window, worker, success_msg):
        """Handle successful Pintheon installation."""

        loading_window.close()
        self.hide()
        worker.deleteLater()

        self.PINTHEON_INSTALLED = True
        self.DOCKER_INSTALLED = True
        
        # Refresh UI to show start/stop actions
        self._refresh_pintheon_ui_state()
        # Show success message
        self.open_msg_dialog(success_msg)
        
    def _update_ui_on_hvym_installed(self):
        # Toggle install/update visibility
        self.install_hvym_action.setVisible(False)
        self.update_hvym_action.setVisible(True)
        # Refresh Pintheon UI state based on actual installation
        self._refresh_pintheon_ui_state()

    def _update_ui_on_press_installed(self):
        """Update UI to reflect hvym_press availability after installation."""
        # Toggle install/update visibility
        self.install_press_action.setVisible(False)
        self.update_press_action.setVisible(True)
        # Refresh press UI state based on actual installation
        self._refresh_press_ui_state()
        
    def _refresh_pintheon_ui_state(self):
        self._setup_pintheon_menu()
        self.INSTALL_STATS = self.hvym_install_stats()
        self.PINTHEON_NETWORK = self.INSTALL_STATS['pintheon_network']
        
        if self.DOCKER_INSTALLED == True:
            self.PINTHEON_INSTALLED = self.INSTALL_STATS['pintheon_image_exists']

            if self.PINTHEON_INSTALLED:
                network_name = 'testnet'
        
                if self.PINTHEON_NETWORK and 'mainnet' in self.PINTHEON_NETWORK:
                    network_name = 'mainnet'
                
                self.tray_pintheon_menu.setTitle("Pintheon "+network_name)

                t = self.INSTALL_STATS['pinggy_tier']
                tier = 'free'
                if 'free' in t:
                    tier = 'pro'

                self.tray_pintheon_menu.setEnabled(True)
                self.pintheon_settings_menu.setEnabled(True)
                self.pintheon_interface_menu.setEnabled(True)
                self.set_tunnel_token_action.setVisible(True)
                self.set_tunnel_tier_action.setVisible(True)
                self.set_tunnel_tier_action.setText(f'Set Tunnel Tier to: {tier}')
                self.install_pintheon_action.setVisible(False)      
                self.run_pintheon_action.setVisible(not self.PINTHEON_ACTIVE)
                self.stop_pintheon_action.setVisible(self.PINTHEON_ACTIVE)
                self.open_pintheon_action.setVisible(self.PINTHEON_ACTIVE)
                self.open_homepage_action.setVisible(self.PINTHEON_ACTIVE)
                self.open_tunnel_action.setVisible(self.PINTHEON_ACTIVE and len(self.TUNNEL_TOKEN) >= 7)
            else:
                self.install_pintheon_action.setVisible(True)
        else:
            self.tray_tools_menu.addMenu("!!DOCKER NOT INSTALLED!!")


    def _refresh_press_ui_state(self):
        """Refresh press-related UI elements based on installation status."""
        if self.PRESS.is_file():
            self._setup_press_menu()
            # Only show press installation if hvym_press is supported on current architecture
            if self.platform_manager.is_hvym_press_supported():
                self.tray_press_menu.setEnabled(True)
                self.run_press_action.setVisible(True)
                self.update_press_action.setVisible(True)
                self.install_press_action.setVisible(False)
        else:
            # Only show press update if hvym_press is supported on current architecture
            if self.platform_manager.is_hvym_press_supported():
                self.update_press_action.setVisible(False)
                self.install_press_action.setVisible(True)

    def _start_pintheon(self):
        start = self.open_confirm_dialog('Start Pintheon Gateway?')
        if start:
            # Run synchronously on main thread (simpler, avoids threading/timer issues)
            result = self.hvym_start_pintheon()
            if result is not None:
                self.PINTHEON_ACTIVE = True
                self._update_ui_on_pintheon_started()
                self.hvym_open_pintheon()
            else:
                self.open_msg_dialog('Failed to start Pintheon. Check logs for details.')


    def _update_ui_on_pintheon_started(self):
        self.pintheon_icon = QIcon(self.ON_IMG)
        self.tray_icon.setIcon(QIcon(self.LOGO_IMG_ACTIVE))
        self.run_pintheon_action.setIcon(self.pintheon_icon)
        self.stop_pintheon_action.setIcon(self.pintheon_icon)
        self.run_pintheon_action.setVisible(False)
        self.stop_pintheon_action.setVisible(True)
        self.open_pintheon_action.setVisible(True)
        self.open_homepage_action.setVisible(True)
        self.open_tunnel_action.setVisible(len(self.TUNNEL_TOKEN) >= 7)

    def _stop_pintheon(self, confirm=True):
        stop = True
        if confirm:
            stop = self.open_confirm_dialog('Stop Pintheon Gateway?')
        if stop:
            # Run synchronously on main thread
            result = self.hvym_stop_pintheon()
            if result is not None:
                self.PINTHEON_ACTIVE = False
                self._update_ui_on_pintheon_stopped()
            else:
                self.open_msg_dialog('Failed to stop Pintheon. Check logs for details.')
    
    def _open_pintheon(self):
        open = self.open_confirm_dialog('Open Pintheon Admin Interface?')
        if open == True:
            webbrowser.open('https://127.0.0.1:9999/admin')

    def _open_homepage(self):
        open = self.open_confirm_dialog('Open Local Homepage?')
        if open == True:
            webbrowser.open('https://127.0.0.1:9998/')
        
    def _update_ui_on_pintheon_stopped(self):
        self.pintheon_icon = QIcon(self.OFF_IMG)
        self.tray_icon.setIcon(QIcon(self.LOGO_IMG))
        self.run_pintheon_action.setIcon(self.pintheon_icon)
        self.stop_pintheon_action.setIcon(self.pintheon_icon)
        self.run_pintheon_action.setVisible(True)
        self.stop_pintheon_action.setVisible(False)
        self.open_pintheon_action.setVisible(False)
        self.open_homepage_action.setVisible(False)
        self.open_tunnel_action.setVisible(False)

    def _open_tunnel(self):
        expose = self.open_confirm_dialog('Expose Pintheon Gateway to the Internet?')
        if expose == True:
            self.hvym_open_tunnel()
            # self.open_tunnel_action.setVisible(False)

    def _set_tunnel_token(self):
        self.hvym_set_tunnel_token()
        self.TUNNEL_TOKEN = self.hvym_tunnel_token_exists()
        if len(self.TUNNEL_TOKEN) < 7:
            self.open_tunnel_action.setVisible(False)
        else:
            self.open_tunnel_action.setVisible(True)

    def _set_tunnel_tier(self):
        self.hvym_set_tunnel_tier()
        self._refresh_pintheon_ui_state()

    def _set_pintheon_network(self):
        self.hvym_set_pintheon_network()
        self._refresh_pintheon_ui_state()

    def _install_press(self):
        # Check if hvym_press is supported on current architecture
        if not self.platform_manager.is_hvym_press_supported():
            self.open_msg_dialog("hvym_press is not supported on this architecture (macOS Apple Silicon)")
            return
            
        install = self.open_confirm_dialog('Install Heavymeta Press?')
        if install == True:
            # Create custom worker using the new HvymPressInstallWorker
            worker = HvymPressInstallWorker(self.PRESS)
            
            # Create animated loading window for consistency with hvym installation
            loading_window = AnimatedLoadingWindow(self, 'INSTALLING HVYM PRESS', self.LOADING_GIF)
            loading_window.show()
            loading_window.raise_()
            loading_window.activateWindow()
            loading_window.start_animation()
            QApplication.processEvents()
            
            # Connect signals
            worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(loading_window, worker)))
            worker.error.connect(lambda error_msg: self._on_animated_loading_error(loading_window, worker, error_msg))
            worker.success.connect(lambda success_msg: QTimer.singleShot(0, lambda: self._on_press_install_success(loading_window, worker, success_msg)))
            
            # Start the worker thread
            worker.start()
            
            # Store references to prevent garbage collection
            self._current_loading_window = loading_window
            self._current_worker = worker
    
    def _on_press_install_success(self, loading_window, worker, success_msg):
        """Handle successful Press installation."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        
        # Update UI to reflect press availability
        self._update_ui_on_press_installed()
        # Show success message
        self.open_msg_dialog(success_msg)
        
    def _on_press_update_success(self, loading_window, worker, success_msg):
        """Handle successful Press update."""
        loading_window.close()
        self.hide()
        worker.deleteLater()
        
        # Update UI to reflect press availability
        self._update_ui_on_press_installed()
        # Show success message
        self.open_msg_dialog(success_msg)

    def _delete_press(self):
        if self.PRESS.is_file():
            self.PRESS.unlink

    def _update_press(self):
        # Check if hvym_press is supported on current architecture
        if not self.platform_manager.is_hvym_press_supported():
            self.open_msg_dialog("hvym_press is not supported on this architecture (macOS Apple Silicon)")
            return
            
        update = self.open_confirm_dialog('Update Heavymeta Press?')
        if update == True:
            # Create custom worker using the new HvymPressInstallWorker
            worker = HvymPressInstallWorker(self.PRESS)
            
            # Create animated loading window for consistency with hvym installation
            loading_window = AnimatedLoadingWindow(self, 'UPDATING HVYM PRESS', self.LOADING_GIF)
            loading_window.show()
            loading_window.raise_()
            loading_window.activateWindow()
            loading_window.start_animation()
            QApplication.processEvents()
            
            # Connect signals
            worker.finished.connect(lambda: QTimer.singleShot(0, lambda: self._on_animated_loading_finished(loading_window, worker)))
            worker.error.connect(lambda error_msg: self._on_animated_loading_error(loading_window, worker, error_msg))
            worker.success.connect(lambda success_msg: QTimer.singleShot(0, lambda: self._on_press_update_success(loading_window, worker, success_msg)))
            
            # Start the worker thread
            worker.start()
            
            # Store references to prevent garbage collection
            self._current_loading_window = loading_window
            self._current_worker = worker

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Keep the app alive even if all windows are hidden/closed; tray remains active
    try:
        app.setQuitOnLastWindowClosed(False)
    except Exception:
        pass
    mw = Metavinci()
    mw.show()
    mw.setFixedSize(70,70)
    mw.center()
    mw.hide()
    
    # Refresh UI states after startup to ensure tray menu accuracy
    mw._refresh_startup_ui_state()
    
    sys.exit(app.exec())

