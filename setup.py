from cx_Freeze import setup, Executable

exe_name = "metavinci.exe"
publisher = "Heavymeta"
upgrade_code = "{12345678-1234-1234-1234-1234567890AB}"  # Replace with a real GUID for production

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

property_table = [
    ("MANUFACTURER", "HEAVYMETA®"),
    ("PUBLISHER", "HEAVYMETA®"),
]

msi_data = {
    "Shortcut": shortcut_table,
    "Property": property_table,
}

setup(
    name="Metavinci",
    version="0.1",
    description="Metavinci Desktop App",
    author=publisher,
    executables=executables,
    options={
        "build_exe": {
            "include_files": [
                "images", "data", "service", "metavinci_desktop.ico",
                "build\\dist\\windows\\metavinci.exe"
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