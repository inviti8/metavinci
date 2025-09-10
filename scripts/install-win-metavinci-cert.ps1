<#
.SYNOPSIS
    Installs the HEAVYMETA code signing certificate to the Trusted Publishers store.

.DESCRIPTION
    This script installs the HEAVYMETA code signing certificate to the Local Machine's
    Trusted Publishers store, allowing the signed application to run without warnings.
    Administrative privileges are required to install the certificate.
    
    The script will automatically download the latest certificate from the release assets
    if no local path is provided.

.PARAMETER CertificatePath
    Optional. The path to the .cer certificate file to install. If not provided,
    the script will download the certificate from the latest release.

.EXAMPLE
    # Install certificate from local file
    .\install-win-metavinci-cert.ps1 -CertificatePath ".\heavymeta-code-sign.cer"
    
    # Download and install certificate from latest release
    .\install-win-metavinci-cert.ps1
#>

# Constants
$CERT_FILENAME = "heavymeta-code-sign.cer"
$RELEASE_URL = "https://github.com/inviti8/metavinci/releases/latest/download/$CERT_FILENAME"

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateScript({
        if ($_ -and -not (Test-Path $_)) {
            throw "Certificate file not found at $_"
        }
        if ($_ -and $_ -notmatch '\.(cer|p7b|p7c|p7s|p12|pfx|pem|crl|der)$') {
            throw "The specified certificate file must be a valid certificate file"
        }
        return $true
    })]
    [string]$CertificatePath,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest"
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

function Get-CertificateFromRelease {
    try {
        $tempDir = [System.IO.Path]::GetTempPath()
        $certPath = Join-Path -Path $tempDir -ChildPath $CERT_FILENAME
        
        Write-Host "Downloading certificate from: $RELEASE_URL" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $RELEASE_URL -OutFile $certPath -ErrorAction Stop
        
        if (Test-Path $certPath) {
            Write-Host "Certificate downloaded successfully to: $certPath" -ForegroundColor Green
            return $certPath
        }
        
        return $null
    }
    catch {
        Write-Host "Error downloading certificate: $_" -ForegroundColor Red
        return $null
    }
}

try {
    # If no certificate path provided, download it from the latest release
    if ([string]::IsNullOrEmpty($CertificatePath)) {
        Write-Host "No certificate path provided. Attempting to download from latest release..." -ForegroundColor Cyan
        
        $CertificatePath = Get-CertificateFromRelease
        if ($null -eq $CertificatePath) {
            throw "Failed to download certificate from release. Please provide a local certificate path using -CertificatePath parameter."
        }
    }
    
    if (-not (Test-Path $CertificatePath)) {
        throw "Certificate file not found at: $CertificatePath"
    }
    
    Write-Host "Installing certificate from: $CertificatePath" -ForegroundColor Cyan
    
    # Import the certificate to the Local Machine's Trusted Publishers store
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertificatePath)
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store(
        [System.Security.Cryptography.X509Certificates.StoreName]::TrustedPublisher,
        [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
    )
    
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    $store.Add($cert)
    $store.Close()
    
    Write-Host "Successfully installed certificate to Trusted Publishers store." -ForegroundColor Green
    Write-Host "Issuer: $($cert.Issuer)" -ForegroundColor Cyan
    Write-Host "Subject: $($cert.Subject)" -ForegroundColor Cyan
    Write-Host "Valid From: $($cert.NotBefore)" -ForegroundColor Cyan
    Write-Host "Valid To: $($cert.NotAfter)" -ForegroundColor Cyan
    Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
    
    # Verify the certificate was installed
    $installedCert = Get-ChildItem -Path "Cert:\LocalMachine\TrustedPublisher" | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
    
    if ($installedCert) {
        Write-Host "Verification: Certificate found in Trusted Publishers store." -ForegroundColor Green
    } else {
        Write-Host "Warning: Could not verify certificate installation. Please check manually." -ForegroundColor Yellow
    }
    
    # Clean up downloaded certificate if it was downloaded
    if ($CertificatePath -like "$([System.IO.Path]::GetTempPath())*") {
        Remove-Item -Path $CertificatePath -Force -ErrorAction SilentlyContinue
    }
    
    exit 0
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
