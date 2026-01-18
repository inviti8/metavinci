from cx_Freeze import setup, Executable
import os

exe_name = "metavinci.exe"
publisher = "HEAVYMETA"
# Unique upgrade code for MSI - this should remain constant across versions
# to allow proper upgrades/uninstalls
upgrade_code = "{2A90AEB2-49BA-49BC-BF80-30CD18EB3298}"

# Get version from environment or default
version = os.environ.get('BUILD_VERSION', '0.1.0')
# Clean version string (remove 'v' prefix, '-no-notarize' suffix, 'installers-' prefix)
import re
version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', version)
if version_match:
    version = version_match.group(1)
else:
    version = '0.1.0'

executables = [Executable("dummy.py", base=None, target_name="dummy.exe")]

shortcut_table = [
    (
        "DesktopShortcut",
        "DesktopFolder",
        "Metavinci",
        "TARGETDIR",
        "[TARGETDIR]metavinci.exe",  # Points to PyInstaller EXE
        "metavinci_desktop.ico",
        "Metavinci Desktop App",
        None, None, None, None, 'TARGETDIR'
    ),
    (
        "StartMenuShortcut",
        "ProgramMenuFolder",
        "Metavinci",
        "TARGETDIR",
        "[TARGETDIR]metavinci.exe",  # Points to PyInstaller EXE
        "metavinci_desktop.ico",
        "Metavinci Desktop App",
        None, None, None, None, 'Metavinci'
    ),
]

msi_data = {
    "Shortcut": shortcut_table,
}

setup(
    name="Metavinci",
    version=version,
    description="Metavinci Desktop Application",
    author=publisher,
    author_email="metavinci@heavymeta.art",
    url="https://heavymeta.io",
    executables=executables,
    options={
        "build_exe": {
            "include_files": [
                "images", "data", "service", "metavinci_desktop.ico",
                "build\\dist\\windows\\metavinci.exe",
                ("uninstall_windows.bat", "uninstall_windows.bat"),
            ],
        },
        "bdist_msi": {
            "add_to_path": False,
            "initial_target_dir": r"[LocalAppDataFolder]\\Programs\\Metavinci",
            "upgrade_code": upgrade_code,
            "all_users": False,
            "install_icon": "metavinci_desktop.ico",
            "data": msi_data,
        }
    },
) 