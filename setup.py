from cx_Freeze import setup, Executable

shortcut_table = [
    (
        "DesktopShortcut",        # Shortcut
        "DesktopFolder",          # Directory_
        "Metavinci",              # Name
        "TARGETDIR",              # Component_
        "[TARGETDIR]metavinci.exe", # Target
        None,                     # Arguments
        "Metavinci Desktop App",  # Description
        None,                     # Hotkey
        None,                     # Icon
        None,                     # IconIndex
        None,                     # ShowCmd
        'TARGETDIR'               # WkDir
    ),
    (
        "StartMenuShortcut",      # Shortcut
        "ProgramMenuFolder",      # Directory_
        "Metavinci",              # Name
        "TARGETDIR",              # Component_
        "[TARGETDIR]metavinci.exe", # Target
        None,                     # Arguments
        "Metavinci Desktop App",  # Description
        None,                     # Hotkey
        None,                     # Icon
        None,                     # IconIndex
        None,                     # ShowCmd
        'TARGETDIR'               # WkDir
    ),
]

msi_data = {
    "Shortcut": shortcut_table,
}

setup(
    name="Metavinci",
    version="0.1",
    description="Metavinci Desktop App",
    executables=[Executable("metavinci.py", base="Win32GUI", icon="metavinci_desktop.ico")],
    options={
        "build_exe": {
            "include_files": ["images", "data", "service"],
        },
        "bdist_msi": {
            "add_to_path": False,
            "initial_target_dir": r"[ProgramFilesFolder]\\Metavinci",
        }
    },
    msi_data=msi_data,
) 