@echo off
REM Windows Uninstall Script for Metavinci
REM This script cleans up the hvym CLI and related files when Metavinci is uninstalled

echo Metavinci Uninstaller for Windows
echo ==================================

REM Get the user's local app data directory
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Local AppData" 2^>nul') do set "LOCALAPPDATA=%%b"
if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"

set "METAVINCI_DIR=%LOCALAPPDATA%\Programs\Metavinci"
set "HVYM_DIR=%LOCALAPPDATA%\heavymeta-cli"
set "HVYM_BINARY=%HVYM_DIR%\hvym-windows.exe"

echo Looking for Metavinci installation...

REM Check if Metavinci directory exists
if not exist "%METAVINCI_DIR%" (
    echo No Metavinci installation found at: %METAVINCI_DIR%
    goto :end
)

echo Found Metavinci installation at: %METAVINCI_DIR%

REM Remove hvym CLI binary if it exists
if exist "%HVYM_BINARY%" (
    echo Removing hvym CLI binary...
    del /f /q "%HVYM_BINARY%"
    echo ✓ Removed hvym CLI binary
) else (
    echo hvym CLI binary not found
)

REM Remove hvym directory if it's empty
if exist "%HVYM_DIR%" (
    dir /a /b "%HVYM_DIR%" | findstr /r /c:"." >nul
    if errorlevel 1 (
        echo Removing empty hvym directory...
        rmdir "%HVYM_DIR%"
        echo ✓ Removed empty hvym directory
    ) else (
        echo hvym directory not empty, leaving it in place
    )
)

echo ✓ Metavinci uninstallation completed successfully
echo.
echo Note: This script only removes the hvym CLI and related files.
echo To completely uninstall Metavinci, also remove it from Programs and Features.

:end
pause
