import urllib.request
import urllib.error
import tempfile
import os
import subprocess
from pathlib import Path


def download_file(url, destination=None):
    """
    Download a file from URL to destination
    Returns the path to the downloaded file
    """
    try:
        if destination is None:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            destination = temp_file.name
            temp_file.close()
        
        # Download the file
        urllib.request.urlretrieve(url, destination)
        return destination
    except urllib.error.URLError as e:
        print(f"Error downloading {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading {url}: {e}")
        return None


def download_and_execute_script(url, platform_manager):
    """
    Download and execute a script based on platform
    """
    try:
        # Download the script
        script_path = download_file(url)
        if not script_path:
            return False
        
        # Make script executable on Unix systems
        if not platform_manager.is_windows:
            os.chmod(script_path, 0o755)
        
        # Execute the script
        if platform_manager.is_windows:
            # Execute PowerShell script on Windows
            result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path], 
                                  capture_output=True, text=True)
        else:
            # Execute shell script on Linux/macOS
            result = subprocess.run(['bash', script_path], capture_output=True, text=True)
        
        # Clean up temporary file
        try:
            os.unlink(script_path)
        except:
            pass
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error executing script {url}: {e}")
        return False


def download_and_extract_zip(url, extract_path):
    """
    Download and extract a ZIP file
    """
    try:
        # Download the ZIP file
        zip_path = download_file(url)
        if not zip_path:
            return False
        
        # Extract the ZIP file
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Clean up temporary file
        try:
            os.unlink(zip_path)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"Error extracting ZIP {url}: {e}")
        return False 