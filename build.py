import shutil
import subprocess
from pathlib import Path
import argparse
import platform
import os

# Import our platform manager
from platform_manager import PlatformManager

parser = argparse.ArgumentParser()
parser.add_argument("--test", help="copy executable to local install directory", action="store_true")
parser.add_argument("--mac", help="copy executable to mac local install directory", action="store_true")
parser.add_argument("--windows", help="copy executable to windows local install directory", action="store_true")
args = parser.parse_args()

# Initialize platform manager
platform_manager = PlatformManager()

# get current working directory
cwd = Path.cwd()

# source files
src_file1 = cwd / 'metavinci.py'
src_file2 = cwd / 'requirements.txt'

# Platform-specific icon file
if platform_manager.is_windows:
    ico_file = cwd / 'hvym_logo_64.ico'
elif platform_manager.is_macos:
    ico_file = cwd / 'hvym_logo_64.icns'  # macOS uses .icns
else:  # Linux
    ico_file = cwd / 'hvym_logo_64.png'  # Linux can use PNG

# target directories for the build folder and files
build_dir = cwd / 'build' 
img_dir = cwd / 'images'
img_copied_dir = build_dir / 'images'
data_dir = cwd / 'data'
data_copied_dir = build_dir / 'data'
service_dir = cwd / 'service'
service_copied_dir = build_dir / 'service'

# Platform-specific dist directory
if args.mac:
    dist_dir = build_dir / 'dist' / 'mac'
elif args.windows:
    dist_dir = build_dir / 'dist' / 'windows'
else:  # Linux (default)
    dist_dir = build_dir / 'dist' / 'linux'

# check if build dir exists, if not create it
if not build_dir.exists():
    build_dir.mkdir()
else: # delete all files inside the directory
    for item in build_dir.iterdir():
        if item.name != '.git' and item.name != 'README.md' and item.name != 'install.sh':
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

# copy source files to build directory
shutil.copy(src_file1, build_dir)
shutil.copy(src_file2, build_dir)

# Copy new cross-platform dependency files
dependency_files = ['platform_manager.py', 'download_utils.py', 'file_utils.py']
for dep_file in dependency_files:
    dep_path = cwd / dep_file
    if dep_path.exists():
        shutil.copy(dep_path, build_dir)
    else:
        print(f"Warning: {dep_file} not found")

shutil.copytree(img_dir, build_dir / img_dir.name)
shutil.copytree(data_dir, build_dir / data_dir.name)
shutil.copytree(service_dir, build_dir / service_dir.name)

# install dependencies from requirements.txt
subprocess.run(['pip', 'install', '-r', str(build_dir / src_file2.name)], cwd=str(build_dir), check=True)

# Platform-specific PyInstaller command
icon_arg = f'--icon={str(ico_file)}' if ico_file.exists() else ''

# Build the python script into an executable using PyInstaller
pyinstaller_cmd = [
    'pyinstaller', '--noconsole', '--onefile',
    f'--distpath={dist_dir}',
    '--add-data', 'images:images',
    '--add-data', 'data:data',
    '--add-data', 'service:service',
    str(build_dir / src_file1.name)
]

if icon_arg:
    pyinstaller_cmd.insert(3, icon_arg)

subprocess.run(pyinstaller_cmd, cwd=str(build_dir), check=True)

# copy built executable to destination directory
if args.test:
    # Use platform-specific paths
    config_path = platform_manager.get_config_path()
    bin_dir = config_path / 'bin'
    test_dir = bin_dir / 'metavinci'
    
    # Ensure bin directory exists
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    executable_name = src_file1.stem
    if platform_manager.is_windows:
        executable_name += '.exe'
    
    shutil.copy(str(dist_dir / executable_name), test_dir)
    
    # Set executable permissions (Unix systems only)
    if not platform_manager.is_windows:
        try:
            os.chmod(test_dir, 0o755)
        except Exception as e:
            print(f"Warning: Could not set executable permissions: {e}")
