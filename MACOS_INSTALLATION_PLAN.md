# macOS Installation Fix Plan for Metavinci

## Problem Analysis

Metavinci faces several challenges on macOS due to Apple's strict security controls:

1. **Network Security**: Apps cannot download and execute binaries without proper entitlements
2. **File System Permissions**: Apps have limited access to system directories
3. **Code Execution**: Downloaded executables cannot run without explicit user approval
4. **Sandbox Restrictions**: Apps are sandboxed and have limited system access

## Root Cause

The application tries to download and install the `hvym` CLI tool when it starts, but macOS prevents this due to:
- Missing entitlements for network access and file system operations
- Attempting to write to system directories that require elevated permissions
- Trying to execute downloaded binaries without proper code signing

## Solution Plan

### Phase 1: Entitlements and Code Signing (Critical)

#### 1.1 Create macOS Entitlements File ✅
- **File**: `metavinci.entitlements`
- **Purpose**: Grants necessary permissions for network access, file operations, and code execution
- **Key Entitlements**:
  - `com.apple.security.network.client` - Network access for downloads
  - `com.apple.security.files.user-selected.read-write` - File system access
  - `com.apple.security.files.downloads.read-write` - Downloads folder access
  - `com.apple.security.cs.disable-library-validation` - Allow execution of downloaded binaries

#### 1.2 Update PyInstaller Configuration ✅
- **File**: `build_cross_platform.py`
- **Changes**: Added macOS-specific options for code signing and bundle identifier
- **Purpose**: Ensure proper app bundle structure and signing

#### 1.3 Update GitHub Workflow (Pending)
- **File**: `.github/workflows/build-installers.yml`
- **Changes Needed**:
  ```yaml
  - name: Code sign .app with hardened runtime and entitlements
    run: |
      codesign --force --options runtime --timestamp \
        --entitlements metavinci.entitlements \
        --sign "$APP_IDENTITY_HASH" --deep "$APP_BUNDLE"
  ```

### Phase 2: Installation Directory Strategy ✅

#### 2.1 Update Platform Manager
- **File**: `platform_manager.py`
- **Changes**: Modified macOS paths to use user-accessible directories
- **New Paths**:
  - Config: `~/Library/Application Support/Metavinci/`
  - Binaries: `~/Library/Application Support/Metavinci/bin/`
- **Benefits**: No elevated permissions required, follows macOS conventions

### Phase 3: macOS-Specific Installation Helper ✅

#### 3.1 Create Installation Helper
- **File**: `macos_install_helper.py`
- **Purpose**: Handle macOS-specific installation requirements
- **Features**:
  - Proper directory creation with correct permissions
  - Network download with error handling
  - Installation verification
  - Permission checking

#### 3.2 Update Main Application
- **File**: `metavinci.py`
- **Changes**: Modified `download_and_install_hvym_cli()` to use macOS helper
- **Fallback**: Maintains original method for other platforms

### Phase 4: Testing and Validation (Next Steps)

#### 4.1 Local Testing
```bash
# Test the macOS installation helper
python3 macos_install_helper.py

# Test the full application
python3 metavinci.py
```

#### 4.2 Build Testing
```bash
# Test the build process
python3 build_cross_platform.py --platform macos

# Test the installer creation
python3 build_installers.py --platform macos --version v0.01
```

#### 4.3 Integration Testing
- Test on clean macOS systems
- Test with different security settings
- Test with Gatekeeper enabled/disabled
- Test the complete user journey

## Implementation Status

### ✅ Completed
1. Created entitlements file
2. Updated platform manager for macOS paths
3. Created macOS installation helper
4. Updated main application to use helper
5. Updated PyInstaller configuration

### 🔄 In Progress
1. Testing the installation helper
2. Validating the build process

### ⏳ Pending
1. Update GitHub workflow with entitlements
2. Test on actual macOS systems
3. Validate notarization process
4. Create user documentation

## Next Steps

### Immediate (This Week)
1. **Test the macOS installation helper** on a macOS system
2. **Update the GitHub workflow** to include entitlements in code signing
3. **Test the build process** to ensure the app bundle is created correctly

### Short Term (Next Week)
1. **Test on clean macOS systems** with different security settings
2. **Validate the notarization process** with the new entitlements
3. **Create user documentation** for macOS installation

### Medium Term (Next Month)
1. **Monitor user feedback** after release
2. **Iterate on the solution** based on real-world usage
3. **Consider additional improvements** like pre-bundling dependencies

## Technical Details

### Entitlements Explanation
The entitlements file grants the app specific permissions:
- **Network Client**: Allows downloading files from the internet
- **File System Access**: Allows reading/writing to user-selected locations
- **Code Execution**: Allows running downloaded binaries
- **Library Validation**: Disables strict library validation for downloaded code

### Directory Structure
```
~/Library/Application Support/Metavinci/
├── bin/
│   ├── hvym-macos-arm64
│   ├── hvym-macos-amd64
│   └── hvym-press-macos
├── db.json
└── other config files
```

### Installation Flow
1. App starts and checks for `hvym` CLI
2. If not found, uses macOS helper to download and install
3. Helper creates directories with proper permissions
4. Downloads binary from GitHub releases
5. Extracts and installs with executable permissions
6. Verifies installation by running a test command

## Troubleshooting

### Common Issues
1. **Permission Denied**: Check if directories exist and have correct permissions
2. **Network Error**: Verify internet connection and GitHub API access
3. **Execution Failed**: Check if binary has executable permissions
4. **Code Signing**: Ensure app is properly signed with entitlements

### Debug Commands
```bash
# Check installation status
python3 macos_install_helper.py

# Check permissions
ls -la ~/Library/Application\ Support/Metavinci/

# Test hvym CLI
~/Library/Application\ Support/Metavinci/bin/hvym-macos-$(uname -m | sed 's/aarch64\|arm.*/arm64/; s/x86_64\|amd.*/amd64/') --version

# Check app bundle
codesign -dv --verbose=4 /path/to/metavinci_desktop.app
```

## Success Criteria

The solution is successful when:
1. ✅ Metavinci can download and install the `hvym` CLI on macOS
2. ✅ The installed CLI can be executed without permission errors
3. ✅ The app passes macOS notarization
4. ✅ Users can install and run the app without manual intervention
5. ✅ The app works consistently across different macOS versions and security settings

## Risk Mitigation

### High Risk
- **Notarization Failure**: Test thoroughly with Apple's notarization service
- **Permission Issues**: Test on various macOS configurations
- **User Experience**: Ensure clear error messages and fallback options

### Medium Risk
- **Network Issues**: Implement retry logic and offline fallbacks
- **Version Compatibility**: Test with different macOS versions
- **Security Updates**: Monitor for changes in macOS security policies

### Low Risk
- **Performance**: Monitor app startup time with new installation process
- **File Size**: Consider impact of additional helper code
- **Maintenance**: Ensure helper code is maintainable and well-documented
