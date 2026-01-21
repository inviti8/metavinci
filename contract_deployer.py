#!/usr/bin/env python3
"""
Soroban Contract Deployment System
Handles deployment of compiled Soroban contracts to Stellar networks using the Soroban CLI
"""

import subprocess
import uuid
import re
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from wallet_manager import WalletManager


class ContractDeployer:
    """Deploys compiled Soroban contracts to Stellar networks using soroban CLI"""

    # Network configurations
    NETWORK_CONFIG = {
        "testnet": {
            "rpc_url": "https://soroban-testnet.stellar.org",
            "network_passphrase": "Test SDF Network ; September 2015",
            "explorer_base": "https://stellar.expert/explorer/testnet"
        },
        "mainnet": {
            "rpc_url": "https://soroban.stellar.org",
            "network_passphrase": "Public Global Stellar Network ; September 2015",
            "explorer_base": "https://stellar.expert/explorer/public"
        },
        "futurenet": {
            "rpc_url": "https://rpc-futurenet.stellar.org",
            "network_passphrase": "Test SDF Future Network ; October 2022",
            "explorer_base": "https://stellar.expert/explorer/futurenet"
        },
        "local": {
            "rpc_url": "http://localhost:8000/soroban/rpc",
            "network_passphrase": "Standalone Network ; February 2017",
            "explorer_base": None
        }
    }

    def __init__(self, network: str = "testnet"):
        self.network = network
        self.wallet_manager = WalletManager()
        self.cli_cmd = "stellar"
        self.deployment_status = {}

        if network not in self.NETWORK_CONFIG:
            raise ValueError(f"Unknown network: {network}. Valid networks: {list(self.NETWORK_CONFIG.keys())}")

        self.config = self.NETWORK_CONFIG[network]

    def deploy_contract(self, wasm_path: str, wallet_address: str, wallet_password: str = None) -> Dict:
        """
        Deploy compiled contract to specified network using soroban CLI

        Args:
            wasm_path: Path to compiled WASM file
            wallet_address: Stellar wallet address for deployment
            wallet_password: Password for mainnet wallet (if required)

        Returns:
            Dict containing deployment results or error information
        """
        deployment_id = str(uuid.uuid4())

        try:
            # 1. Validate WASM file exists
            wasm_file = Path(wasm_path)
            if not wasm_file.exists():
                return {
                    "success": False,
                    "error": "WASM file not found",
                    "deployment_id": deployment_id
                }

            # 2. Load and Validate Wallet
            wallet = self.wallet_manager.get_wallet(wallet_address)
            if not wallet:
                return {
                    "success": False,
                    "error": "Wallet not found",
                    "deployment_id": deployment_id
                }

            # 3. Handle Wallet Authentication and get secret key
            if wallet.network == "mainnet":
                if not wallet_password:
                    return {
                        "success": False,
                        "error": "Password required for mainnet wallet",
                        "deployment_id": deployment_id
                    }
                try:
                    secret_key = self.wallet_manager.decrypt_secret(wallet.secret_key, wallet_password)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Invalid wallet password: {str(e)}",
                        "deployment_id": deployment_id
                    }
            else:
                # For testnet, the secret key is stored unencrypted
                secret_key = wallet.secret_key

            # 4. Check Soroban CLI availability
            cli_check = self._check_stellar_cli()
            if not cli_check["available"]:
                return {
                    "success": False,
                    "error": f"Stellar CLI not available: {cli_check['error']}",
                    "deployment_id": deployment_id
                }

            # 5. Build deployment command
            cmd = [
                self.cli_cmd, "contract", "deploy",
                "--wasm", str(wasm_file),
                "--source", secret_key,
                "--network", self.network
            ]

            # Add RPC URL if not using named network
            if self.network == "local":
                cmd.extend(["--rpc-url", self.config["rpc_url"]])
                cmd.extend(["--network-passphrase", self.config["network_passphrase"]])

            # 6. Execute deployment
            self.deployment_status[deployment_id] = "deploying"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for deployment
                encoding='utf-8',
                errors='replace'
            )

            # 7. Parse results
            if result.returncode == 0:
                # Extract contract ID from output
                # The soroban CLI outputs the contract ID on success
                contract_id = result.stdout.strip()

                # Validate it looks like a contract ID (starts with C and is 56 chars)
                if not contract_id or not self._is_valid_contract_id(contract_id):
                    # Try to extract from output
                    contract_id = self._extract_contract_id(result.stdout)

                if not contract_id:
                    return {
                        "success": False,
                        "error": "Deployment succeeded but could not parse contract ID",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "deployment_id": deployment_id
                    }

                # Generate Stellar Expert URL
                stellar_expert_url = None
                if self.config["explorer_base"]:
                    stellar_expert_url = f"{self.config['explorer_base']}/contract/{contract_id}"

                # Get WASM size
                wasm_size = wasm_file.stat().st_size

                # Create deployment record
                deployment_record = {
                    "deployment_id": deployment_id,
                    "contract_id": contract_id,
                    "network": self.network,
                    "wasm_path": str(wasm_path),
                    "wallet_address": wallet_address,
                    "deployment_wallet": wallet.label or wallet_address[:8] + "...",
                    "transaction_hash": "",  # CLI doesn't return this directly
                    "stellar_expert_url": stellar_expert_url or "",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                    "wasm_size": wasm_size,
                    "fees_paid": 0,  # CLI doesn't return this directly
                    "error": ""
                }

                self.deployment_status[deployment_id] = "success"

                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "contract_id": contract_id,
                    "stellar_expert_url": stellar_expert_url,
                    "deployment_record": deployment_record
                }

            else:
                # Deployment failed
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"

                error_record = {
                    "deployment_id": deployment_id,
                    "contract_id": "",
                    "network": self.network,
                    "wasm_path": str(wasm_path),
                    "wallet_address": wallet_address,
                    "deployment_wallet": wallet.label or wallet_address[:8] + "...",
                    "transaction_hash": "",
                    "stellar_expert_url": "",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "failed",
                    "wasm_size": wasm_file.stat().st_size,
                    "fees_paid": 0,
                    "error": error_msg
                }

                self.deployment_status[deployment_id] = "failed"

                return {
                    "success": False,
                    "deployment_id": deployment_id,
                    "error": error_msg,
                    "deployment_record": error_record
                }

        except subprocess.TimeoutExpired:
            error_record = {
                "deployment_id": deployment_id,
                "contract_id": "",
                "network": self.network,
                "wasm_path": str(wasm_path),
                "wallet_address": wallet_address,
                "deployment_wallet": wallet_address[:8] + "...",
                "transaction_hash": "",
                "stellar_expert_url": "",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "wasm_size": 0,
                "fees_paid": 0,
                "error": "Deployment timed out after 2 minutes"
            }

            self.deployment_status[deployment_id] = "timeout"

            return {
                "success": False,
                "deployment_id": deployment_id,
                "error": "Deployment timed out after 2 minutes",
                "deployment_record": error_record
            }

        except Exception as e:
            error_record = {
                "deployment_id": deployment_id,
                "contract_id": "",
                "network": self.network,
                "wasm_path": str(wasm_path),
                "wallet_address": wallet_address,
                "deployment_wallet": wallet_address[:8] + "...",
                "transaction_hash": "",
                "stellar_expert_url": "",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "wasm_size": 0,
                "fees_paid": 0,
                "error": str(e)
            }

            self.deployment_status[deployment_id] = "error"

            return {
                "success": False,
                "deployment_id": deployment_id,
                "error": f"Deployment exception: {str(e)}",
                "deployment_record": error_record
            }

    def _check_stellar_cli(self) -> Dict:
        """
        Check if Stellar CLI is available and get version

        Returns:
            Dict with availability status and version info
        """
        try:
            result = subprocess.run(
                [self.cli_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    "available": True,
                    "version": version
                }
            else:
                return {
                    "available": False,
                    "error": "Stellar CLI returned non-zero exit code"
                }

        except subprocess.TimeoutExpired:
            return {
                "available": False,
                "error": "Stellar CLI command timed out"
            }
        except FileNotFoundError:
            return {
                "available": False,
                "error": "Stellar CLI not found in PATH. Install with: cargo install stellar-cli"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking Stellar CLI: {str(e)}"
            }

    def _is_valid_contract_id(self, contract_id: str) -> bool:
        """Check if a string looks like a valid Soroban contract ID"""
        # Contract IDs start with 'C' and are 56 characters (strkey encoded)
        if not contract_id:
            return False
        return contract_id.startswith('C') and len(contract_id) == 56

    def _extract_contract_id(self, output: str) -> Optional[str]:
        """Extract contract ID from CLI output"""
        # Look for a string that matches contract ID format
        pattern = r'C[A-Z0-9]{55}'
        matches = re.findall(pattern, output)
        if matches:
            return matches[0]
        return None

    def get_deployment_status(self, deployment_id: str) -> Dict:
        """
        Check deployment status

        Args:
            deployment_id: Unique deployment identifier

        Returns:
            Dict with deployment status
        """
        return {
            "deployment_id": deployment_id,
            "status": self.deployment_status.get(deployment_id, "unknown")
        }

    def estimate_deployment_cost(self, wasm_path: str) -> Dict:
        """
        Estimate deployment fees and costs

        Args:
            wasm_path: Path to WASM file

        Returns:
            Dict with cost estimation
        """
        try:
            wasm_file = Path(wasm_path)
            if not wasm_file.exists():
                return {
                    "success": False,
                    "error": "WASM file not found"
                }

            wasm_size = wasm_file.stat().st_size

            # Rough estimation based on WASM size
            # Soroban charges based on resource usage, this is approximate
            # Base fee + size-based fee
            base_fee_xlm = 0.001  # Minimum transaction fee
            size_fee_xlm = (wasm_size / 1024) * 0.0001  # ~0.0001 XLM per KB

            # Account minimum balance requirement for contract deployment
            minimum_balance = 1.0  # XLM minimum

            estimated_total = base_fee_xlm + size_fee_xlm + minimum_balance

            return {
                "success": True,
                "wasm_size_bytes": wasm_size,
                "wasm_size_kb": round(wasm_size / 1024, 2),
                "estimated_fee_xlm": round(base_fee_xlm + size_fee_xlm, 7),
                "minimum_balance_xlm": minimum_balance,
                "total_required_xlm": round(estimated_total, 4),
                "note": "This is a rough estimate. Actual fees depend on network conditions and resource usage."
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cost estimation failed: {str(e)}"
            }

    def verify_contract(self, contract_id: str) -> Dict:
        """
        Verify a deployed contract exists on the network

        Args:
            contract_id: The contract ID to verify

        Returns:
            Dict with verification result
        """
        try:
            # Use soroban CLI to fetch contract info
            cmd = [
                self.cli_cmd, "contract", "info",
                "--id", contract_id,
                "--network", self.network
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "exists": True,
                    "contract_id": contract_id,
                    "info": result.stdout.strip()
                }
            else:
                return {
                    "success": True,
                    "exists": False,
                    "contract_id": contract_id,
                    "error": result.stderr.strip()
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Verification failed: {str(e)}"
            }


# Utility function for easy access
def deploy_contract(wasm_path: str, wallet_address: str, wallet_password: str = None, network: str = "testnet") -> Dict:
    """
    Convenience function to deploy a contract

    Args:
        wasm_path: Path to compiled WASM file
        wallet_address: Stellar wallet address
        wallet_password: Password for mainnet wallet (if required)
        network: Target network (testnet/mainnet/futurenet/local)

    Returns:
        Deployment result dictionary
    """
    deployer = ContractDeployer(network=network)
    return deployer.deploy_contract(wasm_path, wallet_address, wallet_password)
