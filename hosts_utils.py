"""
Utility functions for managing hosts file entries.
"""
import logging
import sys
from typing import Optional

from python_hosts import Hosts, HostsEntry

def update_hosts_entry(hostname: str, ip: str = '127.0.0.1') -> bool:
    """
    Add or update a hosts file entry.
    
    Args:
        hostname: The hostname to add/update (e.g., 'local.pintheon.com')
        ip: The IP address to map the hostname to (default: '127.0.0.1')
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    try:
        hosts = Hosts()
        
        # Check if the entry already exists
        existing_entry = hosts.find_all_matching(name=hostname)
        
        if existing_entry:
            # Update existing entry
            for entry in existing_entry:
                entry.address = ip
        else:
            # Add new entry
            new_entry = HostsEntry(
                entry_type='ipv4',
                address=ip,
                names=[hostname]
            )
            hosts.add([new_entry])
        
        # Save changes
        hosts.write()
        logging.info(f"Successfully updated hosts file with {ip} {hostname}")
        return True
        
    except PermissionError:
        logging.error("Insufficient permissions to modify hosts file. Please run with admin/root privileges.")
        return False
    except Exception as e:
        logging.error(f"Failed to update hosts file: {str(e)}")
        return False

def is_admin() -> bool:
    """
    Check if the current process has admin/root privileges.
    
    Returns:
        bool: True if running with admin/root privileges, False otherwise
    """
    try:
        if sys.platform == 'win32':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            import os
            return os.geteuid() == 0
    except Exception:
        return False

def ensure_hosts_entry(hostname: str, ip: str = '127.0.0.1') -> bool:
    """
    Ensure a hosts file entry exists, prompting for elevation if needed.
    
    Args:
        hostname: The hostname to ensure exists in hosts file
        ip: The IP address to map the hostname to (default: '127.0.0.1')
        
    Returns:
        bool: True if the entry exists or was successfully added, False otherwise
    """
    try:
        hosts = Hosts()
        existing = hosts.find_all_matching(name=hostname)
        
        if existing and any(entry.address == ip for entry in existing):
            logging.debug(f"Hosts entry {ip} {hostname} already exists")
            return True
            
        if not is_admin():
            logging.warning("Admin/root privileges required to modify hosts file")
            return False
            
        return update_hosts_entry(hostname, ip)
        
    except Exception as e:
        logging.error(f"Error checking/updating hosts file: {str(e)}")
        return False
