from cx_Freeze import setup, Executable

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
            "shortcut_name": "Metavinci",
            "shortcut_dir": "ProgramMenuFolder",
        }
    }
) 