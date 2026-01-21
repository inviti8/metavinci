#!/usr/bin/env python3
"""
Soroban Contract Build System
Handles compilation of Soroban smart contracts from source files
"""

import subprocess
import tempfile
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable


class ContractBuilder:
    """Builds Soroban contracts from source files using the Stellar CLI"""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="soroban_build_"))
        self.cli_cmd = "stellar"
        self.build_status = {"status": "idle", "progress": 0}
    
    def build_contract(self, contract_path: Path, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Build Soroban contract from source files

        Args:
            contract_path: Path to contract directory
            progress_callback: Optional callback for progress updates (message, percentage)

        Returns:
            Dict containing build results or error information
        """
        build_id = str(uuid.uuid4())
        contract_path = Path(contract_path)

        try:
            # 1. Input Validation
            if not contract_path.exists():
                return {
                    "success": False,
                    "error": "Contract path not found",
                    "build_id": build_id
                }

            # 2. Validate Contract Structure
            structure_check = self.validate_contract_structure(contract_path)
            if not structure_check["valid"]:
                return {
                    "success": False,
                    "error": structure_check["error"],
                    "build_id": build_id
                }

            # 3. Progress Callback Setup
            if progress_callback:
                progress_callback("Building contract...", 10)

            # 4. Check Soroban CLI
            soroban_check = self._check_stellar_cli()
            if not soroban_check["available"]:
                return {
                    "success": False,
                    "error": f"Stellar CLI not available: {soroban_check['error']}",
                    "build_id": build_id
                }

            # 5. Execute Soroban Build
            # soroban contract build must be run from within the contract directory
            # It outputs to target/wasm32-unknown-unknown/release/{contract_name}.wasm
            cmd = [self.cli_cmd, "contract", "build"]

            if progress_callback:
                progress_callback("Compiling WASM...", 30)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(contract_path),
                timeout=300,  # 5 minute timeout for compilation
                encoding='utf-8',
                errors='replace'  # Handle encoding errors gracefully
            )

            if progress_callback:
                progress_callback("Processing build output...", 80)

            # 6. Validate Build Results
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Build failed",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "build_id": build_id
                }

            # 7. Find Generated WASM Files
            # The WASM is output to target/wasm32-unknown-unknown/release/ within contract_path
            wasm_output_dir = contract_path / "target" / "wasm32-unknown-unknown" / "release"
            wasm_files = list(wasm_output_dir.glob("*.wasm")) if wasm_output_dir.exists() else []

            # Filter out deps and build script artifacts, keep only the main contract
            wasm_files = [f for f in wasm_files if not f.name.startswith("deps")]

            if not wasm_files:
                # Try broader search as fallback
                wasm_files = list(contract_path.rglob("*.wasm"))
                wasm_files = [f for f in wasm_files if "release" in str(f) and not f.name.startswith("deps")]

            if not wasm_files:
                return {
                    "success": False,
                    "error": "No WASM file generated. Check build output for errors.",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "build_id": build_id
                }

            # Prefer the contract-named wasm file
            wasm_path = wasm_files[0]

            # 8. Copy WASM to temp directory for deployment
            build_dir = self.temp_dir / build_id
            build_dir.mkdir(exist_ok=True)

            dest_wasm_path = build_dir / wasm_path.name
            shutil.copy2(wasm_path, dest_wasm_path)

            # 9. Generate Build Metadata
            build_metadata = {
                "build_id": build_id,
                "contract_path": str(contract_path),
                "wasm_path": str(dest_wasm_path),
                "original_wasm_path": str(wasm_path),
                "wasm_size": dest_wasm_path.stat().st_size,
                "build_time": datetime.utcnow().isoformat(),
                "soroban_version": soroban_check["version"],
                "build_output": result.stdout
            }

            if progress_callback:
                progress_callback("Build complete!", 100)

            return {
                "success": True,
                "build_id": build_id,
                "wasm_path": str(dest_wasm_path),
                "metadata": build_metadata
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timed out after 5 minutes",
                "build_id": build_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Build exception: {str(e)}",
                "build_id": build_id
            }
    
    def validate_contract_structure(self, contract_path: Path) -> Dict:
        """
        Validate required Soroban contract files
        
        Args:
            contract_path: Path to contract directory
            
        Returns:
            Dict with validation result
        """
        required_files = ["Cargo.toml", "src/lib.rs"]
        missing_files = []
        
        for file in required_files:
            if not (contract_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            return {
                "valid": False,
                "error": f"Missing required files: {', '.join(missing_files)}"
            }
        
        # Check Cargo.toml for Soroban dependencies
        cargo_toml = contract_path / "Cargo.toml"
        try:
            with open(cargo_toml, 'r') as f:
                content = f.read()
                if "soroban-sdk" not in content:
                    return {
                        "valid": False,
                        "error": "Cargo.toml missing soroban-sdk dependency"
                    }
        except Exception as e:
            return {"valid": False, "error": f"Failed to read Cargo.toml: {e}"}
        
        return {"valid": True}
    
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
    
    def get_build_output(self, build_id: str) -> Dict:
        """
        Retrieve build results for a specific build ID
        
        Args:
            build_id: Unique build identifier
            
        Returns:
            Dict with build results or error
        """
        build_dir = self.temp_dir / build_id
        
        if not build_dir.exists():
            return {"success": False, "error": "Build ID not found"}
        
        # Find WASM file
        wasm_files = list(build_dir.rglob("*.wasm"))
        if not wasm_files:
            return {"success": False, "error": "No WASM file found"}
        
        return {
            "success": True,
            "wasm_path": str(wasm_files[0]),
            "build_dir": str(build_dir)
        }
    
    def cleanup_build_artifacts(self, build_id: str) -> bool:
        """
        Clean up temporary build files
        
        Args:
            build_id: Unique build identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            build_dir = self.temp_dir / build_id
            if build_dir.exists():
                shutil.rmtree(build_dir)
            return True
        except Exception:
            return False
    
    def cleanup_all_artifacts(self) -> bool:
        """
        Clean up all temporary build artifacts
        
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            return True
        except Exception:
            return False


# Utility function for easy access
def build_contract(contract_path: Path, progress_callback: Optional[Callable] = None) -> Dict:
    """
    Convenience function to build a contract
    
    Args:
        contract_path: Path to contract directory
        progress_callback: Optional progress callback
        
    Returns:
        Build result dictionary
    """
    builder = ContractBuilder()
    return builder.build_contract(contract_path, progress_callback)
