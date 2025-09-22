# Save this as install-cert.ps1
# Run with: powershell.exe -ExecutionPolicy Bypass -File install-cert.ps1

# Constants
$CERT_FILENAME = "heavymeta-code-sign.cer"
$RELEASE_URL = "https://github.com/inviti8/metavinci/releases/latest/download/$CERT_FILENAME"

# Parameters
$CertificatePath = $args[0]
$Version = if ($args[1]) { $args[1] } else { "latest" }

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

function Get-CertificateFromRelease {
    try {
        $tempDir = [System.IO.Path]::GetTempPath()
        $certPath = Join-Path -Path $tempDir -ChildPath $script:CERT_FILENAME
        
        Write-Host "Downloading certificate from: $script:RELEASE_URL" -ForegroundColor Cyan
        (New-Object System.Net.WebClient).DownloadFile($script:RELEASE_URL, $certPath)
        
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
            throw "Failed to download certificate. Please provide a local certificate path."
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
    Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
    exit 1}