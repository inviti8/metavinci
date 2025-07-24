import platform
import os
from pathlib import Path


class PlatformManager:
    """
    Handles cross-platform path resolution and system detection
    while maintaining Linux compatibility patterns
    """
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_windows = self.platform == 'windows'
        self.is_macos = self.platform == 'darwin'
        self.is_linux = self.platform == 'linux'
        
    def get_config_path(self):
        """Get the main configuration directory path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Local' / 'Programs' / 'Metavinci'
        elif self.is_macos:
            return Path.home() / 'Library' / 'Application Support' / 'Metavinci'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.metavinci'
    
    def get_bin_path(self):
        """Get the binary directory path"""
        config_path = self.get_config_path()
        return config_path / 'bin'
    
    def get_dfx_path(self):
        """Get DFX binary path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Local' / 'dfx' / 'bin' / 'dfx.exe'
        elif self.is_macos:
            return Path.home() / '.local' / 'share' / 'dfx' / 'bin' / 'dfx'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.local' / 'share' / 'dfx' / 'bin' / 'dfx'
    
    def get_hvym_path(self):
        """Get Heavymeta CLI path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Local' / 'heavymeta-cli' / 'hvym-win.exe'
        elif self.is_macos:
            return Path.home() / '.local' / 'share' / 'heavymeta-cli' / 'hvym-macos'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.local' / 'share' / 'heavymeta-cli' / 'hvym-linux'
    
    def get_didc_path(self):
        """Get DIDC binary path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Local' / 'didc' / 'didc.exe'
        elif self.is_macos:
            return Path.home() / '.local' / 'share' / 'didc' / 'didc'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.local' / 'share' / 'didc' / 'didc'
    
    def get_press_path(self):
        """Get Heavymeta Press path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Local' / 'heavymeta-press' / 'hvym-press-win.exe'
        elif self.is_macos:
            return Path.home() / '.local' / 'share' / 'heavymeta-press' / 'hvym-press-macos'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.local' / 'share' / 'heavymeta-press' / 'hvym-press-linux'
    
    def get_blender_path(self):
        """Get Blender configuration path"""
        if self.is_windows:
            return Path.home() / 'AppData' / 'Roaming' / 'Blender Foundation' / 'Blender'
        elif self.is_macos:
            return Path.home() / 'Library' / 'Application Support' / 'Blender'
        else:  # Linux - maintain existing pattern
            return Path.home() / '.config' / 'blender'
    
    def get_shell_command(self, command):
        """Get platform-specific shell command"""
        if self.is_windows:
            return ['cmd', '/c', command]
        else:  # Linux/macOS
            return ['bash', '-c', command]
    
    def get_install_script_url(self):
        """Get platform-specific install script URL"""
        if self.is_windows:
            return 'https://github.com/inviti8/hvym/raw/main/install.ps1'
        else:  # Linux/macOS
            return 'https://github.com/inviti8/hvym/raw/main/install.sh'
    
    def get_press_install_script_url(self):
        """Get platform-specific press install script URL"""
        if self.is_windows:
            return 'https://raw.githubusercontent.com/inviti8/hvym_press/refs/heads/main/install.ps1'
        else:  # Linux/macOS
            return 'https://raw.githubusercontent.com/inviti8/hvym_press/refs/heads/main/install.sh' 