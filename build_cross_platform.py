#!/usr/bin/env python3
"""
Cross-platform build script for Metavinci
Supports building for Linux, macOS, and Windows
"""

import shutil
import subprocess
import sys
import os
from pathlib import Path
import argparse

# Import our platform manager
from platform_manager import PlatformManager


class CrossPlatformBuilder:
    def __init__(self):
        self.platform_manager = PlatformManager()
        self.cwd = Path.cwd()
        self.build_dir = self.cwd / 'build'
        
    def clean_build_directory(self):
        """Clean the build directory"""
        if self.build_dir.exists():
            for item in self.build_dir.iterdir():
                if item.name not in ['.git', 'README.md', 'install.sh']:
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)
        else:
            self.build_dir.mkdir()
    
    def get_icon_file(self, target_platform=None):
        """Get the appropriate icon file for the target platform"""
        if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
            return self.cwd / 'hvym_logo_64.ico'
        elif target_platform == 'macos' or (target_platform is None and self.platform_manager.is_macos):
            return self.cwd / 'hvym_logo_64.icns'
        else:  # Linux
            return self.cwd / 'hvym_logo_64.png'
    
    def get_dist_directory(self, target_platform=None):
        """Get the distribution directory for the target platform"""
        if target_platform == 'macos':
            return self.build_dir / 'dist' / 'mac'
        elif target_platform == 'windows':
            return self.build_dir / 'dist' / 'windows'
        else:  # Linux
            return self.build_dir / 'dist' / 'linux'
    
    def copy_source_files(self):
        """Copy source files to build directory"""
        source_files = [
            ('metavinci.py', 'metavinci.py'),
            ('requirements.txt', 'requirements.txt'),
            ('platform_manager.py', 'platform_manager.py'),
            ('download_utils.py', 'download_utils.py'),
            ('file_utils.py', 'file_utils.py'),
        ]
        
        directories = ['images', 'data', 'service']
        
        # Copy files
        for src, dst in source_files:
            src_path = self.cwd / src
            if src_path.exists():
                shutil.copy(src_path, self.build_dir / dst)
            else:
                print(f"Warning: {src} not found")
        
        # Copy directories
        for dir_name in directories:
            src_dir = self.cwd / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, self.build_dir / dir_name)
            else:
                print(f"Warning: {dir_name} directory not found")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        # Skip dependency installation in CI/CD environment
        if os.environ.get('CI') == 'true':
            print("Skipping dependency installation in CI environment")
            return
            
        requirements_file = self.build_dir / 'requirements.txt'
        if requirements_file.exists():
            print("Installing dependencies...")
            subprocess.run(['pip', 'install', '-r', str(requirements_file)], 
                         cwd=str(self.build_dir), check=True)
        else:
            print("Warning: requirements.txt not found")
    
    def build_executable(self, target_platform=None):
        """Build the executable using PyInstaller"""
        dist_dir = self.get_dist_directory(target_platform)
        icon_file = self.get_icon_file(target_platform)
        
        # Ensure dist directory exists
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Build PyInstaller command with minimal exclusions
        pyinstaller_cmd = [
            'pyinstaller',
            '--noconsole',
            '--onefile',
            '--strip',  # Strip debug symbols
            f'--distpath={dist_dir}',
            # Only exclude modules that are definitely not needed
            '--exclude-module', 'pytest',
            '--exclude-module', 'unittest',
            '--exclude-module', 'doctest',
            '--collect-all', 'PyQt5.Qt',
            'metavinci.py'
        ]
        
        # Add data files with platform-specific separators
        if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
            # Windows uses semicolon separator
            pyinstaller_cmd.extend(['--add-data', 'images;images'])
            pyinstaller_cmd.extend(['--add-data', 'data;data'])
            pyinstaller_cmd.extend(['--add-data', 'service;service'])
        else:
            # Unix systems use colon separator
            pyinstaller_cmd.extend(['--add-data', 'images:images'])
            pyinstaller_cmd.extend(['--add-data', 'data:data'])
            pyinstaller_cmd.extend(['--add-data', 'service:service'])
        
        # Add PyQt5 Qt platforms plugin directory
        try:
            import PyQt5
            import os as _os
            qt_plugins = _os.path.join(_os.path.dirname(PyQt5.__file__), 'Qt', 'plugins', 'platforms')
            if _os.path.exists(qt_plugins) and _os.listdir(qt_plugins):
                if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
                    pyinstaller_cmd.extend(['--add-data', f'{qt_plugins};PyQt5/Qt/plugins/platforms'])
                else:
                    pyinstaller_cmd.extend(['--add-data', f'{qt_plugins}:PyQt5/Qt/plugins/platforms'])
            else:
                print(f"[INFO] Qt platforms directory not found or empty, skipping --add-data for platforms.")
        except Exception as e:
            print(f"[WARN] Could not add PyQt5 Qt platforms: {e}")
        
        # Add icon if it exists
        if icon_file.exists():
            pyinstaller_cmd.insert(3, f'--icon={str(icon_file)}')
        else:
            print(f"Warning: Icon file {icon_file} not found")
        
        print(f"Building for {target_platform or 'current platform'}...")
        print(f"Command: {' '.join(pyinstaller_cmd)}")
        
        try:
            subprocess.run(pyinstaller_cmd, cwd=str(self.build_dir), check=True)
            
            # Analyze the built executable size
            executable_name = 'metavinci'
            if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
                executable_name += '.exe'
            
            executable_path = dist_dir / executable_name
            if executable_path.exists():
                size_mb = executable_path.stat().st_size / (1024 * 1024)
                print(f"Build completed successfully!")
                print(f"Executable size: {size_mb:.2f} MB")
                
                # Provide size analysis
                if size_mb > 50:
                    print(f"[WARN] Large executable size ({size_mb:.2f} MB) - consider optimizing dependencies")
                elif size_mb > 30:
                    print(f"[SIZE] Moderate executable size ({size_mb:.2f} MB)")
                else:
                    print(f"[OK] Good executable size ({size_mb:.2f} MB)")
                
                # Remove the test that runs the binary with --help
                # (was here previously, now removed)
            else:
                print(f"Build completed but executable not found at {executable_path}")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")
            return False
    
    def install_to_local(self, target_platform=None):
        """Install the built executable to local directory"""
        dist_dir = self.get_dist_directory(target_platform)
        config_path = self.platform_manager.get_config_path()
        bin_dir = config_path / 'bin'
        
        # Ensure bin directory exists
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine executable name
        executable_name = 'metavinci'
        if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
            executable_name += '.exe'
        
        source_executable = dist_dir / executable_name
        target_executable = bin_dir / executable_name
        
        if source_executable.exists():
            shutil.copy(str(source_executable), str(target_executable))
            
            # Set executable permissions (Unix systems only)
            if not self.platform_manager.is_windows:
                try:
                    os.chmod(target_executable, 0o755)
                    print(f"Executable permissions set on {target_executable}")
                except Exception as e:
                    print(f"Warning: Could not set executable permissions: {e}")
            
            print(f"Installed to: {target_executable}")
            return True
        else:
            print(f"Error: Executable not found at {source_executable}")
            return False
    
    def build_all_platforms(self):
        """Build for all platforms"""
        platforms = ['linux', 'macos', 'windows']
        results = {}
        
        for platform in platforms:
            print(f"\n{'='*50}")
            print(f"Building for {platform}")
            print(f"{'='*50}")
            
            self.clean_build_directory()
            self.copy_source_files()
            self.install_dependencies()
            
            success = self.build_executable(platform)
            results[platform] = success
            
            if success:
                print(f"[OK] {platform} build successful")
            else:
                print(f"[FAIL] {platform} build failed")
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Cross-platform build script for Metavinci')
    parser.add_argument('--platform', choices=['linux', 'macos', 'windows'], 
                       help='Target platform to build for')
    parser.add_argument('--all', action='store_true', 
                       help='Build for all platforms')
    parser.add_argument('--install', action='store_true', 
                       help='Install built executable to local directory')
    parser.add_argument('--clean', action='store_true', 
                       help='Clean build directory only')
    
    args = parser.parse_args()
    
    builder = CrossPlatformBuilder()
    
    if args.clean:
        builder.clean_build_directory()
        print("Build directory cleaned")
        return
    
    if args.all:
        results = builder.build_all_platforms()
        print("\n" + "="*50)
        print("Build Summary:")
        for platform, success in results.items():
            status = "[OK] SUCCESS" if success else "[FAIL] FAILED"
            print(f"{platform}: {status}")
        return
    
    # Single platform build
    target_platform = args.platform
    
    builder.clean_build_directory()
    builder.copy_source_files()
    builder.install_dependencies()
    
    success = builder.build_executable(target_platform)
    
    if success and args.install:
        builder.install_to_local(target_platform)
    
    if success:
        print(f"\n[OK] Build completed successfully for {target_platform or 'current platform'}")
        if args.install:
            print("[OK] Executable installed to local directory")
    else:
        print(f"\n[FAIL] Build failed for {target_platform or 'current platform'}")
        sys.exit(1)


if __name__ == "__main__":
    main() 