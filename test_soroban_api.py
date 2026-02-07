#!/usr/bin/env python3
"""
Test script for Soroban contract build and deployment API endpoints.
Starts a standalone API server and runs tests against it.
"""

import sys
import time
import json
import requests
import threading
import uvicorn
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

API_BASE = "http://127.0.0.1:7778"  # Use different port for testing


def start_api_server():
    """Start the API server in a background thread."""
    from api_server import create_api_app

    app = create_api_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=7778, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def wait_for_server(timeout=10):
    """Wait for the server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API_BASE}/api/v1/health", timeout=1)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def test_health():
    """Test health endpoint."""
    print("\n=== Test: Health Check ===")
    r = requests.get(f"{API_BASE}/api/v1/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    return r.status_code == 200


def test_generate():
    """Test contract generation endpoint."""
    print("\n=== Test: Generate Contract ===")

    payload = {
        "contract_name": "TestNFT",
        "symbol": "TEST",
        "max_supply": 1000,
        "nft_type": "HVYC",
        "write_to_disk": True,
        "val_props": {
            "health": {
                "default": 100,
                "min": 0,
                "max": 100,
                "amount": 10,
                "prop_action_type": "Bicremental"
            }
        }
    }

    r = requests.post(f"{API_BASE}/api/v1/soroban/generate", json=payload)
    print(f"Status: {r.status_code}")

    data = r.json()
    print(f"Success: {data.get('success')}")
    print(f"Contract Name: {data.get('contract_name')}")
    print(f"Output Path: {data.get('output_path')}")

    if data.get('output_path'):
        # Check if files were created
        output_path = Path(data['output_path'])
        if output_path.exists():
            print(f"Files created:")
            for f in output_path.rglob("*"):
                if f.is_file():
                    print(f"  - {f.relative_to(output_path)}")

    return data


def test_build(contract_path: str):
    """Test contract build endpoint."""
    print("\n=== Test: Build Contract ===")

    payload = {
        "contract_path": contract_path
    }

    r = requests.post(f"{API_BASE}/api/v1/soroban/build", json=payload)
    print(f"Status: {r.status_code}")

    data = r.json()
    print(f"Success: {data.get('success')}")
    print(f"Build ID: {data.get('build_id')}")
    print(f"WASM Path: {data.get('wasm_path')}")
    print(f"WASM Size: {data.get('wasm_size')} bytes")

    if not data.get('success'):
        print(f"Error: {data.get('error')}")
        if data.get('build_output'):
            print(f"Build Output:\n{data.get('build_output')[:500]}")

    return data


def test_generate_and_build():
    """Test combined generate and build endpoint."""
    print("\n=== Test: Generate and Build ===")

    payload = {
        "contract_name": "CombinedTest",
        "symbol": "CTEST",
        "max_supply": 500,
        "nft_type": "HVYC",
        "val_props": {
            "power": {
                "default": 50,
                "min": 0,
                "max": 200,
                "amount": 5,
                "prop_action_type": "Incremental"
            }
        }
    }

    r = requests.post(f"{API_BASE}/api/v1/soroban/generate-and-build", json=payload)
    print(f"Status: {r.status_code}")

    data = r.json()
    print(f"Success: {data.get('success')}")
    print(f"Contract Name: {data.get('contract_name')}")
    print(f"Output Path: {data.get('output_path')}")
    print(f"WASM Path: {data.get('wasm_path')}")
    print(f"WASM Size: {data.get('wasm_size')} bytes")

    if not data.get('success'):
        print(f"Error: {data.get('error')}")

    return data


def test_deployments():
    """Test deployments listing endpoint."""
    print("\n=== Test: List Deployments ===")

    r = requests.get(f"{API_BASE}/api/v1/soroban/deployments")
    print(f"Status: {r.status_code}")

    data = r.json()
    print(f"Success: {data.get('success')}")
    print(f"Total: {data.get('total')}")

    if data.get('deployments'):
        print("Recent deployments:")
        for d in data['deployments'][:3]:
            print(f"  - {d.get('contract_id', 'N/A')[:20]}... ({d.get('network')}) - {d.get('status')}")

    return data


def main():
    """Main test runner."""
    print("=" * 60)
    print("Soroban API Test Suite")
    print("=" * 60)

    # Start server in background
    print("\nStarting API server...")
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server():
        print("ERROR: Server failed to start!")
        return 1

    print("Server ready!")

    try:
        # Run tests
        test_health()

        # Test generate
        gen_result = test_generate()

        # Test build (if generate succeeded)
        if gen_result.get('success') and gen_result.get('output_path'):
            build_result = test_build(gen_result['output_path'])
        else:
            print("\nSkipping build test - generation failed")

        # Test combined generate and build
        test_generate_and_build()

        # Test deployments listing
        test_deployments()

        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
