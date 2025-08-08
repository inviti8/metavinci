# Metavinci Uninstall Guide

This guide explains how to completely uninstall Metavinci and clean up the `hvym` CLI on all supported platforms.

## Overview

When you uninstall Metavinci, the `hvym` CLI that was downloaded and installed by the application should also be removed. This guide provides platform-specific instructions for complete cleanup.

## Platform-Specific Uninstallation

### macOS

#### Automatic Cleanup (Recommended)
1. **Remove the Metavinci app bundle** from `/Applications/`
2. **Run the uninstall script** (included in the DMG/ZIP):
   ```bash
   chmod +x uninstall_macos.sh
   ./uninstall_macos.sh
   ```

#### Manual Cleanup
If the uninstall script is not available, manually remove:
```bash
# Remove hvym CLI binary
rm -f ~/Library/Application\ Support/Metavinci/bin/hvym-macos

# Remove empty directories
rmdir ~/Library/Application\ Support/Metavinci/bin 2>/dev/null || true
rmdir ~/Library/Application\ Support/Metavinci 2>/dev/null || true
```

### Windows

#### Automatic Cleanup (Recommended)
1. **Uninstall Metavinci** from Programs and Features
2. **Run the uninstall script** (included in the MSI):
   ```cmd
   uninstall_windows.bat
   ```

#### Manual Cleanup
If the uninstall script is not available, manually remove:
```cmd
# Remove hvym CLI binary
del "%LOCALAPPDATA%\heavymeta-cli\hvym-windows.exe"

# Remove empty directory
rmdir "%LOCALAPPDATA%\heavymeta-cli" 2>nul
```

### Linux

#### Automatic Cleanup (Recommended)
1. **Uninstall the Debian package**:
   ```bash
   sudo dpkg -r com.metavinci.desktop
   ```
2. **Run the uninstall script** (installed to system path):
   ```bash
   metavinci-uninstall
   ```

#### Manual Cleanup
If the uninstall script is not available, manually remove:
```bash
# Remove hvym CLI binary
rm -f ~/.local/share/heavymeta-cli/hvym-linux

# Remove empty directory
rmdir ~/.local/share/heavymeta-cli 2>/dev/null || true
```

## Programmatic Cleanup

### Using the Application
The Metavinci application includes a built-in cleanup function:

```python
# In the application, you can call:
app._delete_hvym()
```

### Using the macOS Helper
On macOS, you can use the installation helper for cleanup:

```python
from macos_install_helper import MacOSInstallHelper

helper = MacOSInstallHelper()
helper.uninstall_hvym_cli()
```

## Verification

After uninstallation, verify that the `hvym` CLI has been removed:

### macOS
```bash
ls ~/Library/Application\ Support/Metavinci/bin/hvym-macos
# Should return "No such file or directory"
```

### Windows
```cmd
dir "%LOCALAPPDATA%\heavymeta-cli\hvym-windows.exe"
# Should return "File Not Found"
```

### Linux
```bash
ls ~/.local/share/heavymeta-cli/hvym-linux
# Should return "No such file or directory"
```

## Troubleshooting

### Permission Issues
If you encounter permission errors during cleanup:

**macOS:**
```bash
sudo chmod -R 755 ~/Library/Application\ Support/Metavinci
```

**Linux:**
```bash
sudo chmod -R 755 ~/.local/share/heavymeta-cli
```

**Windows:**
Run the uninstall script as Administrator.

### Stuck Files
If files cannot be deleted:

1. **Ensure no processes are using the files**
2. **Restart the system** and try again
3. **Use force deletion** (use with caution):
   ```bash
   # macOS/Linux
   rm -rf ~/Library/Application\ Support/Metavinci
   rm -rf ~/.local/share/heavymeta-cli
   
   # Windows
   rmdir /s /q "%LOCALAPPDATA%\heavymeta-cli"
   ```

## Reinstallation

After complete uninstallation, you can reinstall Metavinci fresh:

1. Download the latest installer for your platform
2. Run the installer
3. The `hvym` CLI will be automatically downloaded and installed when needed

## Support

If you encounter issues with uninstallation:

1. Check the platform-specific troubleshooting section above
2. Verify file permissions and ownership
3. Ensure no background processes are using the files
4. Contact support with specific error messages and platform details
