<#
.SYNOPSIS
    Installs the HEAVYMETA code signing certificate to the Trusted Publishers store.

.DESCRIPTION
    This script installs the HEAVYMETA code signing certificate to the Local Machine's
    Trusted Publishers store, allowing the signed application to run without warnings.
    Administrative privileges are required to install the certificate.

.PARAMETER CertificatePath
    The path to the .cer certificate file to install.

.EXAMPLE
    .\install-code-signing-cert.ps1 -CertificatePath ".\heavymeta-code-sign.cer"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateScript({
        if (-Not ($_ | Test-Path)) {
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
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

try {
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
    
    exit 0
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
