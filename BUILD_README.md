# Cross-Platform Build Instructions

This project now supports building executables for Linux, macOS, and Windows.

## Build Scripts

### 1. Original build.py (Updated)
The original build script has been updated for cross-platform compatibility.

**Usage:**
```bash
# Build for current platform
python build.py

# Build for specific platform
python build.py --mac
python build.py --windows

# Build and install to local directory
python build.py --test
```

### 2. New build_cross_platform.py (Recommended)
A more comprehensive cross-platform build script with better features.

**Usage:**
```bash
# Build for current platform
python build_cross_platform.py

# Build for specific platform
python build_cross_platform.py --platform linux
python build_cross_platform.py --platform macos
python build_cross_platform.py --platform windows

# Build for all platforms
python build_cross_platform.py --all

# Build and install to local directory
python build_cross_platform.py --platform linux --install

# Clean build directory
python build_cross_platform.py --clean
```

## Platform-Specific Requirements

### Linux
- PyInstaller
- Python 3.6+
- Icon file: `hvym_logo_64.png` (optional)

### macOS
- PyInstaller
- Python 3.6+
- Icon file: `hvym_logo_64.icns` (optional)
- May require code signing for distribution

### Windows
- PyInstaller
- Python 3.6+
- Icon file: `hvym_logo_64.ico` (optional)
- Visual Studio Build Tools (if building from source)

## Installation

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
python build_cross_platform.py --platform linux --install
```

## Output Locations

### Build Output
- Linux: `build/dist/linux/metavinci`
- macOS: `build/dist/mac/metavinci`
- Windows: `build/dist/windows/metavinci.exe`

### Local Installation
- Linux: `~/.metavinci/bin/metavinci`
- macOS: `~/Library/Application Support/Metavinci/bin/metavinci`
- Windows: `%LOCALAPPDATA%\Metavinci\bin\metavinci.exe`

## Troubleshooting

### Common Issues

1. **PyInstaller not found**
   ```bash
   pip install pyinstaller
   ```

2. **Icon file not found**
   - Create appropriate icon files for each platform
   - Linux: PNG format
   - macOS: ICNS format
   - Windows: ICO format

3. **Permission denied (Unix systems)**
   ```bash
   chmod +x build_cross_platform.py
   ```

4. **Build fails on Windows**
   - Ensure Visual Studio Build Tools are installed
   - Try running as Administrator

### Platform-Specific Notes

**Linux:**
- Should work out of the box
- Executable permissions are automatically set

**macOS:**
- May require code signing for distribution
- Gatekeeper may block unsigned executables

**Windows:**
- Antivirus software may flag PyInstaller executables
- May require running as Administrator for installation

## Cross-Platform Testing

### Pre-build Testing
Before building, verify all dependencies are available:

```bash
python test_build_dependencies.py
```

This will check that all required modules and files are present.

### Post-build Testing
After building, test the cross-platform functionality:

```bash
python test_cross_platform.py
```

This will verify that the platform detection and path resolution work correctly. 

## GitHub Installer Build & Release

A dedicated workflow, `.github/workflows/build-installers.yml`, builds and publishes platform-specific installers for each release.

### Workflow Triggers

- **Version tags**: Any tag matching `v0.00`, `v0.01`, etc.
- **Keyword**: Any tag containing `installers`
- **Manual**: Can be triggered manually from the GitHub Actions tab.

### Installer Outputs

- **Linux**: `.deb` package in `release/linux/`
- **Windows**: `.msi` installer in `dist/` (creates Start Menu and Desktop shortcuts)
- **macOS**: `.zip` archive in `release/mac/`

All installers are uploaded as release assets on GitHub.

### Local Installer Build

To build installers locally for a specific platform and version:

```bash
python build_installers.py --platform linux --version v0.01
python setup.py bdist_msi  # for Windows MSI
python build_installers.py --platform macos --version v0.01
```

This will generate the appropriate installer in the `release/` (Linux/macOS) or `dist/` (Windows MSI) subdirectory. 