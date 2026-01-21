"""
Metavinci - Network Daemon for Heavymeta

This application supports threaded loading windows for better performance.
The loading windows run in background threads to keep the UI responsive during
long-running operations.

Threading Features:
- LoadingWorker: Base class for background operations
- threaded_loading_window(): Creates loading window with background work
- threaded_animated_loading_window(): Creates animated loading window with background work
- Custom workers for specific operations:
  * PintheonSetupWorker: For Pintheon Docker setup
  * PressInstallWorker: For hvym_press installation

Usage Example:
    # For simple operations
    loading_window, worker = self.threaded_loading_window('Loading...', my_work_function, arg1, arg2)

    # For animated operations
    animated_window, worker = self.threaded_animated_loading_window('Loading...', my_work_function, gif_path, arg1, arg2)

    # The windows and workers are automatically cleaned up when work completes
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QWidgetAction, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QComboBox, QDialogButtonBox, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QDesktopWidget, QFileDialog, QMessageBox, QSplashScreen, QPlainTextEdit, QScrollBar, QInputDialog, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QSize, QTimer, QByteArray, QThread, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QIcon, QPixmap, QImageReader, QPalette
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

try:
    from stellar_sdk import Keypair as StellarKeypair
    from hvym_stellar import Stellar25519KeyPair
    HAS_STELLAR_SDK = True
except ImportError:
    HAS_STELLAR_SDK = False
    StellarKeypair = None
    Stellar25519KeyPair = None

import hashlib

# Try to import API server
try:
    from api_server import ApiServerWorker, FASTAPI_AVAILABLE
    HAS_API_SERVER = FASTAPI_AVAILABLE
except ImportError:
    HAS_API_SERVER = False
    ApiServerWorker = None

# Try to import wallet manager
try:
    from wallet_manager import WalletManager
    HAS_WALLET_MANAGER = True
except ImportError:
    HAS_WALLET_MANAGER = False
    WalletManager = None

# Try to import Soroban components
try:
    from contract_builder import ContractBuilder
    from contract_deployer import ContractDeployer
    from deployment_manager import DeploymentManager
    HAS_SOROBAN = True
except ImportError:
    HAS_SOROBAN = False
    ContractBuilder = None
    ContractDeployer = None
    DeploymentManager = None

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


class PintheonSetupWorker(QThread):
    """
    Worker that directly handles Pintheon setup without CLI dependency.
    Installs Pinggy, pulls Docker image, and creates container with streaming output.
    """
    output_line = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    success = pyqtSignal(str)

    # Pintheon configuration
    PINTHEON_VERSION = 'latest'
    PINTHEON_PORT = 9998
    PINTHEON_NETWORK = 'testnet'
    PINGGY_VERSION = 'v0.2.2'

    def __init__(self):
        super().__init__()
        self._stop_requested = False

    def _get_pintheon_dapp_name(self):
        """Get architecture-specific Pintheon Docker image name."""
        machine = platform.machine().lower()

        # Normalize architecture
        if machine in ('x86_64', 'amd64', 'intel64', 'i386', 'i686'):
            arch = 'linux-amd64'
        elif machine in ('aarch64', 'arm64', 'armv8', 'armv7l', 'arm'):
            arch = 'linux-arm64'
        else:
            arch = f'linux-{machine}'

        return f'pintheon-{self.PINTHEON_NETWORK}-{arch}'

    def _get_pinggy_paths(self):
        """Get platform-specific Pinggy paths."""
        home = Path.home()
        system = platform.system().lower()
        if system == 'windows':
            pinggy_dir = home / 'AppData' / 'Local' / 'pinggy'
            pinggy_path = pinggy_dir / 'pinggy.exe'
        elif system == 'darwin':
            pinggy_dir = home / '.local' / 'share' / 'pinggy'
            pinggy_path = pinggy_dir / 'pinggy'
        else:  # Linux
            pinggy_dir = home / '.local' / 'share' / 'pinggy'
            pinggy_path = pinggy_dir / 'pinggy'
        return pinggy_dir, pinggy_path

    def _get_pinggy_download_url(self):
        """Get platform-specific Pinggy download URL."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Determine architecture
        if machine in ('x86_64', 'amd64'):
            arch = 'amd64'
        elif machine in ('arm64', 'aarch64'):
            arch = 'arm64'
        elif machine in ('i386', 'i686', 'x86'):
            arch = '386'
        else:
            arch = 'amd64'  # Default fallback

        base_url = f"https://s3.ap-south-1.amazonaws.com/public.pinggy.binaries/cli/{self.PINGGY_VERSION}"

        if system == 'windows':
            return f"{base_url}/windows/{arch}/pinggy.exe"
        elif system == 'darwin':
            return f"{base_url}/darwin/{arch}/pinggy"
        else:  # Linux
            return f"{base_url}/linux/{arch}/pinggy"

    def _get_docker_volume_path(self, local_path):
        """Get cross-platform Docker volume path."""
        system = platform.system().lower()
        path_str = str(local_path)

        if system == 'windows':
            # Convert Windows path to Docker-compatible format
            # C:\Users\... -> /c/Users/...
            if len(path_str) >= 2 and path_str[1] == ':':
                drive = path_str[0].lower()
                rest = path_str[2:].replace('\\', '/')
                return f"/{drive}{rest}"
        return path_str

    def _check_docker_installed(self):
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'Docker version' in result.stdout
        except Exception:
            return False

    def _docker_container_exists(self, name):
        """Check if a Docker container with the given name exists."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name=^{name}$', '--format', '{{{{.Names}}}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == name
        except Exception:
            return False

    def _docker_image_exists(self, image_name):
        """Check if a Docker image exists locally."""
        try:
            result = subprocess.run(
                ['docker', 'images', '-q', image_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _run_docker_command_streaming(self, command, description):
        """Run a Docker command and stream its output."""
        self.output_line.emit(f"\n{description}...")
        self.output_line.emit(f"$ {' '.join(command)}")

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                cwd=str(Path.home()),
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == 'windows' else 0
            )

            while not self._stop_requested:
                line = process.stdout.readline()
                if not line:
                    break
                try:
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                except Exception:
                    decoded = str(line).rstrip()
                if decoded:
                    self.output_line.emit(decoded)

            process.wait()
            return process.returncode == 0

        except Exception as e:
            self.output_line.emit(f"Error: {e}")
            return False

    def run(self):
        """Execute the Pintheon setup process."""
        try:
            self.output_line.emit("=" * 50)
            self.output_line.emit("Starting Pintheon Setup")
            self.output_line.emit("=" * 50)

            # Step 1: Check Docker
            self.output_line.emit("\n[1/4] Checking Docker installation...")
            if not self._check_docker_installed():
                self.error.emit("Docker is not installed. Please install Docker first.")
                self.finished.emit()
                return
            self.output_line.emit("Docker is installed ✓")

            # Step 2: Install Pinggy
            self.output_line.emit("\n[2/4] Installing Pinggy...")
            if not self._install_pinggy():
                self.error.emit("Failed to install Pinggy")
                self.finished.emit()
                return

            # Step 3: Pull Docker image
            self.output_line.emit("\n[3/4] Pulling Pintheon Docker image...")
            image_name = f"metavinci/{self._get_pintheon_dapp_name()}:{self.PINTHEON_VERSION}"
            pull_command = ['docker', 'pull', image_name]

            if not self._run_docker_command_streaming(pull_command, f"Pulling {image_name}"):
                self.error.emit(f"Failed to pull Docker image: {image_name}")
                self.finished.emit()
                return
            self.output_line.emit("Docker image pulled successfully ✓")

            # Step 4: Create container
            self.output_line.emit("\n[4/4] Creating Pintheon container...")
            if self._docker_container_exists('pintheon'):
                self.output_line.emit("Container 'pintheon' already exists, skipping creation")
            else:
                if not self._create_pintheon_container():
                    self.error.emit("Failed to create Pintheon container")
                    self.finished.emit()
                    return
                self.output_line.emit("Container created successfully ✓")

            # Step 5: Update hosts file
            self.output_line.emit("\n[5/5] Updating hosts file...")
            if ensure_hosts_entry('local.pintheon.com'):
                self.output_line.emit("Hosts file updated ✓")
            else:
                self.output_line.emit("Warning: Could not update hosts file automatically")
                self.output_line.emit("You may need to add '127.0.0.1 local.pintheon.com' manually")

            # Remove macOS quarantine from Pinggy if needed
            if platform.system().lower() == 'darwin':
                _, pinggy_path = self._get_pinggy_paths()
                if pinggy_path.exists():
                    try:
                        subprocess.run(
                            ['xattr', '-d', 'com.apple.quarantine', str(pinggy_path)],
                            capture_output=True,
                            check=False
                        )
                    except Exception:
                        pass

            self.output_line.emit("\n" + "=" * 50)
            self.output_line.emit("Pintheon setup completed successfully!")
            self.output_line.emit("=" * 50)

            self.success.emit("Pintheon installed successfully")
            self.finished.emit()

        except Exception as e:
            logging.error(f"PintheonSetupWorker error: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit()

    def _install_pinggy(self):
        """Download and install Pinggy."""
        try:
            pinggy_dir, pinggy_path = self._get_pinggy_paths()

            # Check if already installed
            if pinggy_path.exists():
                self.output_line.emit(f"Pinggy already installed at {pinggy_path}")
                return True

            # Get download URL
            download_url = self._get_pinggy_download_url()
            self.output_line.emit(f"Downloading Pinggy from: {download_url}")

            # Download
            response = requests.get(download_url, timeout=60)
            if not response.ok:
                self.output_line.emit(f"Failed to download Pinggy: HTTP {response.status_code}")
                return False

            # Create directory and write file
            pinggy_dir.mkdir(parents=True, exist_ok=True)
            with open(pinggy_path, 'wb') as f:
                f.write(response.content)

            # Make executable on Unix systems
            if platform.system().lower() != 'windows':
                os.chmod(pinggy_path, 0o755)

            self.output_line.emit(f"Pinggy installed successfully at {pinggy_path} ✓")
            return True

        except Exception as e:
            self.output_line.emit(f"Error installing Pinggy: {e}")
            return False

    def _create_pintheon_container(self):
        """Create the Pintheon Docker container."""
        try:
            # Create data directory
            data_dir = Path.home() / 'pintheon_data'
            data_dir.mkdir(parents=True, exist_ok=True)

            volume_path = self._get_docker_volume_path(data_dir)
            image_name = f"metavinci/{self._get_pintheon_dapp_name()}:{self.PINTHEON_VERSION}"

            command = [
                'docker', 'create',
                '--name', 'pintheon',
                '--dns=8.8.8.8',
                '--network', 'bridge',
                '-p', f'{self.PINTHEON_PORT}:{self.PINTHEON_PORT}/tcp',
                '-p', '9999:9999/tcp',
                '-v', f'{volume_path}:/home/pintheon/data',
                image_name
            ]

            self.output_line.emit(f"$ {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(Path.home()),
                timeout=60
            )

            if result.returncode != 0:
                self.output_line.emit(f"Error: {result.stderr or result.stdout}")
                return False

            return True

        except Exception as e:
            self.output_line.emit(f"Error creating container: {e}")
            return False

    def stop(self):
        """Request the worker to stop."""
        self._stop_requested = True


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


class StreamingOutputWorker(QThread):
    """Worker that streams subprocess output line by line for real-time display."""
    output_line = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    success = pyqtSignal(str)

    def __init__(self, command, cwd=None, env=None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.env = env
        self._process = None
        self._stop_requested = False

    def run(self):
        try:
            logging.info(f"StreamingOutputWorker: Starting command: {self.command}")
            self.output_line.emit(f"Starting: {' '.join(self.command)}")

            # Prepare environment
            run_env = self.env if self.env else os.environ.copy()

            # Add certifi CA bundle
            import certifi
            run_env["REQUESTS_CA_BUNDLE"] = certifi.where()

            # Force unbuffered Python output in child process
            run_env["PYTHONUNBUFFERED"] = "1"

            # Platform-specific environment setup
            if platform.system().lower() == 'darwin':
                default_paths = [
                    '/usr/local/bin',
                    '/opt/homebrew/bin',
                    '/usr/bin', '/bin', '/usr/sbin', '/sbin',
                    '/Applications/Docker.app/Contents/Resources/bin'
                ]
                current_path_parts = run_env.get('PATH', '').split(':') if run_env.get('PATH') else []
                for p in default_paths:
                    if p not in current_path_parts:
                        current_path_parts.append(p)
                run_env['PATH'] = ':'.join(current_path_parts)
                run_env.setdefault('LC_ALL', 'en_US.UTF-8')
                run_env.setdefault('LANG', 'en_US.UTF-8')

                # Docker socket handling
                try:
                    docker_sock_home = Path.home() / '.docker' / 'run' / 'docker.sock'
                    default_sock = Path('/var/run/docker.sock')
                    if 'DOCKER_HOST' not in run_env and docker_sock_home.exists() and not default_sock.exists():
                        run_env['DOCKER_HOST'] = f'unix://{docker_sock_home}'
                except Exception:
                    pass

            # Use home directory as cwd if not specified
            working_dir = self.cwd if self.cwd else str(Path.home())
            logging.info(f"StreamingOutputWorker: Working directory: {working_dir}")

            # Platform-specific Popen kwargs
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'cwd': working_dir,
                'env': run_env,
            }

            # On Windows, prevent console window and use different buffering
            if platform.system().lower() == 'windows':
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                # Use binary mode on Windows for more reliable streaming
                popen_kwargs['bufsize'] = 0
            else:
                popen_kwargs['text'] = True
                popen_kwargs['bufsize'] = 1

            # Start the process
            logging.info("StreamingOutputWorker: Starting subprocess...")
            self._process = subprocess.Popen(self.command, **popen_kwargs)
            logging.info(f"StreamingOutputWorker: Process started with PID: {self._process.pid}")

            # Stream output line by line using readline() for better cross-platform support
            if platform.system().lower() == 'windows':
                # Binary mode on Windows - decode manually
                while not self._stop_requested:
                    line = self._process.stdout.readline()
                    if not line:
                        break
                    try:
                        decoded_line = line.decode('utf-8', errors='replace').rstrip()
                    except Exception:
                        decoded_line = str(line).rstrip()
                    if decoded_line:
                        self.output_line.emit(decoded_line)
            else:
                # Text mode on Unix
                while not self._stop_requested:
                    line = self._process.stdout.readline()
                    if not line:
                        break
                    self.output_line.emit(line.rstrip())

            self._process.wait()
            logging.info(f"StreamingOutputWorker: Process exited with code: {self._process.returncode}")

            if self._process.returncode == 0:
                self.success.emit("Operation completed successfully")
            else:
                self.error.emit(f"Process exited with code {self._process.returncode}")

            self.finished.emit()

        except Exception as e:
            logging.error(f"StreamingOutputWorker: Exception: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit()

    def stop(self):
        """Stop the running process."""
        self._stop_requested = True
        if self._process and self._process.poll() is None:
            self._process.terminate()


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
        """Update the loading text and ensure it fits properly on screen."""
        # Set text color and background
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Window, Qt.black)
        self.setPalette(palette)
        
        # Update the message with the new palette
        self.showMessage(text, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        
        # Ensure the window is wide enough for the text
        if hasattr(self, 'movie') and self.movie.state() == QMovie.Running:
            # Get the current pixmap size
            current_pixmap = self.movie.currentPixmap()
            if not current_pixmap.isNull():
                # Calculate required width for the text
                font_metrics = self.fontMetrics()
                text_width = font_metrics.horizontalAdvance(text) + 20  # Add padding
                
                # Get the current size
                current_size = current_pixmap.size()
                
                # Set new width to be the maximum of text width and image width
                new_width = max(text_width, current_size.width())
                
                # Add extra height for the text if needed
                text_height = font_metrics.height() * (text.count('\n') + 1) + 20
                new_height = current_size.height() + text_height
                
                # Resize the window
                self.setFixedSize(new_width, new_height)
                
                # Re-center the window
                self._center_on_screen()
    
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


class OutputWindow(QDialog):
    """Window that displays real-time CLI output in a non-editable text field."""

    def __init__(self, parent, title="Output"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(700, 450)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)

        # Read-only text area for output
        self.output_text = QPlainTextEdit(self)
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #3c3c3c;
                padding: 8px;
            }
        """)
        layout.addWidget(self.output_text)

        # Close button (disabled until operation completes)
        self.close_button = QPushButton("Close", self)
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        # Center the window
        self._center_on_screen()

    def _center_on_screen(self):
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def append_output(self, text):
        """Append text and auto-scroll to bottom."""
        self.output_text.appendPlainText(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def enable_close(self):
        """Enable the close button when operation is complete."""
        self.close_button.setEnabled(True)

    def set_status(self, message, is_error=False):
        """Set a status message with optional error styling."""
        if is_error:
            self.append_output(f"\n--- ERROR: {message} ---")
        else:
            self.append_output(f"\n--- {message} ---")


# -------------------------------------------------------------------------
# Stellar Dialog Classes
# -------------------------------------------------------------------------

class StellarUserPasswordDialog(QDialog):
    """Dialog for entering account name and password with Stellar branding."""

    def __init__(self, parent, title, message, icon_path=None, default_user=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Account name field
        layout.addWidget(QLabel("Account Name:"))
        self.account_edit = QLineEdit(self)
        self.account_edit.setText(default_user)
        layout.addWidget(self.account_edit)

        # Password field
        layout.addWidget(QLabel("Passphrase:"))
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def get_values(self):
        return {'user': self.account_edit.text(), 'password': self.password_edit.text()}


class StellarPasswordDialog(QDialog):
    """Dialog for entering password only with Stellar branding."""

    def __init__(self, parent, title, message, icon_path=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Password field
        layout.addWidget(QLabel("Passphrase:"))
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def get_password(self):
        return self.password_edit.text()


class StellarAccountSelectDialog(QDialog):
    """Dialog for selecting a Stellar account from a dropdown."""

    def __init__(self, parent, title, message, accounts, icon_path=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Account dropdown
        self.combo = QComboBox(self)
        for account in accounts:
            self.combo.addItem(account)
        layout.addWidget(self.combo)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def get_selected(self):
        return self.combo.currentText()


class StellarCopyTextDialog(QDialog):
    """Dialog for displaying text with a copy button (for seed phrases)."""

    def __init__(self, parent, title, message, text_to_copy, icon_path=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.text_to_copy = text_to_copy

        layout = QVBoxLayout(self)

        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Text display (read-only)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setPlainText(text_to_copy)
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(100)
        layout.addWidget(self.text_edit)

        # Copy button
        copy_btn = QPushButton("Copy to Clipboard", self)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        layout.addWidget(copy_btn)

        # OK button
        ok_btn = QPushButton("OK", self)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_to_copy)


class StellarMessageDialog(QDialog):
    """Simple message dialog with Stellar branding."""

    def __init__(self, parent, title, message, icon_path=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)


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
        self.DIDC = self.platform_manager.get_didc_path()
        self.PRESS = self.platform_manager.get_press_path()
        self.BLENDER_PATH = self.platform_manager.get_blender_path()
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
        self.DOCKER_INSTALLED = False
        self.PINTHEON_INSTALLED = False
        self.TUNNEL_TOKEN = ''

        # Initialize these before _update_install_stats()
        self.PINTHEON_NETWORK = 'testnet'
        self.PINTHEON_PORT = 9998
        self.PINGGY_TIER = 'free'

        self._update_install_stats()
        self.PINTHEON_ACTIVE = False

        # Initialize API server
        self.api_server = None
        self.API_PORT = self._get_api_port()
        self.API_ACTIVE = False
        if HAS_API_SERVER:
            self._start_api_server()
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

        # API Server actions
        self.api_status_action = QAction("Status: Stopped", self)
        self.api_status_action.setEnabled(False)

        self.api_open_docs_action = QAction(self.web_icon, "Open API Docs", self)
        self.api_open_docs_action.triggered.connect(self._open_api_docs)
        self.api_open_docs_action.setVisible(False)

        self.api_restart_action = QAction(self.cog_icon, "Restart API Server", self)
        self.api_restart_action.triggered.connect(self._restart_api_server)
        self.api_restart_action.setVisible(False)

        self.api_port_action = QAction(self.cog_icon, "Change Port...", self)
        self.api_port_action.triggered.connect(self._change_api_port)

        # Wallet Management actions
        self.wallet_manage_action = QAction(self.stellar_icon, "Manage Wallets", self)
        self.wallet_manage_action.triggered.connect(self._open_wallet_manager)
        
        self.wallet_create_action = QAction(self.stellar_icon, "Create Wallet", self)
        self.wallet_create_action.triggered.connect(self._create_wallet)
        
        self.wallet_recover_action = QAction(self.stellar_icon, "Recover Wallet", self)
        self.wallet_recover_action.triggered.connect(self._recover_wallet)
        
        self.soroban_deployments_action = QAction(self.stellar_icon, "Soroban Deployments", self)
        self.soroban_deployments_action.triggered.connect(self._show_soroban_deployments)

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
        quit_action.triggered.connect(self._quit_application)

        test_action = QAction("TEST", self)
        test_action.triggered.connect(self.test_process)
        
        test_animated_action = QAction("TEST ANIMATED", self)
        test_animated_action.triggered.connect(self.test_animated_process)

        tray_menu = QMenu()

        self.tray_tools_menu = tray_menu.addMenu("Tools")

        # self.tray_tools_menu.addAction(test_animated_action)


        self.tray_tools_update_menu = self.tray_tools_menu.addMenu("Installations")
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

        # Refresh Pintheon UI state
        self._refresh_pintheon_ui_state()

        # Add Metadata API menu if available
        if HAS_API_SERVER:
            self._setup_api_menu(tray_menu)

        # Add Wallet Management menu if available
        if HAS_WALLET_MANAGER:
            self._setup_wallet_menu(tray_menu)

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

    def _update_install_stats(self):
        # Use direct implementation (no CLI dependency)
        self.INSTALL_STATS = self._get_installation_stats()
        self.DOCKER_INSTALLED = self.INSTALL_STATS['docker_installed']
        self.PINTHEON_INSTALLED = self.INSTALL_STATS['pintheon_image_exists']
        # Note: TUNNEL_TOKEN is now managed locally, not from CLI

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
            self.tray_pintheon_menu.setVisible(True)

    def _setup_press_menu(self):
        if not hasattr(self, 'tray_press_menu') or self.tray_press_menu is None:
            self.tray_press_menu = self.tray_tools_menu.addMenu("Press")
            self.tray_press_menu.setIcon(self.press_icon)
            self.tray_press_menu.addAction(self.run_press_action)
            self.tray_press_menu.setVisible(True)

    # =========================================================================
    # API Server Methods
    # =========================================================================

    def _get_api_port(self) -> int:
        """Get API port from database config or use default."""
        try:
            result = self.DB.search(self.QUERY.type == 'app_data')
            if result and 'api_port' in result[0]:
                return result[0]['api_port']
        except Exception:
            pass
        return 7777  # Default port

    def _set_api_port(self, port: int):
        """Save API port to database config."""
        try:
            self.DB.update({'api_port': port}, self.QUERY.type == 'app_data')
            self.API_PORT = port
        except Exception as e:
            logging.error(f"Failed to save API port: {e}")

    def _setup_api_menu(self, tray_menu):
        """Set up the Metadata API submenu in the system tray."""
        self.tray_api_menu = tray_menu.addMenu("Metadata API")
        self.tray_api_menu.setIcon(self.web_icon)

        self.tray_api_menu.addAction(self.api_status_action)
        self.tray_api_menu.addSeparator()
        self.tray_api_menu.addAction(self.api_open_docs_action)
        self.tray_api_menu.addAction(self.api_restart_action)
        self.tray_api_menu.addAction(self.api_port_action)

    def _setup_wallet_menu(self, tray_menu):
        """Set up the Wallet Management submenu in the system tray."""
        self.tray_wallet_menu = tray_menu.addMenu("Wallet Management")
        self.tray_wallet_menu.setIcon(self.stellar_icon)

        self.tray_wallet_menu.addAction(self.wallet_manage_action)
        self.tray_wallet_menu.addSeparator()
        self.tray_wallet_menu.addAction(self.wallet_create_action)
        self.tray_wallet_menu.addAction(self.wallet_recover_action)
        self.tray_wallet_menu.addSeparator()
        self.tray_wallet_menu.addAction(self.soroban_deployments_action)

    def _start_api_server(self):
        """Start the local metadata API server."""
        if not HAS_API_SERVER:
            logging.warning("API server not available (FastAPI not installed)")
            return

        if self.api_server and self.api_server.isRunning():
            logging.info("API server already running")
            return

        self.api_server = ApiServerWorker(port=self.API_PORT, parent=self)
        self.api_server.started_signal.connect(self._on_api_started)
        self.api_server.stopped_signal.connect(self._on_api_stopped)
        self.api_server.error_signal.connect(self._on_api_error)
        self.api_server.start()
        logging.info(f"Starting HEAVYMETADATA API server on port {self.API_PORT}")

    def _stop_api_server(self):
        """Stop the API server gracefully."""
        if self.api_server and self.api_server.isRunning():
            self.api_server.stop()
            self.api_server.wait(5000)  # Wait up to 5 seconds
            logging.info("HEAVYMETADATA API server stopped")

    def _restart_api_server(self):
        """Restart the API server."""
        self._stop_api_server()
        self._start_api_server()

    def _on_api_started(self):
        """Handle API server started signal."""
        self.API_ACTIVE = True
        self.api_status_action.setText(f"Status: Running (port {self.API_PORT})")
        self.api_open_docs_action.setVisible(True)
        self.api_restart_action.setVisible(True)
        logging.info(f"HEAVYMETADATA API started on http://127.0.0.1:{self.API_PORT}")

    def _on_api_stopped(self):
        """Handle API server stopped signal."""
        self.API_ACTIVE = False
        self.api_status_action.setText("Status: Stopped")
        self.api_open_docs_action.setVisible(False)
        self.api_restart_action.setVisible(False)

    def _on_api_error(self, error: str):
        """Handle API server error signal."""
        self.API_ACTIVE = False
        self.api_status_action.setText(f"Status: Error")
        self.api_open_docs_action.setVisible(False)
        self.api_restart_action.setVisible(False)
        logging.error(f"HEAVYMETADATA API error: {error}")
        QMessageBox.warning(self, "API Server Error", f"Failed to start Metadata API server:\n{error}")

    def _open_api_docs(self):
        """Open the API documentation in browser."""
        webbrowser.open(f"http://127.0.0.1:{self.API_PORT}/docs")

    def _change_api_port(self):
        """Show dialog to change API server port."""
        port, ok = QInputDialog.getInt(
            self,
            "Change API Port",
            "Enter new port number:",
            self.API_PORT,
            1024,  # Min port
            65535,  # Max port
            1  # Step
        )
        if ok and port != self.API_PORT:
            self._set_api_port(port)
            if self.API_ACTIVE:
                reply = QMessageBox.question(
                    self,
                    "Restart API Server",
                    f"Port changed to {port}. Restart the API server now?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self._restart_api_server()
            else:
                QMessageBox.information(
                    self,
                    "Port Changed",
                    f"API port changed to {port}. It will be used on next server start."
                )

    # =========================================================================
    # Wallet Management Methods
    # =========================================================================

    def _open_wallet_manager(self):
        """Open the wallet management window."""
        if not HAS_WALLET_MANAGER:
            QMessageBox.warning(self, "Wallet Manager Not Available", 
                              "Wallet management is not available. Please ensure wallet_manager.py is present.")
            return
        
        # Create and show wallet manager dialog
        dialog = WalletManagerDialog(self)
        dialog.exec_()

    def _create_wallet(self):
        """Create a new wallet with network selection."""
        if not HAS_WALLET_MANAGER:
            QMessageBox.warning(self, "Wallet Manager Not Available", 
                              "Wallet management is not available. Please ensure wallet_manager.py is present.")
            return
        
        # Create unified wallet creation dialog
        dialog = WalletCreationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            network = dialog.get_network()
            label = dialog.get_label()
            password = dialog.get_password()
            
            try:
                wallet_manager = WalletManager()
                
                if network == "testnet":
                    wallet = wallet_manager.create_testnet_wallet(label=label)
                    # Get the actual secret key (testnet wallets store plaintext)
                    secret_key = wallet.secret_key
                else:  # mainnet
                    wallet, unencrypted_secret = wallet_manager.create_mainnet_wallet(label=label, password=password)
                    secret_key = unencrypted_secret
                
                # Generate seed phrase
                seed_phrase = wallet_manager.generate_seed_phrase(secret_key)
                
                # Show wallet details dialog
                details_dialog = WalletDetailsDialog(
                    self, 
                    wallet=wallet, 
                    secret_key=secret_key, 
                    seed_phrase=seed_phrase
                )
                details_dialog.exec_()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Wallet Creation Failed",
                    f"Failed to create {network} wallet:\n{str(e)}"
                )

    def _recover_wallet(self):
        """Recover a wallet from secret key."""
        if not HAS_WALLET_MANAGER:
            QMessageBox.warning(self, "Wallet Manager Not Available", 
                              "Wallet management is not available. Please ensure wallet_manager.py is present.")
            return
        
        # Create recovery dialog
        dialog = WalletRecoveryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            secret_key = dialog.get_secret_key()
            network = dialog.get_network()
            label = dialog.get_label()
            password = dialog.get_password()
            
            try:
                wallet_manager = WalletManager()
                wallet = wallet_manager.recover_wallet_from_secret(
                    secret_key=secret_key,
                    network=network,
                    label=label,
                    password=password
                )
                
                QMessageBox.information(
                    self,
                    "Wallet Recovered",
                    f"Wallet recovered successfully!\n\n"
                    f"Address: {wallet.address}\n"
                    f"Network: {wallet.network}\n"
                    f"Label: {wallet.label}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Wallet Recovery Failed",
                    f"Failed to recover wallet:\n{str(e)}"
                )

    def _show_soroban_deployments(self):
        """Show Soroban deployments for current network."""
        try:
            # Import deployment list dialog
            from ui.soroban.deployment_list_dialog import DeploymentListDialog
            
            # Get current network (default to testnet)
            current_network = "testnet"  # This could be made configurable
            
            # Show deployment list dialog
            deployment_dialog = DeploymentListDialog(self, network=current_network)
            deployment_dialog.exec_()
            
        except ImportError:
            QMessageBox.warning(
                self, 
                "Soroban Deployments Not Available",
                "Soroban deployment management is not available. Please ensure the UI components are properly installed."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening Deployments",
                f"Failed to open Soroban deployments: {str(e)}"
            )

    def _quit_application(self):
        """Clean shutdown of the application."""
        # Stop API server
        if HAS_API_SERVER and self.api_server:
            self._stop_api_server()

        # Call the original quit
        qApp.quit()

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

    # =========================================================================
    # Direct Stellar Operations (no CLI dependency)
    # =========================================================================

    def _get_stellar_accounts_table(self):
        """Get or create the Stellar accounts table in the database."""
        return self.DB.table('stellar_accounts')

    def _get_stellar_account_names(self):
        """Get list of all Stellar account names."""
        table = self._get_stellar_accounts_table()
        return [acct['name'] for acct in table.all()]

    def _get_active_stellar_account(self):
        """Get the currently active Stellar account."""
        table = self._get_stellar_accounts_table()
        results = table.search(self.QUERY.active == True)
        return results[0] if results else None

    def _hash_password(self, password):
        """Hash a password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password, stored_hash):
        """Verify a password against a stored hash."""
        return self._hash_password(password) == stored_hash

    def new_stellar_account(self):
        """Create a new Stellar account directly (no CLI dependency)."""
        if not HAS_STELLAR_SDK:
            self.open_msg_dialog("Stellar SDK not installed. Please install stellar-sdk package.")
            return

        # Show user/password dialog
        dialog = StellarUserPasswordDialog(
            self, "New Stellar Account",
            "Enter a name and passphrase for your new Stellar account.\n\nIMPORTANT: Remember this passphrase - it protects your account!",
            self.STELLAR_LOGO_IMG
        )
        if not dialog.exec():
            return

        values = dialog.get_values()
        account_name = values['user'].strip()
        password = values['password']

        if not account_name:
            self.open_msg_dialog("Account name cannot be empty.")
            return

        if not password:
            self.open_msg_dialog("Passphrase cannot be empty.")
            return

        # Check if account name already exists
        table = self._get_stellar_accounts_table()
        if table.search(self.QUERY.name == account_name):
            self.open_msg_dialog("An account with this name already exists.")
            return

        # Confirm password
        confirm_dialog = StellarPasswordDialog(
            self, "Confirm Passphrase",
            "Please confirm your passphrase.",
            self.STELLAR_LOGO_IMG
        )
        if not confirm_dialog.exec():
            return

        if confirm_dialog.get_password() != password:
            self.open_msg_dialog("Passphrases do not match.")
            return

        try:
            # Generate Stellar keypair
            keypair = StellarKeypair.random()
            seed = keypair.secret

            # Generate 25519 keypair from Stellar keypair
            keypair_25519 = Stellar25519KeyPair(keypair)

            # Set all existing accounts to inactive
            table.update({'active': False})

            # Store the new account
            account_data = {
                'data_type': 'STELLAR_ID',
                'name': account_name,
                'public': keypair.public_key,
                '25519_pub': keypair_25519.public_key(),
                'active': True,
                'pw_hash': self._hash_password(password),
                'network': 'mainnet'
            }
            table.insert(account_data)

            # Show seed phrase - CRITICAL for user to save
            seed_dialog = StellarCopyTextDialog(
                self, "Save Your Seed Phrase",
                "Your Stellar account has been created!\n\n"
                "CRITICAL: Copy and securely store this seed phrase.\n"
                "It is the ONLY way to recover your account. Never share it!",
                seed,
                self.STELLAR_LOGO_IMG
            )
            seed_dialog.exec()

        except Exception as e:
            self.open_msg_dialog(f"Error creating Stellar account: {str(e)}")

    def change_stellar_account(self):
        """Change the active Stellar account directly (no CLI dependency)."""
        accounts = self._get_stellar_account_names()

        if not accounts:
            self.open_msg_dialog("No Stellar accounts found. Create one first.")
            return

        # Show account selection dialog
        dialog = StellarAccountSelectDialog(
            self, "Select Stellar Account",
            "Choose which Stellar account to make active.",
            accounts,
            self.STELLAR_LOGO_IMG
        )
        if not dialog.exec():
            return

        selected = dialog.get_selected()
        if not selected:
            return

        # Update active status
        table = self._get_stellar_accounts_table()
        table.update({'active': False})
        table.update({'active': True}, self.QUERY.name == selected)

        self.open_msg_dialog(f"Active account changed to: {selected}")

    def remove_stellar_account(self):
        """Remove a Stellar account directly (no CLI dependency)."""
        accounts = self._get_stellar_account_names()

        if not accounts:
            self.open_msg_dialog("No Stellar accounts found.")
            return

        # Show account selection dialog
        dialog = StellarAccountSelectDialog(
            self, "Remove Stellar Account",
            "Select the Stellar account to remove.\n\nWARNING: This cannot be undone!",
            accounts,
            self.STELLAR_LOGO_IMG
        )
        if not dialog.exec():
            return

        selected = dialog.get_selected()
        if not selected:
            return

        # Verify password
        table = self._get_stellar_accounts_table()
        account = table.get(self.QUERY.name == selected)

        if not account:
            self.open_msg_dialog("Account not found.")
            return

        pw_dialog = StellarPasswordDialog(
            self, "Verify Passphrase",
            f"Enter the passphrase for '{selected}' to confirm removal.",
            self.STELLAR_LOGO_IMG
        )
        if not pw_dialog.exec():
            return

        if not self._verify_password(pw_dialog.get_password(), account.get('pw_hash', '')):
            self.open_msg_dialog("Incorrect passphrase.")
            return

        # Remove the account
        was_active = account.get('active', False)
        table.remove(self.QUERY.name == selected)

        # If removed account was active, set another as active
        remaining = table.all()
        if was_active and remaining:
            table.update({'active': True}, doc_ids=[remaining[0].doc_id])
            self.open_msg_dialog(f"'{selected}' removed. Active account is now: {remaining[0]['name']}")
        elif remaining:
            self.open_msg_dialog(f"'{selected}' has been removed.")
        else:
            self.open_msg_dialog("All Stellar accounts have been removed.")

    def new_stellar_testnet_account(self):
        """Create a new Stellar testnet account with funding (no CLI dependency)."""
        if not HAS_STELLAR_SDK:
            self.open_msg_dialog("Stellar SDK not installed. Please install stellar-sdk package.")
            return

        # Show user/password dialog
        dialog = StellarUserPasswordDialog(
            self, "New Stellar Testnet Account",
            "Enter a name and passphrase for your new Stellar testnet account.\n\n"
            "This account will be automatically funded via Friendbot.",
            self.STELLAR_LOGO_IMG
        )
        if not dialog.exec():
            return

        values = dialog.get_values()
        account_name = values['user'].strip()
        password = values['password']

        if not account_name:
            self.open_msg_dialog("Account name cannot be empty.")
            return

        if not password:
            self.open_msg_dialog("Passphrase cannot be empty.")
            return

        # Check if account name already exists
        table = self._get_stellar_accounts_table()
        if table.search(self.QUERY.name == account_name):
            self.open_msg_dialog("An account with this name already exists.")
            return

        # Confirm password
        confirm_dialog = StellarPasswordDialog(
            self, "Confirm Passphrase",
            "Please confirm your passphrase.",
            self.STELLAR_LOGO_IMG
        )
        if not confirm_dialog.exec():
            return

        if confirm_dialog.get_password() != password:
            self.open_msg_dialog("Passphrases do not match.")
            return

        try:
            # Generate Stellar keypair
            keypair = StellarKeypair.random()
            seed = keypair.secret

            # Generate 25519 keypair from Stellar keypair
            keypair_25519 = Stellar25519KeyPair(keypair)

            # Fund via Friendbot
            funding_success = False
            funding_message = ""
            try:
                friendbot_url = f"https://horizon-testnet.stellar.org/friendbot?addr={keypair.public_key}"
                response = requests.get(friendbot_url, timeout=30)
                if response.status_code == 200:
                    funding_success = True
                    funding_message = "Account funded with 10,000 test XLM!"
                else:
                    funding_message = f"Friendbot funding failed (status {response.status_code})"
            except Exception as e:
                funding_message = f"Friendbot funding error: {str(e)}"

            # Set all existing accounts to inactive
            table.update({'active': False})

            # Store the new account
            account_data = {
                'data_type': 'STELLAR_ID',
                'name': account_name,
                'public': keypair.public_key,
                '25519_pub': keypair_25519.public_key(),
                'active': True,
                'pw_hash': self._hash_password(password),
                'network': 'testnet'
            }
            table.insert(account_data)

            # Build result message
            result_msg = "Your Stellar testnet account has been created!\n\n"
            if funding_success:
                result_msg += f"✓ {funding_message}\n\n"
            else:
                result_msg += f"⚠ {funding_message}\n\n"
            result_msg += "CRITICAL: Copy and securely store this seed phrase.\n"
            result_msg += "It is the ONLY way to recover your account!"

            # Show seed phrase
            seed_dialog = StellarCopyTextDialog(
                self, "Save Your Seed Phrase",
                result_msg,
                seed,
                self.STELLAR_LOGO_IMG
            )
            seed_dialog.exec()

        except Exception as e:
            self.open_msg_dialog(f"Error creating Stellar testnet account: {str(e)}")

    # =========================================================================
    # Direct Pintheon Operations (no CLI dependency)
    # =========================================================================

    def _check_docker_installed(self):
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'Docker version' in result.stdout
        except Exception:
            return False

    def _docker_container_exists(self, name):
        """Check if a Docker container with the given name exists."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name=^{name}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == name
        except Exception:
            return False

    def _docker_container_running(self, name):
        """Check if a Docker container is currently running."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name=^{name}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == name
        except Exception:
            return False

    def _docker_image_exists(self, image_name):
        """Check if a Docker image exists locally."""
        try:
            result = subprocess.run(
                ['docker', 'images', '-q', image_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _get_pintheon_image_name(self):
        """Get the full Pintheon Docker image name for the current architecture."""
        machine = platform.machine().lower()
        if machine in ('x86_64', 'amd64', 'intel64', 'i386', 'i686'):
            arch = 'linux-amd64'
        elif machine in ('aarch64', 'arm64', 'armv8', 'armv7l', 'arm'):
            arch = 'linux-arm64'
        else:
            arch = f'linux-{machine}'
        return f'metavinci/pintheon-{self.PINTHEON_NETWORK}-{arch}:latest'

    def _get_docker_volume_path(self, local_path):
        """Get cross-platform Docker volume path."""
        path_str = str(local_path)
        if platform.system().lower() == 'windows':
            # Convert Windows path to Docker-compatible format: C:\Users\... -> /c/Users/...
            if len(path_str) >= 2 and path_str[1] == ':':
                drive = path_str[0].lower()
                rest = path_str[2:].replace('\\', '/')
                return f"/{drive}{rest}"
        return path_str

    def _pintheon_image_exists(self):
        """Check if the Pintheon Docker image exists locally."""
        image_name = self._get_pintheon_image_name()
        return self._docker_image_exists(image_name)

    def _start_pintheon_direct(self):
        """Start Pintheon container directly without CLI."""
        try:
            if self._docker_container_exists('pintheon'):
                # Container exists, just start it
                result = subprocess.run(
                    ['docker', 'start', 'pintheon'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.returncode == 0
            else:
                # Container doesn't exist, create and run it
                port = getattr(self, 'PINTHEON_PORT', 9998)
                data_dir = Path.home() / 'pintheon_data'
                data_dir.mkdir(parents=True, exist_ok=True)
                volume_path = self._get_docker_volume_path(data_dir)
                image_name = self._get_pintheon_image_name()

                command = [
                    'docker', 'run', '-d',
                    '--name', 'pintheon',
                    '--dns=8.8.8.8',
                    '--network', 'bridge',
                    '-p', f'{port}:{port}/tcp',
                    '-p', '9999:9999/tcp',
                    '-v', f'{volume_path}:/home/pintheon/data',
                    image_name
                ]

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=str(Path.home()),
                    timeout=60
                )
                return result.returncode == 0
        except Exception as e:
            logging.error(f"Error starting Pintheon: {e}")
            return False

    def _stop_pintheon_direct(self):
        """Stop Pintheon container directly without CLI."""
        try:
            result = subprocess.run(
                ['docker', 'stop', 'pintheon'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error stopping Pintheon: {e}")
            return False

    def _open_pintheon_admin(self):
        """Open Pintheon admin interface in browser."""
        port = getattr(self, 'PINTHEON_PORT', 9998)
        webbrowser.open(f'https://127.0.0.1:9999/admin')

    def _open_pintheon_homepage(self):
        """Open Pintheon homepage in browser."""
        port = getattr(self, 'PINTHEON_PORT', 9998)
        webbrowser.open(f'https://127.0.0.1:{port}/')

    def _get_installation_stats(self):
        """Get installation statistics without CLI dependency."""
        return {
            'docker_installed': self._check_docker_installed(),
            'pintheon_image_exists': self._pintheon_image_exists(),
            'pintheon_container_exists': self._docker_container_exists('pintheon'),
            'pintheon_running': self._docker_container_running('pintheon'),
            'pinggy_tier': getattr(self, 'PINGGY_TIER', 'free'),
            'pinggy_token': getattr(self, 'TUNNEL_TOKEN', ''),
            'pintheon_network': getattr(self, 'PINTHEON_NETWORK', 'testnet'),
        }

    # =========================================================================
    # Direct Tunnel Operations (no CLI dependency)
    # =========================================================================

    def _get_pinggy_path(self):
        """Get platform-specific Pinggy executable path."""
        home = Path.home()
        system = platform.system().lower()
        if system == 'windows':
            return home / 'AppData' / 'Local' / 'pinggy' / 'pinggy.exe'
        elif system == 'darwin':
            return home / '.local' / 'share' / 'pinggy' / 'pinggy'
        else:  # Linux
            return home / '.local' / 'share' / 'pinggy' / 'pinggy'

    def _is_tunnel_open(self):
        """Check if Pinggy tunnel is running by accessing the web debugger."""
        try:
            response = requests.get("http://localhost:4300", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _open_tunnel_direct(self):
        """Open Pinggy tunnel in a new terminal window."""
        # Check if token is configured
        if not self.TUNNEL_TOKEN or len(self.TUNNEL_TOKEN) < 7:
            self.open_msg_dialog('Pinggy token not configured. Please set your token first.')
            return False

        # Check if tunnel is already open
        if self._is_tunnel_open():
            self.open_msg_dialog('Tunnel is already running.')
            return True

        # Get pinggy path
        pinggy_path = self._get_pinggy_path()
        if not pinggy_path.exists():
            self.open_msg_dialog('Pinggy not installed. Please install Pintheon first.')
            return False

        # Build pinggy command
        port = getattr(self, 'PINTHEON_PORT', 9998)
        tier = getattr(self, 'PINGGY_TIER', 'free')
        token = self.TUNNEL_TOKEN

        pinggy_command = f'"{pinggy_path}" -p 443 -R0:localhost:{port} -L4300:localhost:4300 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -t {token}@{tier}.pinggy.io x:https x:localServerTls:localhost x:passpreflight'

        try:
            system = platform.system().lower()

            if system == 'windows':
                # Open in new cmd window
                cmd = f'start "Pintheon Tunnel" cmd /k {pinggy_command}'
                subprocess.Popen(cmd, shell=True)
            elif system == 'darwin':
                # Open in Terminal.app
                escaped_cmd = pinggy_command.replace('"', '\\"')
                apple_script = f'tell app "Terminal" to do script "{escaped_cmd}"'
                subprocess.Popen(['osascript', '-e', apple_script])
            else:  # Linux
                # Try xterm first, then gnome-terminal
                if shutil.which('xterm'):
                    subprocess.Popen(['xterm', '-title', 'Pintheon Tunnel', '-e', 'bash', '-c', pinggy_command])
                elif shutil.which('gnome-terminal'):
                    subprocess.Popen(['gnome-terminal', '--title=Pintheon Tunnel', '--', 'bash', '-c', pinggy_command])
                else:
                    # Fallback - run in background
                    subprocess.Popen(pinggy_command, shell=True)

            logging.info("Tunnel started successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to start tunnel: {e}")
            self.open_msg_dialog(f'Failed to start tunnel: {e}')
            return False

    def _set_tunnel_token_direct(self):
        """Show dialog to set Pinggy tunnel token."""
        current_token = getattr(self, 'TUNNEL_TOKEN', '')

        token, ok = QInputDialog.getText(
            self,
            'Set Pinggy Token',
            'Enter your Pinggy authentication token:',
            QLineEdit.Normal,
            current_token
        )

        if ok and token:
            self.TUNNEL_TOKEN = token.strip()
            # Update visibility of tunnel action
            if len(self.TUNNEL_TOKEN) >= 7:
                self.open_tunnel_action.setVisible(self.PINTHEON_ACTIVE)
            else:
                self.open_tunnel_action.setVisible(False)
            self.open_msg_dialog('Pinggy token saved successfully.')
            return True
        return False

    def _set_tunnel_tier_direct(self):
        """Show dialog to select Pinggy tunnel tier."""
        tiers = ['pro', 'free']
        current_tier = getattr(self, 'PINGGY_TIER', 'free')

        # Set current tier as default selection
        current_index = tiers.index(current_tier) if current_tier in tiers else 1

        tier, ok = QInputDialog.getItem(
            self,
            'Set Pinggy Tier',
            'Select your Pinggy subscription tier:',
            tiers,
            current_index,
            False  # Not editable
        )

        if ok and tier:
            self.PINGGY_TIER = tier
            self.open_msg_dialog(f'Pinggy tier set to: {tier}')
            return True
        return False

    def _set_pintheon_network_direct(self):
        """Show dialog to select Pintheon network."""
        networks = ['testnet', 'mainnet']
        current_network = getattr(self, 'PINTHEON_NETWORK', 'testnet')

        current_index = networks.index(current_network) if current_network in networks else 0

        network, ok = QInputDialog.getItem(
            self,
            'Set Pintheon Network',
            'Select network (requires re-installing Pintheon):',
            networks,
            current_index,
            False  # Not editable
        )

        if ok and network:
            if network != current_network:
                self.PINTHEON_NETWORK = network
                self.open_msg_dialog(f'Network set to: {network}\n\nNote: You need to re-install Pintheon for this to take effect.')
            return True
        return False

    # =========================================================================

    def update_tools(self):
        update = self.open_confirm_dialog('You want to update Heavymeta Tools?')
        if update == True:
            self._update_blender_addon(self.BLENDER_VERSION)
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
        # All Pintheon and Stellar operations now work directly without CLI
        pass

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
        """Install Pintheon directly without CLI dependency."""
        install = self.open_confirm_dialog('Install Pintheon?')
        if install == True:
            # Create output window to show real-time progress
            output_window = OutputWindow(self, 'Installing Pintheon')
            output_window.show()
            output_window.raise_()
            output_window.activateWindow()
            QApplication.processEvents()

            # Create the direct setup worker (no CLI dependency)
            worker = PintheonSetupWorker()

            # Connect signals for real-time output
            worker.output_line.connect(output_window.append_output)
            worker.finished.connect(lambda: self._on_pintheon_setup_finished(output_window, worker))
            worker.error.connect(lambda error_msg: self._on_pintheon_setup_error(output_window, worker, error_msg))
            worker.success.connect(lambda success_msg: self._on_pintheon_setup_success(output_window, worker, success_msg))

            # Start the worker thread
            worker.start()

            # Store references to prevent garbage collection
            self._current_output_window = output_window
            self._current_worker = worker

    def _on_pintheon_setup_finished(self, output_window, worker):
        """Handle setup completion."""
        output_window.enable_close()
        worker.deleteLater()

    def _on_pintheon_setup_error(self, output_window, worker, error_msg):
        """Handle setup error."""
        output_window.set_status(error_msg, is_error=True)
        output_window.enable_close()

    def _on_pintheon_setup_success(self, output_window, worker, success_msg):
        """Handle successful Pintheon setup."""
        self.PINTHEON_INSTALLED = True
        self.DOCKER_INSTALLED = True
        self._refresh_pintheon_ui_state()
        output_window.enable_close()

    def _update_ui_on_press_installed(self):
        """Update UI to reflect hvym_press availability after installation."""
        # Toggle install/update visibility
        self.install_press_action.setVisible(False)
        self.update_press_action.setVisible(True)
        # Refresh press UI state based on actual installation
        self._refresh_press_ui_state()
        
    def _refresh_pintheon_ui_state(self):
        self._setup_pintheon_menu()
        self._update_install_stats()
        self.PINTHEON_NETWORK = self.INSTALL_STATS['pintheon_network']
        
        if self.DOCKER_INSTALLED == True:
            self.PINTHEON_INSTALLED = self.INSTALL_STATS['pintheon_image_exists']

            if self.PINTHEON_INSTALLED:
                network_name = 'testnet'
        
                if self.PINTHEON_NETWORK and 'mainnet' in self.PINTHEON_NETWORK:
                    network_name = 'mainnet'
                
                # Only try to update the menu if it exists
                if hasattr(self, 'tray_pintheon_menu') and self.tray_pintheon_menu is not None:
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
            # Use direct Docker command (no CLI dependency)
            if self._start_pintheon_direct():
                self.PINTHEON_ACTIVE = True
                self._update_ui_on_pintheon_started()
                self._open_pintheon_admin()
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
            # Use direct Docker command (no CLI dependency)
            if self._stop_pintheon_direct():
                self.PINTHEON_ACTIVE = False
                self._update_ui_on_pintheon_stopped()
            else:
                self.open_msg_dialog('Failed to stop Pintheon. Check logs for details.')

    def _open_pintheon(self):
        open_it = self.open_confirm_dialog('Open Pintheon Admin Interface?')
        if open_it:
            self._open_pintheon_admin()

    def _open_homepage(self):
        open_it = self.open_confirm_dialog('Open Local Homepage?')
        if open_it:
            self._open_pintheon_homepage()
        
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
        if expose:
            # Use direct implementation (no CLI dependency)
            self._open_tunnel_direct()

    def _set_tunnel_token(self):
        # Use direct implementation with Qt dialog (no CLI dependency)
        self._set_tunnel_token_direct()

    def _set_tunnel_tier(self):
        # Use direct implementation with Qt dialog (no CLI dependency)
        self._set_tunnel_tier_direct()
        self._refresh_pintheon_ui_state()

    def _set_pintheon_network(self):
        # Use direct implementation with Qt dialog (no CLI dependency)
        self._set_pintheon_network_direct()
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


# ============================================================================
# Wallet Management Dialog Classes
# ============================================================================

class WalletManagerDialog(QDialog):
    """Dialog for managing wallets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallet Manager")
        self.setMinimumSize(600, 400)
        self.wallet_manager = WalletManager()
        
        layout = QVBoxLayout(self)
        
        # Wallet list
        self.wallet_list = QListWidget()
        layout.addWidget(QLabel("Your Wallets:"))
        layout.addWidget(self.wallet_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_wallets)
        button_layout.addWidget(self.refresh_btn)
        
        self.fund_btn = QPushButton("Fund Testnet")
        self.fund_btn.clicked.connect(self.fund_selected_wallet)
        button_layout.addWidget(self.fund_btn)
        
        self.copy_btn = QPushButton("Copy Address")
        self.copy_btn.clicked.connect(self.copy_selected_address)
        button_layout.addWidget(self.copy_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_wallet)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Load initial wallets
        self.refresh_wallets()
        
        # Enable/disable buttons based on selection
        self.wallet_list.itemSelectionChanged.connect(self.update_buttons)
        self.update_buttons()
    
    def refresh_wallets(self):
        """Refresh the wallet list."""
        self.wallet_list.clear()
        
        try:
            # Get testnet wallets
            testnet_wallets = self.wallet_manager.list_testnet_wallets()
            for wallet in testnet_wallets:
                item = QListWidgetItem(f"Testnet: {wallet.label} - {wallet.address[:8]}...")
                item.setData(32, wallet)  # Qt.UserRole = 32
                self.wallet_list.addItem(item)
            
            # Get mainnet wallets
            mainnet_wallets = self.wallet_manager.list_mainnet_wallets()
            for wallet in mainnet_wallets:
                item = QListWidgetItem(f"Mainnet: {wallet.label} - {wallet.address[:8]}...")
                item.setData(32, wallet)  # Qt.UserRole = 32
                self.wallet_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load wallets: {str(e)}")
    
    def update_buttons(self):
        """Update button states based on selection."""
        has_selection = bool(self.wallet_list.currentItem())
        self.fund_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # Only enable fund button for testnet wallets
        if has_selection:
            wallet = self.wallet_list.currentItem().data(32)
            self.fund_btn.setEnabled(wallet.network == "testnet")
    
    def fund_selected_wallet(self):
        """Fund the selected testnet wallet."""
        item = self.wallet_list.currentItem()
        if not item:
            return
        
        wallet = item.data(32)
        if wallet.network != "testnet":
            return
        
        try:
            result = self.wallet_manager.fund_testnet_wallet(wallet.address)
            if result.get("success"):
                QMessageBox.information(self, "Success", "Wallet funded successfully!")
            else:
                QMessageBox.warning(self, "Failed", "Failed to fund wallet")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fund wallet: {str(e)}")
    
    def copy_selected_address(self):
        """Copy the selected wallet address to clipboard."""
        item = self.wallet_list.currentItem()
        if not item:
            return
        
        wallet = item.data(32)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(wallet.address)
        
        QMessageBox.information(self, "Success", f"Address copied to clipboard:\n{wallet.address}")
    
    def delete_selected_wallet(self):
        """Delete the selected wallet."""
        item = self.wallet_list.currentItem()
        if not item:
            return
        
        wallet = item.data(32)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete wallet '{wallet.label}'?\n\n"
            f"Address: {wallet.address}\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.wallet_manager.delete_wallet(wallet.address):
                    self.refresh_wallets()
                    QMessageBox.information(self, "Success", "Wallet deleted successfully")
                else:
                    QMessageBox.warning(self, "Failed", "Failed to delete wallet")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete wallet: {str(e)}")


class WalletRecoveryDialog(QDialog):
    """Dialog for recovering a wallet from secret key."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recover Wallet")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Secret key input
        layout.addWidget(QLabel("Secret Key:"))
        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setPlaceholderText("S...")
        layout.addWidget(self.secret_key_edit)
        
        # Network selection
        layout.addWidget(QLabel("Network:"))
        self.network_combo = QComboBox()
        self.network_combo.addItems(["testnet", "mainnet"])
        self.network_combo.currentTextChanged.connect(self.on_network_changed)
        layout.addWidget(self.network_combo)
        
        # Label input
        layout.addWidget(QLabel("Label (optional):"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("My recovered wallet")
        layout.addWidget(self.label_edit)
        
        # Password input (for mainnet only)
        self.password_label = QLabel("Password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password to encrypt secret key")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        
        # Initially hide password fields
        self.on_network_changed("testnet")
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_network_changed(self, network):
        """Handle network selection change."""
        is_mainnet = (network == "mainnet")
        self.password_label.setVisible(is_mainnet)
        self.password_edit.setVisible(is_mainnet)
        if is_mainnet:
            self.password_edit.setFocus()
    
    def get_secret_key(self):
        """Get the secret key."""
        return self.secret_key_edit.text().strip()
    
    def get_network(self):
        """Get the selected network."""
        return self.network_combo.currentText()
    
    def get_label(self):
        """Get the wallet label."""
        label = self.label_edit.text().strip()
        return label if label else None
    
    def get_password(self):
        """Get the password (for mainnet only)."""
        if self.network_combo.currentText() == "mainnet":
            return self.password_edit.text()
        return None
    
    def accept(self):
        """Validate input before accepting."""
        secret_key = self.get_secret_key()
        if not secret_key:
            QMessageBox.warning(self, "Invalid Input", "Please enter a secret key")
            return
        
        if not secret_key.startswith('S'):
            QMessageBox.warning(self, "Invalid Input", "Secret key must start with 'S'")
            return
        
        network = self.get_network()
        if network == "mainnet":
            password = self.get_password()
            if not password:
                QMessageBox.warning(self, "Invalid Input", "Password is required for mainnet wallets")
                return
        
        super().accept()


class WalletCreationDialog(QDialog):
    """Dialog for creating a new wallet with network selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Wallet")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Network selection
        layout.addWidget(QLabel("Network:"))
        self.network_combo = QComboBox()
        self.network_combo.addItems(["testnet", "mainnet"])
        self.network_combo.currentTextChanged.connect(self.on_network_changed)
        layout.addWidget(self.network_combo)
        
        # Label input
        layout.addWidget(QLabel("Label (optional):"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("My wallet")
        layout.addWidget(self.label_edit)
        
        # Password input (for mainnet only)
        self.password_label = QLabel("Password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password to encrypt secret key")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        
        # Password confirmation (for mainnet only)
        self.password_confirm_label = QLabel("Confirm Password:")
        self.password_confirm_edit = QLineEdit()
        self.password_confirm_edit.setEchoMode(QLineEdit.Password)
        self.password_confirm_edit.setPlaceholderText("Re-enter password")
        layout.addWidget(self.password_confirm_label)
        layout.addWidget(self.password_confirm_edit)
        
        # Warning text for mainnet
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.warning_label)
        
        # Initially hide password fields
        self.on_network_changed("testnet")
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_network_changed(self, network):
        """Handle network selection change."""
        is_mainnet = (network == "mainnet")
        self.password_label.setVisible(is_mainnet)
        self.password_edit.setVisible(is_mainnet)
        self.password_confirm_label.setVisible(is_mainnet)
        self.password_confirm_edit.setVisible(is_mainnet)
        self.warning_label.setVisible(is_mainnet)
        
        if is_mainnet:
            self.warning_label.setText("⚠ Mainnet wallets use real funds. Keep your password safe!")
            self.password_edit.setFocus()
        else:
            self.warning_label.setText("")
    
    def get_network(self):
        """Get the selected network."""
        return self.network_combo.currentText()
    
    def get_label(self):
        """Get the wallet label."""
        label = self.label_edit.text().strip()
        return label if label else None
    
    def get_password(self):
        """Get the password (for mainnet only)."""
        if self.network_combo.currentText() == "mainnet":
            return self.password_edit.text()
        return None
    
    def accept(self):
        """Validate input before accepting."""
        network = self.get_network()
        
        if network == "mainnet":
            password = self.get_password()
            password_confirm = self.password_confirm_edit.text()
            
            if not password:
                QMessageBox.warning(self, "Invalid Input", "Password is required for mainnet wallets")
                return
            
            if password != password_confirm:
                QMessageBox.warning(self, "Invalid Input", "Passwords do not match")
                return
            
            if len(password) < 8:
                QMessageBox.warning(self, "Invalid Input", "Password must be at least 8 characters")
                return
        
        super().accept()


class WalletDetailsDialog(QDialog):
    """Dialog for displaying newly created wallet details."""
    
    def __init__(self, parent=None, wallet=None, secret_key=None, seed_phrase=None):
        super().__init__(parent)
        self.setWindowTitle("Wallet Created Successfully")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.wallet = wallet
        self.secret_key = secret_key
        self.seed_phrase = seed_phrase
        
        layout = QVBoxLayout(self)
        
        # Success message
        layout.addWidget(QLabel(f"✅ {wallet.network.title()} wallet created successfully!"))
        layout.addWidget(QLabel(f"Label: {wallet.label}"))
        layout.addSpacing(10)
        
        # Public Key (copyable)
        layout.addWidget(QLabel("Public Key (Address):"))
        self.public_key_edit = QLineEdit(wallet.address)
        self.public_key_edit.setReadOnly(True)
        public_layout = QHBoxLayout()
        public_layout.addWidget(self.public_key_edit)
        self.copy_public_btn = QPushButton("Copy")
        self.copy_public_btn.clicked.connect(self.copy_public_key)
        public_layout.addWidget(self.copy_public_btn)
        layout.addLayout(public_layout)
        
        # Private Key (copyable password field)
        layout.addWidget(QLabel("Private Key (Secret):"))
        self.private_key_edit = QLineEdit(secret_key)
        self.private_key_edit.setEchoMode(QLineEdit.Password)
        self.private_key_edit.setReadOnly(True)
        private_layout = QHBoxLayout()
        private_layout.addWidget(self.private_key_edit)
        self.copy_private_btn = QPushButton("Copy")
        self.copy_private_btn.clicked.connect(self.copy_private_key)
        self.reveal_private_btn = QPushButton("Show")
        self.reveal_private_btn.clicked.connect(self.toggle_private_visibility)
        self.reveal_private_btn.setCheckable(True)
        private_layout.addWidget(self.copy_private_btn)
        private_layout.addWidget(self.reveal_private_btn)
        layout.addLayout(private_layout)
        
        # Seed Phrase (copyable text area)
        layout.addWidget(QLabel("Seed Phrase (12 words):"))
        self.seed_edit = QPlainTextEdit(seed_phrase)
        self.seed_edit.setReadOnly(True)
        self.seed_edit.setMaximumHeight(80)
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(self.seed_edit)
        self.copy_seed_btn = QPushButton("Copy")
        self.copy_seed_btn.clicked.connect(self.copy_seed_phrase)
        seed_layout.addWidget(self.copy_seed_btn)
        layout.addLayout(seed_layout)
        
        # Warning message
        if wallet.network == "mainnet":
            warning = QLabel("⚠️ WARNING: This is a MAINNET wallet with real funds!")
            warning.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
            layout.addWidget(warning)
        
        warning2 = QLabel("⚠️ Keep your private key and seed phrase secure and never share them!")
        warning2.setStyleSheet("color: orange; font-weight: bold; padding: 10px;")
        layout.addWidget(warning2)
        
        # Auto-funding status for testnet
        if wallet.network == "testnet":
            layout.addWidget(QLabel("🪙 The wallet has been auto-funded with test lumens."))
        
        layout.addSpacing(10)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def copy_public_key(self):
        """Copy public key to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.wallet.address)
        QMessageBox.information(self, "Copied", "Public key copied to clipboard!")
    
    def copy_private_key(self):
        """Copy private key to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.secret_key)
        QMessageBox.warning(self, "Copied", "Private key copied to clipboard!\n\nKeep it secure!")
    
    def copy_seed_phrase(self):
        """Copy seed phrase to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.seed_phrase)
        QMessageBox.warning(self, "Copied", "Seed phrase copied to clipboard!\n\nKeep it secure!")
    
    def toggle_private_visibility(self):
        """Toggle private key visibility."""
        if self.reveal_private_btn.isChecked():
            self.private_key_edit.setEchoMode(QLineEdit.Normal)
            self.reveal_private_btn.setText("Hide")
        else:
            self.private_key_edit.setEchoMode(QLineEdit.Password)
            self.reveal_private_btn.setText("Show")


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

