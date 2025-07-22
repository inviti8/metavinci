from cx_Freeze import setup, Executable

exe_name = "metavinci.exe"
publisher = "Heavymeta"
upgrade_code = "{12345678-1234-1234-1234-1234567890AB}"  # Replace with a real GUID for production

shortcut_table = [
    (
        "DesktopShortcut",
        "DesktopFolder",
        "Metavinci",
        "TARGETDIR",
        f"[TARGETDIR]{exe_name}",
        None,
        "Metavinci Desktop App",
        None, None, None, None, 'TARGETDIR'
    ),
    (
        "StartMenuShortcut",
        "ProgramMenuFolder",
        "Metavinci",
        "TARGETDIR",
        f"[TARGETDIR]{exe_name}",
        None,
        "Metavinci Desktop App",
        None, None, None, None, 'TARGETDIR'
    ),
]

msi_data = {
    "Shortcut": shortcut_table,
}

setup(
    name="Metavinci",
    version="0.1",
    description="Metavinci Desktop App",
    author=publisher,
    executables=[Executable("metavinci.py", base="Win32GUI", icon="metavinci_desktop.ico", target_name=exe_name)],
    options={
        "build_exe": {
            "include_files": ["images", "data", "service", "metavinci_desktop.ico"],
        },
        "bdist_msi": {
            "add_to_path": False,
            "initial_target_dir": r"[LocalAppDataFolder]\\Programs\\Metavinci",
            "upgrade_code": upgrade_code,
            "all_users": False,
            "install_icon": "metavinci_desktop.ico",
            "msi_data": msi_data,
        }
    },
) 