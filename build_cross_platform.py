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
            ('macos_install_helper.py', 'macos_install_helper.py'),
            ('resources.qrc', 'resources.qrc'),
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
        requirements_file = self.build_dir / 'requirements.txt'
        fallback_file = Path.cwd() / 'build_requirements.txt'
        to_install = None
        if requirements_file.exists():
            to_install = requirements_file
        elif fallback_file.exists():
            to_install = fallback_file

        if to_install:
            print(f"Installing dependencies from {to_install} ...")
            try:
                subprocess.run(['pip', 'install', '--upgrade', 'pip', 'wheel', 'setuptools'], check=True)
                subprocess.run(['pip', 'install', '-r', str(to_install)], 
                             cwd=str(self.build_dir), check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to install dependencies: {e}")
                raise
        else:
            print("Warning: No requirements file found to install dependencies")
        # Compile Qt resources (minimal: loading.gif)
        try:
            qrc_src = self.build_dir / 'resources.qrc'
            if qrc_src.exists():
                resources_py = self.build_dir / 'resources_rc.py'
                # Prefer Python module invocation to avoid relying on external pyrcc5 in PATH
                cmd = [sys.executable, '-m', 'PyQt5.pyrcc_main', str(qrc_src), '-o', str(resources_py)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    # Fallback to pyrcc5 if module invocation failed
                    subprocess.run(['pyrcc5', str(qrc_src), '-o', str(resources_py)], check=True)
        except Exception as e:
            print(f"[WARN] Could not compile Qt resources: {e}")
    
    def build_executable(self, target_platform=None):
        """Build the executable using PyInstaller"""
        dist_dir = self.get_dist_directory(target_platform)
        icon_file = self.get_icon_file(target_platform)
        
        # Ensure dist directory exists
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Build PyInstaller command with minimal exclusions
        if target_platform == 'macos':
            pyinstaller_cmd = [
                'pyinstaller',
                '--windowed',
                '--name', 'metavinci_desktop',
                f'--distpath={dist_dir}',
                '--exclude-module', 'pytest',
                '--exclude-module', 'unittest',
                '--exclude-module', 'doctest',
                '--collect-all', 'PyQt5.Qt',
                '--log-level', 'DEBUG',
                '--codesign-identity', '-',  # Ad-hoc signing for development
                '--osx-bundle-identifier', 'com.heavymeta.metavinci',
                '--hidden-import', 'macos_install_helper',
            ]
            if icon_file.exists():
                pyinstaller_cmd.extend(['--icon', str(icon_file)])
            pyinstaller_cmd.append('metavinci.py')
            # DO NOT add '--onefile' for macOS
        elif target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
            pyinstaller_cmd = [
                'pyinstaller',
                '--noconsole',
                '--onefile',
                f'--distpath={dist_dir}',
                '--exclude-module', 'pytest',
                '--exclude-module', 'unittest',
                '--exclude-module', 'doctest',
                '--collect-all', 'PyQt5.Qt',
            ]
            if icon_file.exists():
                pyinstaller_cmd.extend(['--icon', str(icon_file)])
            pyinstaller_cmd.append('metavinci.py')
        else:
            pyinstaller_cmd = [
                'pyinstaller',
                '--noconsole',
                '--onefile',
                '--strip',  # Strip debug symbols (only for non-Windows)
                f'--distpath={dist_dir}',
                '--exclude-module', 'pytest',
                '--exclude-module', 'unittest',
                '--exclude-module', 'doctest',
                '--collect-all', 'PyQt5.Qt',
                '--hidden-import', 'PyQt5.sip',
            ]
            if icon_file.exists():
                pyinstaller_cmd.extend(['--icon', str(icon_file)])
            pyinstaller_cmd.append('metavinci.py')
        
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

            # Also include imageformats (qgif plugin) so QMovie can load GIFs
            img_plugins = _os.path.join(_os.path.dirname(PyQt5.__file__), 'Qt', 'plugins', 'imageformats')
            if _os.path.exists(img_plugins) and _os.listdir(img_plugins):
                if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
                    pyinstaller_cmd.extend(['--add-data', f'{img_plugins};PyQt5/Qt/plugins/imageformats'])
                else:
                    pyinstaller_cmd.extend(['--add-data', f'{img_plugins}:PyQt5/Qt/plugins/imageformats'])
            else:
                print(f"[INFO] Qt imageformats directory not found or empty, GIFs may not load.")
        except Exception as e:
            print(f"[WARN] Could not add PyQt5 Qt platforms: {e}")
        
        # Add icon if it exists
        if icon_file.exists():
            pyinstaller_cmd.extend(['--icon', str(icon_file)])
        else:
            print(f"Warning: Icon file {icon_file} not found")
        
        print(f"Building for {target_platform or 'current platform'}...")
        print(f"Command: {' '.join(pyinstaller_cmd)}")
        
        try:
            proc = subprocess.run(pyinstaller_cmd, cwd=str(self.build_dir), capture_output=True, text=True)
            if proc.returncode != 0:
                print("[ERROR] PyInstaller failed")
                print("[STDOUT]\n" + (proc.stdout or ""))
                print("[STDERR]\n" + (proc.stderr or ""))
                return False
            
            # Analyze the built executable or .app size
            if target_platform == 'macos':
                app_path = dist_dir / 'metavinci_desktop.app'
                if app_path.exists():
                    size_mb = sum(f.stat().st_size for f in app_path.rglob('*')) / (1024 * 1024)
                    print(f"Build completed successfully!")
                    print(f".app bundle size: {size_mb:.2f} MB")
                else:
                    print(f"Build completed but .app bundle not found at {app_path}")
                    return False
            else:
                executable_name = 'metavinci'
                if target_platform == 'windows' or (target_platform is None and self.platform_manager.is_windows):
                    executable_name += '.exe'
                executable_path = dist_dir / executable_name
                if executable_path.exists():
                    size_mb = executable_path.stat().st_size / (1024 * 1024)
                    print(f"Build completed successfully!")
                    print(f"Executable size: {size_mb:.2f} MB")
                    if size_mb > 50:
                        print(f"[WARN] Large executable size ({size_mb:.2f} MB) - consider optimizing dependencies")
                    elif size_mb > 30:
                        print(f"[SIZE] Moderate executable size ({size_mb:.2f} MB)")
                    else:
                        print(f"[OK] Good executable size ({size_mb:.2f} MB)")
                else:
                    print(f"Build completed but executable not found at {executable_path}")
                    return False
            return True
        except Exception as e:
            print(f"Build failed with exception: {e}")
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