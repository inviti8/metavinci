import shutil
import subprocess
from pathlib import Path
import argparse
import platform
import os
import sys
import zipfile

# Import our platform manager
from platform_manager import PlatformManager

def run_generate_icons():
    """Ensure .ico and .icns files exist by running generate_icons.py."""
    result = subprocess.run([sys.executable, 'generate_icons.py'])
    if result.returncode != 0:
        print("Failed to generate icons. Aborting.")
        sys.exit(1)

def _clean_dir(dir):
    print(f"Cleaning {dir}")
    if not dir.exists():
        dir.mkdir(parents=True)
    else:
        for item in dir.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

def build_linux_installer(version):
    bin_name = 'metavinci_desktop'
    cwd = Path.cwd()
    build_dir = cwd / "build"
    dist_dir = cwd / "dist"
    release_dir = cwd / "release"
    release_linux_dir = release_dir / "linux"
    src_bin = dist_dir / bin_name
    src_icon = cwd / f'{bin_name}.png'
    src_ctrl = cwd / 'linux' / 'control'
    src_desktop = cwd / 'linux' / 'metavinci.desktop'
    pkg_dir = cwd / f'metavinci_desktop_{version}'
    deb_dir = pkg_dir / 'DEBIAN'
    usr_dir = pkg_dir / 'usr'
    bin_dir = usr_dir / 'bin'
    share_dir = usr_dir / 'share'
    app_dir = share_dir  / 'applications'
    icon_dir = share_dir / 'icons'
    hicolor_dir = icon_dir / 'hicolor'
    icon_size_dir = hicolor_dir / '512x512'
    icon_apps_dir = icon_size_dir / 'apps'
    dest_ctrl = deb_dir / 'control'
    dest_desktop = app_dir / 'metavinci.desktop'
    dest_bin = bin_dir / bin_name
    deb = cwd / f'metavinci_desktop_{version}.deb'
    dest_deb = release_linux_dir / f'metavinci-desktop_{version}_amd64.deb'
    dest_icon = icon_apps_dir / f'{bin_name}.png'

    # Clean and prepare directories
    _clean_dir(pkg_dir)
    _clean_dir(release_dir)
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    for d in [release_dir, release_linux_dir, pkg_dir, deb_dir, usr_dir, bin_dir, share_dir, app_dir, icon_dir, hicolor_dir, icon_size_dir, icon_apps_dir]:
        d.mkdir(parents=True, exist_ok=True)
    if deb.is_file():
        deb.unlink()

    # Copy files
    shutil.copy(src_ctrl, dest_ctrl)
    shutil.copy(src_desktop, dest_desktop)
    shutil.copy(src_bin,  dest_bin)
    shutil.copy(src_icon,  dest_icon)

    print("Building debian package...")
    subprocess.run(['dpkg-deb', '--build', str(pkg_dir)], check=True)
    print("Package created: " + str(deb))
    shutil.move(str(deb), str(dest_deb))
    print(f"Debian package moved to {dest_deb}")

def build_windows_installer(version):
    bin_name = 'metavinci_desktop.exe'
    cwd = Path.cwd()
    dist_dir = cwd / "dist"
    release_dir = cwd / "release"
    release_win_dir = release_dir / "windows"
    exe_path = dist_dir / bin_name
    ico_path = cwd / 'metavinci_desktop.ico'
    readme = cwd / 'README.md'
    license_file = cwd / 'LICENSE' if (cwd / 'LICENSE').exists() else None
    zip_name = f'metavinci-desktop_{version}_win64.zip'
    zip_path = release_win_dir / zip_name

    # Clean and prepare directories
    release_win_dir.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    # Collect files
    files = [(exe_path, bin_name), (ico_path, 'metavinci_desktop.ico')]
    if readme.exists():
        files.append((readme, 'README.md'))
    if license_file and license_file.exists():
        files.append((license_file, 'LICENSE'))

    # Create ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            if not src.exists():
                print(f"Warning: {src} not found, skipping.")
                continue
            z.write(src, arc)
    print(f"Windows ZIP installer created: {zip_path}")

def build_macos_installer(version):
    bin_name = 'metavinci_desktop.app'
    cwd = Path.cwd()
    dist_dir = cwd / "dist"
    release_dir = cwd / "release"
    release_mac_dir = release_dir / "mac"
    app_path = dist_dir / bin_name
    icns_path = cwd / 'metavinci_desktop.icns'
    readme = cwd / 'README.md'
    license_file = cwd / 'LICENSE' if (cwd / 'LICENSE').exists() else None
    zip_name = f'metavinci-desktop_{version}_macos.zip'
    zip_path = release_mac_dir / zip_name

    # Clean and prepare directories
    release_mac_dir.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    # Collect files
    files = [(app_path, f'metavinci_desktop.app')]
    if icns_path.exists():
        files.append((icns_path, 'metavinci_desktop.icns'))
    if readme.exists():
        files.append((readme, 'README.md'))
    if license_file and license_file.exists():
        files.append((license_file, 'LICENSE'))

    # Create ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            if not src.exists():
                print(f"Warning: {src} not found, skipping.")
                continue
            if src.is_dir():
                for root, _, files_in_dir in os.walk(src):
                    for file in files_in_dir:
                        file_path = Path(root) / file
                        arcname = os.path.join(arc, os.path.relpath(file_path, src))
                        z.write(file_path, arcname)
            else:
                z.write(src, arc)
    print(f"macOS ZIP installer created: {zip_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=['linux', 'macos', 'windows'], required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()

    # Ensure icons exist
    run_generate_icons()

    # Build the cross-platform binary first
    subprocess.run([sys.executable, 'build_cross_platform.py', '--platform', args.platform], check=True)

    if args.platform == 'linux':
        build_linux_installer(args.version)
    elif args.platform == 'windows':
        build_windows_installer(args.version)
    elif args.platform == 'macos':
        build_macos_installer(args.version)
    else:
        print(f"Unknown platform: {args.platform}")
        sys.exit(1)

if __name__ == '__main__':
    main()