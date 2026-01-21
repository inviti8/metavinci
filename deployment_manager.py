#!/usr/bin/env python3
"""
Deployment Record Management System
Handles storage and retrieval of Soroban contract deployment records
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from tinydb import TinyDB, Query


def _get_data_dir() -> Path:
    """Get the platform-specific data directory for deployment storage."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_dir = base / "heavymeta" / "deployments"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class DeploymentRecord:
    """Data structure for deployment records"""
    
    def __init__(self):
        self.deployment_id: str = ""
        self.contract_id: str = ""
        self.network: str = ""
        self.wasm_path: str = ""
        self.wallet_address: str = ""
        self.deployment_wallet: str = ""
        self.transaction_hash: str = ""
        self.stellar_expert_url: str = ""
        self.timestamp: str = ""
        self.status: str = ""  # success, failed, pending, error
        self.wasm_size: int = 0
        self.fees_paid: int = 0
        self.error: str = ""
    
    def from_dict(self, data: Dict):
        """Populate from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "deployment_id": self.deployment_id,
            "contract_id": self.contract_id,
            "network": self.network,
            "wasm_path": self.wasm_path,
            "wallet_address": self.wallet_address,
            "deployment_wallet": self.deployment_wallet,
            "transaction_hash": self.transaction_hash,
            "stellar_expert_url": self.stellar_expert_url,
            "timestamp": self.timestamp,
            "status": self.status,
            "wasm_size": self.wasm_size,
            "fees_paid": self.fees_paid,
            "error": self.error
        }


class DeploymentManager:
    """Manages deployment records storage and retrieval"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the deployment manager.

        Args:
            db_path: Optional custom path for deployment database.
                     If not provided, uses platform-specific data directory.
        """
        if db_path is None:
            self.db_path = _get_data_dir() / "deployments.json"
        else:
            self.db_path = Path(db_path)

        self.db = TinyDB(str(self.db_path))
        self.deployments = self.db.table('deployments')
    
    def store_deployment(self, record: Dict) -> bool:
        """
        Store deployment record
        
        Args:
            record: Deployment record dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure required fields
            required_fields = ['deployment_id', 'timestamp', 'status']
            for field in required_fields:
                if field not in record:
                    record[field] = "" if field == 'deployment_id' else datetime.utcnow().isoformat() if field == 'timestamp' else 'unknown'
            
            self.deployments.insert(record)
            return True
        except Exception as e:
            print(f"Failed to store deployment: {e}")
            return False
    
    def get_deployments(self, network: str = None, wallet_address: str = None, status: str = None) -> List[Dict]:
        """
        Get deployments with optional filtering
        
        Args:
            network: Filter by network (testnet/mainnet/futurenet/local)
            wallet_address: Filter by wallet address
            status: Filter by status (success/failed/pending/error)
            
        Returns:
            List of deployment records
        """
        query = Query()
        
        # Build query based on filters
        conditions = []
        
        if network and network != "all":
            conditions.append(query.network == network)
        
        if wallet_address:
            conditions.append(query.wallet_address == wallet_address)
        
        if status and status != "all":
            conditions.append(query.status == status)
        
        # Execute query
        if conditions:
            # Combine all conditions with AND
            combined_query = conditions[0]
            for condition in conditions[1:]:
                combined_query = combined_query & condition
            deployments = self.deployments.search(combined_query)
        else:
            deployments = self.deployments.all()
        
        # Sort by timestamp (newest first)
        deployments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return deployments
    
    def get_deployment_by_id(self, deployment_id: str) -> Optional[Dict]:
        """
        Get specific deployment record by ID
        
        Args:
            deployment_id: Unique deployment identifier
            
        Returns:
            Deployment record or None if not found
        """
        query = Query()
        result = self.deployments.search(query.deployment_id == deployment_id)
        return result[0] if result else None
    
    def get_deployments_by_contract_id(self, contract_id: str) -> List[Dict]:
        """
        Get all deployments for a specific contract ID
        
        Args:
            contract_id: Contract address
            
        Returns:
            List of deployment records
        """
        query = Query()
        deployments = self.deployments.search(query.contract_id == contract_id)
        
        # Sort by timestamp (newest first)
        deployments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return deployments
    
    def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete deployment record

        Args:
            deployment_id: Unique deployment identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            query = Query()
            removed = self.deployments.remove(query.deployment_id == deployment_id)
            # remove() returns list of removed doc IDs, convert to bool
            return len(removed) > 0
        except Exception:
            return False
    
    def update_deployment_status(self, deployment_id: str, status: str, error: str = None) -> bool:
        """
        Update deployment status
        
        Args:
            deployment_id: Unique deployment identifier
            status: New status (success/failed/pending/error)
            error: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = Query()
            updates = {"status": status}
            if error:
                updates["error"] = error
            
            return self.deployments.update(updates, query.deployment_id == deployment_id)
        except Exception:
            return False
    
    def get_deployment_stats(self, network: str = None) -> Dict:
        """
        Get deployment statistics
        
        Args:
            network: Optional network filter
            
        Returns:
            Dictionary with deployment statistics
        """
        deployments = self.get_deployments(network=network)
        
        stats = {
            "total": len(deployments),
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "error": 0,
            "by_network": {},
            "by_wallet": {}
        }
        
        for deployment in deployments:
            # Count by status
            status = deployment.get('status', 'unknown')
            if status in stats:
                stats[status] += 1
            
            # Count by network
            network_name = deployment.get('network', 'unknown')
            if network_name not in stats["by_network"]:
                stats["by_network"][network_name] = 0
            stats["by_network"][network_name] += 1
            
            # Count by wallet
            wallet = deployment.get('deployment_wallet', 'unknown')
            if wallet not in stats["by_wallet"]:
                stats["by_wallet"][wallet] = 0
            stats["by_wallet"][wallet] += 1
        
        return stats
    
    def export_deployments(self, network: str = None, format: str = "json") -> str:
        """
        Export deployment records
        
        Args:
            network: Optional network filter
            format: Export format (json/csv)
            
        Returns:
            Exported data as string
        """
        deployments = self.get_deployments(network=network)
        
        if format.lower() == "csv":
            import csv
            import io
            
            if not deployments:
                return "No deployments found"
            
            output = io.StringIO()
            fieldnames = deployments[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deployments)
            return output.getvalue()
        
        else:  # JSON format
            import json
            return json.dumps(deployments, indent=2)
    
    def cleanup_old_deployments(self, days: int = 30) -> int:
        """
        Clean up old deployment records
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of records deleted
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            query = Query()
            old_deployments = self.deployments.search(query.timestamp < cutoff_str)
            
            # Delete old deployments
            deleted_count = 0
            for deployment in old_deployments:
                if self.delete_deployment(deployment['deployment_id']):
                    deleted_count += 1
            
            return deleted_count
        except Exception:
            return 0
    
    def search_deployments(self, search_term: str, network: str = None) -> List[Dict]:
        """
        Search deployments by contract ID, wallet address, or wallet name
        
        Args:
            search_term: Search term
            network: Optional network filter
            
        Returns:
            List of matching deployment records
        """
        deployments = self.get_deployments(network=network)
        
        search_term = search_term.lower()
        matches = []
        
        for deployment in deployments:
            # Search in contract ID
            if search_term in deployment.get('contract_id', '').lower():
                matches.append(deployment)
                continue
            
            # Search in wallet address
            if search_term in deployment.get('wallet_address', '').lower():
                matches.append(deployment)
                continue
            
            # Search in wallet name
            if search_term in deployment.get('deployment_wallet', '').lower():
                matches.append(deployment)
                continue
            
            # Search in transaction hash
            if search_term in deployment.get('transaction_hash', '').lower():
                matches.append(deployment)
        
        return matches


# Utility functions for easy access
def store_deployment(record: Dict) -> bool:
    """Store a deployment record"""
    manager = DeploymentManager()
    return manager.store_deployment(record)

def get_deployments(network: str = None, wallet_address: str = None) -> List[Dict]:
    """Get deployments with optional filtering"""
    manager = DeploymentManager()
    return manager.get_deployments(network=network, wallet_address=wallet_address)

def get_deployment_by_id(deployment_id: str) -> Optional[Dict]:
    """Get deployment by ID"""
    manager = DeploymentManager()
    return manager.get_deployment_by_id(deployment_id)
