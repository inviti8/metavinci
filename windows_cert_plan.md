# Windows Code Signing Implementation Guide

This document outlines the process for implementing code signing for Windows installers in the Metavinci project, including certificate creation, GitHub Actions integration, and user certificate installation. This implementation is specifically designed for the HEAVYMETA organization's build process.

## Table of Contents
1. [Certificate Creation](#certificate-creation)
2. [GitHub Actions Setup](#github-actions-setup)
3. [Certificate Installation Script](#certificate-installation-script)
4. [Testing](#testing)
5. [User Documentation](#user-documentation)
6. [Security Considerations](#security-considerations)

## Certificate Creation

### Prerequisites
- Linux machine with OpenSSL installed
- For verification: A Windows machine or Wine (recommended for testing)

### Steps to Create Certificate on Linux

1. **Install OpenSSL** (if not already installed):
   ```bash
   # For Debian/Ubuntu
   sudo apt update && sudo apt install -y openssl
   
   # For RHEL/CentOS
   # sudo yum install -y openssl
   ```

2. **Create a configuration file** for the certificate (optional but recommended):
   ```bash
   cat > metavinci-cert.cnf << 'EOL'
   [ req ]
   default_bits = 4096
   default_md = sha256
   prompt = no
   encrypt_key = no
   distinguished_name = dn
   x509_extensions = v3_ca
   
   [ dn ]
   CN = HEAVYMETA Code Signing
   O = HEAVYMETA
   
   [ v3_ca ]
   basicConstraints = critical,CA:FALSE
   keyUsage = digitalSignature, nonRepudiation
   extendedKeyUsage = codeSigning
   subjectKeyIdentifier = hash
   authorityKeyIdentifier = keyid:always,issuer
   EOL
   ```

3. **Generate a private key and self-signed certificate**:
   ```bash
   # Generate private key
   openssl genrsa -out metavinci.key 4096
   
   # Generate self-signed certificate (valid for 3 years)
   openssl req -new -x509 \
       -key ./metavinci.key \
       -out ./metavinci.crt \
       -days 1095 \
       -config ./heavymeta-cert.cnf \
       -extensions v3_ca
   
   # Verify the certificate
   openssl x509 -in metavinci.crt -text -noout
   ```

4. **Create PKCS#12 (PFX) file** (for Windows compatibility):
   ```bash
   # Set a strong password
   CERT_PASSWORD="YourSecurePassword123!"
   
   # Create PFX file
   openssl pkcs12 -export \
       -out metavinci.pfx \
       -inkey metavinci.key \
       -in metavinci.crt \
       -password pass:${CERT_PASSWORD} \
       -name "Metavinci Code Signing"
   
   # Create CER file (for distribution)
   openssl x509 -inform PEM -in metavinci.crt -outform DER -out metavinci.cer
   ```

5. **Prepare for GitHub Actions**:
   ```bash
   # Convert PFX to base64 for GitHub Secrets
   base64 -w 0 metavinci.pfx > certificate.txt
   
   # The password will also be needed in GitHub Secrets
   echo "Certificate password: ${CERT_PASSWORD}"
   ```

### Verification (Recommended)

1. **Check certificate details**:
   ```bash
   openssl pkcs12 -info -in metavinci.pfx -nodes -passin pass:${CERT_PASSWORD}
   ```

2. **Test with signtool** (if you have Wine or Windows):
   ```bash
   # Install signtool on Linux (using Mono's version)
   # For Debian/Ubuntu:
   sudo apt install -y mono-devel
   
   # Sign a test file
   SIGNTOOL="/usr/lib/mono/4.5/signcode"
   ${SIGNTOOL} sign \
       -spc metavinci.cer \
       -v metavinci.key \
       -a sha256 \
       -$ commercial \
       -n "Metavinci Application" \
       -t http://timestamp.digicert.com \
       your_application.exe
   ```

### Files to Secure
- `heavymeta.key`: Your private key (keep this secure!)
- `heavymeta.pfx`: Contains both certificate and private key (keep secure)
- `heavymeta.crt`: Public certificate (can be distributed)
- `heavymeta.cer`: Public certificate in DER format (for Windows users)
- `certificate.txt`: Base64-encoded PFX for GitHub Secrets

## GitHub Actions Setup

1. **Add GitHub Secrets**:
   - Go to your GitHub repository
   - Navigate to Settings > Secrets and variables > Actions
   - Add the following secrets:
     - `WINDOWS_SIGNING_CERT`: Paste the base64-encoded content of `heavymeta.pfx`
   - `WINDOWS_SIGNING_PASSWORD`: The password used when exporting the PFX (store this securely in GitHub Secrets)

2. **Update GitHub Actions Workflow**:
   Add these steps to your `build-windows-installer` job after the MSI is built:

   ```yaml
   - name: Sign Windows MSI
     if: success()
     run: |
       # Write the certificate to a secure temporary file
       $certBytes = [System.Convert]::FromBase64String("${{ secrets.WINDOWS_SIGNING_CERT }}")
       $certPath = "$env:RUNNER_TEMP\cert.pfx"
       [System.IO.File]::WriteAllBytes($certPath, $certBytes)
       
       # Sign the MSI using the installed Windows SDK signtool
       $signTool = "$env:ProgramFiles (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
       $msiFile = (Get-ChildItem -Path "dist\*.msi").FullName
       
       # Sign with SHA-256 and timestamp
       & "$signTool" sign `
           /f "$certPath" `
           /p "${{ secrets.WINDOWS_SIGNING_PASSWORD }}" `
           /fd sha256 `
           /td sha256 `
           /tr "http://timestamp.digicert.com" `
           /v `
           "$msiFile"
       
       # Verify the signature
       & "$signTool" verify /pa /v "$msiFile"
       
       # Clean up the certificate file
       if (Test-Path $certPath) {
           Remove-Item -Path $certPath -Force
       }
   ```

## Certificate Installation Script

Create a file named `install-certificate.ps1` in your repository:
```powershell
<#
.SYNOPSIS
    Installs the HEAVYMETA code signing certificate to the Trusted Publishers store.

.DESCRIPTION
    This script installs the HEAVYMETA code signing certificate to the Local Machine's
    Trusted Publishers store, allowing the signed application to run without warnings.

.PARAMETER CertificatePath
    The path to the .cer certificate file to install.

.EXAMPLE
    .\install-certificate.ps1 -CertificatePath ".\heavymeta-code-sign.cer"
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateScript({
        if (-Not ($_ | Test-Path) ) {
            throw "Certificate file not found at $_"
        }
        if ($_ -notmatch '\.(cer|p7b|p7c|p7s|p12|pfx|pem|crl|der)$') {
            throw "The specified certificate file must be a valid certificate file"
        }
        return $true
    })]
    [string]$CertificatePath
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

try {
    Write-Host "Installing certificate from: $CertificatePath" -ForegroundColor Cyan
    
    # Import the certificate
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import($CertificatePath)
    
    # Add to Trusted Publishers store
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPublisher", "LocalMachine")
    $store.Open("ReadWrite")
    $store.Add($cert)
    $store.Close()
    
    Write-Host "`nCertificate successfully installed to Trusted Publishers store." -ForegroundColor Green
    Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Green
    Write-Host "Subject: $($cert.Subject)" -ForegroundColor Green
    Write-Host "Expires: $($cert.NotAfter)" -ForegroundColor Green
    
    exit 0
}
catch {
    Write-Host "Error installing certificate: $_" -ForegroundColor Red
    exit 1
}
```

## Testing

1. **Local Testing**:
   - Build the MSI locally
   - Run the signing script manually
   - Verify the signature with:
     ```powershell
     Get-AuthenticodeSignature -FilePath "path\to\your.msi" | Format-List *
     ```

2. **GitHub Actions Testing**:
   - Push a test tag to trigger the workflow
   - Check the workflow logs for any signing errors
   - Download the signed MSI and verify the signature

## Release Notes and User Documentation

### Release Notes Example
Add this to your release notes for each version:

```markdown
## Windows Installation Notes

### First-Time Installation
1. Download both the MSI installer and the certificate file
2. Install the certificate (one-time only)
3. Run the installer

### Updating from Previous Versions
- No need to reinstall the certificate
- Simply run the new installer - your existing settings will be preserved

### Security Note
This version is signed with a self-signed certificate. You'll need to install our certificate once to verify future updates.
```

### Platform-Specific Instructions

#### Windows
```markdown
## Windows Installation

### Prerequisites
- Windows 10/11 (64-bit)
- Administrator privileges (required once for certificate installation)

### First-Time Setup
1. Download:
   - `heavymeta-installer-x.x.x.msi` (installer)
   - `heavymeta-code-sign.cer` (security certificate - one-time download)

2. Install the certificate (one-time only):
   - Right-click `heavymeta-code-sign.cer`
   - Select "Install Certificate"
   - Choose "Local Machine" (requires admin rights)
   - Select "Place all certificates in the following store"
   - Click "Browse..." and select "Trusted Publishers"
   - Complete the wizard

3. Run the installer:
   - Double-click `heavymeta-installer-x.x.x.msi`
   - Follow the installation prompts

### Updating
- Simply download and run the new MSI - no certificate reinstallation needed
- Your settings and preferences will be preserved

### Troubleshooting

**Security Warning**
If you see a warning:
1. Ensure the certificate is in "Trusted Publishers"
2. Right-click the MSI → Properties → Check "Unblock"
3. Try installing again

**Certificate Issues**
If certificate installation fails:
```powershell
# Run in Administrator PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Linux
```markdown
## Linux Installation

### Prerequisites
- glibc 2.31 or later
- Python 3.8+

### Installation
```bash
# For Debian/Ubuntu
sudo apt install ./heavymeta-x.x.x.deb

# For RHEL/CentOS
sudo yum install ./heavymeta-x.x.x.rpm
```

#### macOS
```markdown
## macOS Installation

### Prerequisites
- macOS 11.0 (Big Sur) or later

### Installation
1. Download `Heavymeta-x.x.x.dmg`
2. Open the DMG and drag Heavymeta to Applications
3. If blocked, right-click and select Open
```

## Security Considerations

1. **Private Key Protection**:
   - The private key (`heavymeta.key` and `heavymeta.pfx`) must be stored securely offline in encrypted storage.
   - The PFX file is only used during the build process and is never committed to version control.

2. **GitHub Secrets**:
   - The base64-encoded certificate and password are stored in GitHub Secrets.
   - Repository settings should restrict access to these secrets to only the necessary workflows.

3. **Certificate Renewal**:
   - The certificate is valid for 3 years. Set calendar reminders to renew it before expiration.
   - Update GitHub Secrets with the new certificate before the old one expires.

4. **Build Security**:
   - Only tagged releases trigger the signing process to prevent unauthorized builds.
   - The build process runs in an isolated GitHub Actions environment.
