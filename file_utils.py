import os
import stat
from pathlib import Path


def set_secure_permissions(file_path):
    """
    Set secure file permissions based on platform
    """
    try:
        if os.name == 'nt':  # Windows
            # On Windows, we can't set Unix-style permissions
            # The file will inherit the user's permissions
            pass
        else:  # Unix-like systems (Linux, macOS)
            # Set read/write for owner only
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as e:
        print(f"Warning: Could not set permissions on {file_path}: {e}")


def create_secure_directory(dir_path):
    """
    Create a directory with secure permissions
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        if os.name != 'nt':  # Unix-like systems
            # Set read/write/execute for owner only
            os.chmod(dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception as e:
        print(f"Warning: Could not set directory permissions on {dir_path}: {e}")


def ensure_config_directory(config_path):
    """
    Ensure configuration directory exists with proper permissions
    """
    try:
        create_secure_directory(config_path)
        return True
    except Exception as e:
        print(f"Error creating config directory {config_path}: {e}")
        return False 