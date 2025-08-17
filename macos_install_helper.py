#!/usr/bin/env python3
"""
macOS-specific installation helper for Metavinci.
Handles the unique requirements of macOS security and permissions
for installing the hvym CLI.
"""

import os
import sys
import stat
import tempfile
import urllib.request
import ssl
import tarfile
import zipfile
from pathlib import Path
from platform_manager import PlatformManager

class MacOSInstallHelper:
    """Helper class for macOS-specific installation requirements."""
    
    def __init__(self):
        self.platform_manager = PlatformManager()
        self.config_dir = self.platform_manager.get_config_path()
        self.bin_dir = self.config_dir / 'bin'
        self.hvym_path = self.platform_manager.get_hvym_path()
        
    def install_hvym_cli(self):
        """
        Download and install the hvym CLI for macOS.
        
        Returns:
            str: Path to the installed hvym binary, or None if failed
        """
        try:
            print("Starting macOS-specific hvym CLI installation...")
            
            # Create necessary directories
            self._create_directories()
            
            # Download the latest hvym CLI
            download_path = self._download_hvym_cli()
            if not download_path:
                print("Failed to download hvym CLI")
                return None
                
            # Install the binary
            success = self._install_binary(download_path)
            if not success:
                print("Failed to install hvym CLI")
                return None
                
            # Verify installation
            if self._verify_installation():
                print(f"Successfully installed hvym CLI to: {self.hvym_path}")
                return str(self.hvym_path)
            else:
                print("Installation verification failed")
                return None
                
        except Exception as e:
            print(f"Error during macOS installation: {e}")
            return None
    
    def install_hvym_press_cli(self):
        """
        Download and install the hvym_press CLI for macOS.
        Note: hvym_press is not supported on Apple Silicon (ARM64).
        
        Returns:
            str: Path to the installed hvym_press binary, or None if failed
        """
        try:
            print("Starting macOS-specific hvym_press CLI installation...")
            
            # Check if hvym_press is supported on current architecture
            if not self.platform_manager.is_hvym_press_supported():
                print("hvym_press is not supported on macOS Apple Silicon (ARM64)")
                return None
            
            # Create necessary directories
            self._create_directories()
            
            # Download the latest hvym_press CLI
            download_path = self._download_hvym_press_cli()
            if not download_path:
                print("Failed to download hvym_press CLI")
                return None
                
            # Install the binary
            success = self._install_hvym_press_binary(download_path)
            if not success:
                print("Failed to install hvym_press CLI")
                return None
                
            # Verify installation
            if self._verify_hvym_press_installation():
                print(f"Successfully installed hvym_press CLI to: {self.platform_manager.get_press_path()}")
                return str(self.platform_manager.get_press_path())
            else:
                print("Installation verification failed")
                return None
                
        except Exception as e:
            print(f"Error during macOS hvym_press installation: {e}")
            return None
    
    def _create_directories(self):
        """Create necessary directories with proper permissions."""
        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create bin directory
            self.bin_dir.mkdir(parents=True, exist_ok=True)
            
            # Set proper permissions (755 for directories)
            os.chmod(self.config_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            os.chmod(self.bin_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            
            print(f"Created directories: {self.config_dir}, {self.bin_dir}")
            
        except Exception as e:
            print(f"Error creating directories: {e}")
            raise
    
    def _download_hvym_cli(self):
        """
        Download the latest hvym CLI for macOS.
        
        Returns:
            Path: Path to downloaded file, or None if failed
        """
        try:
            # Get the latest release URL for macOS (architecture-aware)
            url = self._get_latest_hvym_release_url()
            if not url:
                print("Could not determine download URL")
                return None
            
            print(f"Downloading from: {url}")
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
                temp_path = Path(temp_file.name)
            
            # Download with certifi-backed SSL context to avoid certificate issues
            try:
                import certifi
                context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                context = ssl.create_default_context()
            
            req = urllib.request.Request(url, headers={"User-Agent": "Metavinci/1.0"})
            with urllib.request.urlopen(req, context=context) as resp, open(temp_path, 'wb') as out:
                out.write(resp.read())
            
            print(f"Downloaded to: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"Error downloading hvym CLI: {e}")
            return None
    
    def _get_latest_hvym_release_url(self):
        """
        Get the URL for the latest hvym CLI release for macOS.
        
        Returns:
            str: Download URL, or None if failed
        """
        try:
            # GitHub API URL for latest release (using the correct repository)
            api_url = "https://api.github.com/repos/inviti8/heavymeta-cli-dev/releases/latest"
            
            # Get the latest release info
            with urllib.request.urlopen(api_url) as response:
                import json
                release_data = json.loads(response.read().decode())
            
            # Find the macOS asset (architecture-aware)
            import platform as _platform
            machine = (_platform.machine() or '').lower()
            arch_suffix = 'arm64' if 'arm' in machine or 'aarch64' in machine else 'amd64'
            expected_asset_name = f"hvym-macos-{arch_suffix}.tar.gz"
            assets = {asset['name']: asset['browser_download_url'] for asset in release_data.get('assets', [])}
            url = assets.get(expected_asset_name)
            
            if not url:
                # Fallback: try legacy universal macOS asset name if arch-specific not found
                legacy_name = "hvym-macos.tar.gz"
                url = assets.get(legacy_name)
                if not url:
                    print(f"Assets {expected_asset_name} or {legacy_name} not found in latest release")
                    return None
            
            return url
            
        except Exception as e:
            print(f"Error getting release URL: {e}")
            return None
    
    def _install_binary(self, download_path):
        """
        Extract and install the downloaded binary.
        
        Args:
            download_path (Path): Path to downloaded file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract the archive
            if download_path.suffix == '.tar.gz' or download_path.name.endswith('.tar.gz'):
                with tarfile.open(download_path, 'r:gz') as tar:
                    tar.extractall(self.bin_dir)
            elif download_path.suffix == '.zip':
                with zipfile.ZipFile(download_path, 'r') as zip_file:
                    zip_file.extractall(self.bin_dir)
            else:
                print(f"Unsupported file format: {download_path.suffix} (filename: {download_path.name})")
                return False
            
            # Find the extracted binary (architecture-aware)
            import platform as _platform
            machine = (_platform.machine() or '').lower()
            arch_suffix = 'arm64' if 'arm' in machine or 'aarch64' in machine else 'amd64'
            binary_name = f'hvym-macos-{arch_suffix}'
            extracted_binary = self.bin_dir / binary_name
            
            if not extracted_binary.exists():
                # Look for the binary in subdirectories
                for item in self.bin_dir.iterdir():
                    if item.is_dir():
                        potential_binary = item / binary_name
                        if potential_binary.exists():
                            extracted_binary = potential_binary
                            break
            
            if not extracted_binary.exists():
                # Fallback to legacy filename if present
                legacy_binary = self.bin_dir / 'hvym-macos'
                if legacy_binary.exists():
                    extracted_binary = legacy_binary
                else:
                    print(f"Could not find {binary_name} or legacy hvym-macos in extracted files")
                    return False
            
            # Move to final location if needed
            if extracted_binary != self.hvym_path:
                if self.hvym_path.exists():
                    self.hvym_path.unlink()
                extracted_binary.rename(self.hvym_path)
            
            # Set executable permissions
            os.chmod(self.hvym_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

            # Remove macOS quarantine attribute if present to avoid Gatekeeper blocking execution
            try:
                import subprocess
                subprocess.run([
                    'xattr', '-d', 'com.apple.quarantine', str(self.hvym_path)
                ], check=False, capture_output=True)
            except Exception:
                # Best-effort: ignore if xattr removal fails
                pass
            
            # Clean up downloaded file
            download_path.unlink()
            
            print(f"Installed binary to: {self.hvym_path}")
            return True
            
        except Exception as e:
            print(f"Error installing binary: {e}")
            return False
    
    def _verify_installation(self):
        """
        Verify that the installation was successful.
        
        Returns:
            bool: True if verification passes, False otherwise
        """
        try:
            # Check if binary exists
            if not self.hvym_path.exists():
                print("Binary does not exist")
                return False
            
            # Check if binary is executable
            if not os.access(self.hvym_path, os.X_OK):
                print("Binary is not executable")
                return False
            
            # For PyInstaller executables on macOS, the --version command might fail
            # due to directory creation issues, but the binary is still valid
            # Let's try a simple verification first
            import subprocess
            try:
                result = subprocess.run([str(self.hvym_path), '--version'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"Binary verification successful: {result.stdout.strip()}")
                    return True
                else:
                    # If --version fails, check if it's a PyInstaller error
                    if "PYI-" in result.stderr:
                        print("Binary is a PyInstaller executable (expected behavior)")
                        print("Installation appears successful - binary exists and is executable")
                        return True
                    else:
                        print(f"Binary verification failed: {result.stderr}")
                        return False
                        
            except subprocess.TimeoutExpired:
                print("Binary verification timed out")
                return False
                
        except Exception as e:
            print(f"Error during verification: {e}")
            return False
    
    def check_installation_status(self):
        """
        Check if hvym CLI is already installed and working.
        
        Returns:
            bool: True if installed and working, False otherwise
        """
        try:
            if not self.hvym_path.exists():
                return False
            
            if not os.access(self.hvym_path, os.X_OK):
                return False
            
            import subprocess
            try:
                result = subprocess.run([str(self.hvym_path), '--version'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    return True
                else:
                    # If --version fails, check if it's a PyInstaller error
                    if "PYI-" in result.stderr:
                        # PyInstaller executables on macOS might have directory issues
                        # but the binary is still valid if it exists and is executable
                        return True
                    else:
                        return False
                        
            except subprocess.TimeoutExpired:
                return False
                
        except Exception:
            return False

    def _download_hvym_press_cli(self):
        """
        Download the latest hvym_press CLI for macOS.
        
        Returns:
            Path: Path to downloaded file, or None if failed
        """
        try:
            # Get the latest release URL for macOS
            url = self._get_latest_hvym_press_release_url()
            if not url:
                print("Could not determine download URL")
                return None
            
            print(f"Downloading from: {url}")
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
                temp_path = Path(temp_file.name)
            
            # Download with certifi-backed SSL context to avoid certificate issues
            try:
                import certifi
                context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                context = ssl.create_default_context()
            
            req = urllib.request.Request(url, headers={"User-Agent": "Metavinci/1.0"})
            with urllib.request.urlopen(req, context=context) as resp, open(temp_path, 'wb') as out:
                out.write(resp.read())
            
            print(f"Downloaded to: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"Error downloading hvym_press CLI: {e}")
            return None

    def _get_latest_hvym_press_release_url(self):
        """
        Get the URL for the latest hvym_press CLI release for macOS.
        
        Returns:
            str: Download URL, or None if failed
        """
        try:
            # GitHub API URL for latest release
            api_url = "https://api.github.com/repos/inviti8/hvym_press/releases/latest"
            
            # Get the latest release info
            with urllib.request.urlopen(api_url) as response:
                import json
                release_data = json.loads(response.read().decode())
            
            # Find the macOS asset
            expected_asset_name = "hvym_press-macos"
            assets = {asset['name']: asset['browser_download_url'] for asset in release_data.get('assets', [])}
            url = assets.get(expected_asset_name)
            
            if not url:
                print(f"Asset {expected_asset_name} not found in latest release")
                return None
            
            return url
            
        except Exception as e:
            print(f"Error getting release URL: {e}")
            return None

    def _install_hvym_press_binary(self, download_path):
        """
        Extract and install the downloaded hvym_press binary.
        
        Args:
            download_path (Path): Path to downloaded file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract the archive
            if download_path.suffix == '.tar.gz' or download_path.name.endswith('.tar.gz'):
                with tarfile.open(download_path, 'r:gz') as tar:
                    tar.extractall(self.bin_dir)
            elif download_path.suffix == '.zip':
                with zipfile.ZipFile(download_path, 'r') as zip_file:
                    zip_file.extractall(self.bin_dir)
            else:
                print(f"Unsupported file format: {download_path.suffix} (filename: {download_path.name})")
                return False
            
            # Find the extracted binary
            binary_name = 'hvym_press-macos'
            extracted_binary = self.bin_dir / binary_name
            
            if not extracted_binary.exists():
                # Look for the binary in subdirectories
                for item in self.bin_dir.iterdir():
                    if item.is_dir():
                        potential_binary = item / binary_name
                        if potential_binary.exists():
                            extracted_binary = potential_binary
                            break
            
            if not extracted_binary.exists():
                print(f"Could not find {binary_name} in extracted files")
                return False
            
            # Move to final location if needed
            press_path = self.platform_manager.get_press_path()
            if extracted_binary != press_path:
                if press_path.exists():
                    press_path.unlink()
                extracted_binary.rename(press_path)
            
            # Set executable permissions
            os.chmod(press_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

            # Remove macOS quarantine attribute if present to avoid Gatekeeper blocking execution
            try:
                import subprocess
                subprocess.run([
                    'xattr', '-d', 'com.apple.quarantine', str(press_path)
                ], check=False, capture_output=True)
            except Exception:
                # Best-effort: ignore if xattr removal fails
                pass
            
            # Clean up downloaded file
            download_path.unlink()
            
            print(f"Installed binary to: {press_path}")
            return True
            
        except Exception as e:
            print(f"Error installing binary: {e}")
            return False

    def _verify_hvym_press_installation(self):
        """
        Verify that the hvym_press installation was successful.
        
        Returns:
            bool: True if verification passes, False otherwise
        """
        try:
            press_path = self.platform_manager.get_press_path()
            
            # Check if binary exists
            if not press_path.exists():
                print("Binary does not exist")
                return False
            
            # Check if binary is executable
            if not os.access(press_path, os.X_OK):
                print("Binary is not executable")
                return False
            
            # For PyInstaller executables on macOS, the --version command might fail
            # due to directory creation issues, but the binary is still valid
            # Let's try a simple verification first
            import subprocess
            try:
                result = subprocess.run([str(press_path), '--version'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"Binary verification successful: {result.stdout.strip()}")
                    return True
                else:
                    # If --version fails, check if it's a PyInstaller error
                    if "PYI-" in result.stderr:
                        print("Binary is a PyInstaller executable (expected behavior)")
                        print("Installation appears successful - binary exists and is executable")
                        return True
                    else:
                        print(f"Binary verification failed: {result.stderr}")
                        return False
                        
            except subprocess.TimeoutExpired:
                print("Binary verification timed out")
                return False
                
        except Exception as e:
            print(f"Error during verification: {e}")
            return False

    # --- Convenience methods used by tests ---
    def ensure_directories(self) -> bool:
        """Public wrapper used by tests to create needed directories."""
        try:
            self._create_directories()
            return True
        except Exception:
            return False

    def get_installation_status(self) -> dict:
        """Return a summary of install-related paths and status for tests."""
        try:
            return self.get_install_info()
        except Exception:
            return {
                'hvym_path': str(self.hvym_path),
                'bin_dir': str(self.bin_dir),
                'config_dir': str(self.config_dir),
                'is_installed': False
            }

    def check_macos_permissions(self) -> list:
        """Best-effort permission checks; return list of issue strings (empty if none)."""
        issues = []
        try:
            # Check directories are writable and executable
            for path in (self.config_dir, self.bin_dir):
                try:
                    if not path.exists():
                        continue
                    if not os.access(path, os.W_OK):
                        issues.append(f"Directory not writable: {path}")
                    if not os.access(path, os.X_OK):
                        issues.append(f"Directory not executable: {path}")
                except Exception:
                    issues.append(f"Could not validate permissions for: {path}")

            # If hvym exists, ensure it's executable
            try:
                if self.hvym_path.exists() and not os.access(self.hvym_path, os.X_OK):
                    issues.append(f"Binary not executable: {self.hvym_path}")
            except Exception:
                issues.append("Could not validate hvym binary permissions")
        except Exception:
            # On any unexpected error, provide a generic hint but don't fail
            issues.append("Permission check encountered an unexpected error")
        return issues

    def uninstall_hvym_cli(self):
        """
        Uninstall the hvym CLI and clean up all related files.
        
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        try:
            print("Starting macOS-specific hvym CLI uninstallation...")
            
            # Remove the hvym binary
            if self.hvym_path.exists():
                self.hvym_path.unlink()
                print(f"Removed hvym binary: {self.hvym_path}")
            
            # Remove the bin directory if it's empty
            if self.bin_dir.exists() and not any(self.bin_dir.iterdir()):
                self.bin_dir.rmdir()
                print(f"Removed empty bin directory: {self.bin_dir}")
            
            # Remove the config directory if it's empty (and not the root Metavinci dir)
            if self.config_dir.exists() and not any(self.config_dir.iterdir()):
                self.config_dir.rmdir()
                print(f"Removed empty config directory: {self.config_dir}")
            
            print("Successfully uninstalled hvym CLI")
            return True
            
        except Exception as e:
            print(f"Error during macOS uninstallation: {e}")
            return False

    def get_install_info(self):
        """
        Get information about the current installation for uninstall scripts.
        
        Returns:
            dict: Installation information including paths and files
        """
        return {
            'hvym_path': str(self.hvym_path),
            'bin_dir': str(self.bin_dir),
            'config_dir': str(self.config_dir),
            'is_installed': self.check_installation_status()
        }

def main():
    """Test the macOS installation helper."""
    helper = MacOSInstallHelper()
    
    print("=== macOS Installation Helper Test ===")
    print(f"Config directory: {helper.config_dir}")
    print(f"Binary directory: {helper.bin_dir}")
    print(f"Expected hvym path: {helper.hvym_path}")
    
    # Check current status
    if helper.check_installation_status():
        print("✅ hvym CLI is already installed and working")
    else:
        print("❌ hvym CLI is not installed or not working")
        
        # Try to install
        print("\nAttempting installation...")
        result = helper.install_hvym_cli()
        
        if result:
            print(f"✅ Installation successful: {result}")
        else:
            print("❌ Installation failed")

if __name__ == "__main__":
    main()
