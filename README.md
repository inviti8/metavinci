## Official Metavinci Daemon repo

The heavymeta cli is a toolset that empowers artist to leverage the power of Web 3.0 to take true ownership of their digital creations.

Installation:

```
curl -L https://raw.githubusercontent.com/inviti8/metavinci/main/install.sh | bash
```

## Cross-Platform Installers

Official installers for Linux (.deb), Windows (.msi), and macOS (.zip) are available on the [GitHub Releases](https://github.com/inviti8/metavinci/releases) page. These are built and published automatically for each tagged release (e.g., `v0.01`, `v0.02`, etc.) or when the tag contains the keyword `installers`.

### Windows Installation

1. **Download the following files from the latest release**:
   - `metavinci-x.x.x.msi` (the installer)
   - `install-win-metavinci-cert.ps1` (certificate installation script)
   - `heavymeta-code-sign.cer` (code signing certificate)

2. **Install the Certificate (one-time setup)**:
   - Right-click on `install-win-metavinci-cert.ps1` and select "Run with PowerShell"
   - When prompted, confirm running the script
   - The script will automatically install the certificate to the Trusted Publishers store

3. **Run the Installer**:
   - Double-click `metavinci-x.x.x.msi`
   - Follow the installation wizard
   - The application will be available in the Start Menu and as a Desktop shortcut

### Linux Installation
```bash
# Install the .deb package
sudo dpkg -i metavinci-x.x.x.deb

# Install any missing dependencies
sudo apt-get install -f
```

### macOS Installation
- Download the `.zip` file
- Extract the `.app` bundle
- Drag the application to your Applications folder
- If you see a security warning, right-click the app and select "Open" to run it


