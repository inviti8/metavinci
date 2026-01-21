#!/usr/bin/env python3
"""
Quick Test for Soroban Build & Deploy Pipeline
Simple test to verify API endpoints work correctly
"""

import requests
import json
import time


def test_api_health(base_url="http://127.0.0.1:7777"):
    """Test if API server is running"""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_contract_generation(base_url="http://127.0.0.1:7777"):
    """Test contract generation endpoint"""
    print("🔨 Testing contract generation...")
    
    contract_config = {
        "contract_name": "TestCounter",
        "symbol": "TEST",
        "max_supply": 1000,
        "nft_type": "HVYC",
        "val_props": {
            "counter": {
                "prop_name": "counter",
                "prop_type": "Int",
                "prop_action_type": "Incremental",
                "initial_value": 0,
                "min_value": 0,
                "max_value": 1000000
            }
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/soroban/generate",
            json=contract_config,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Contract generated: {result.get('contract_name', 'Unknown')}")
            return result.get('contract_name')
        else:
            print(f"❌ Generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None


def test_contract_build(base_url="http://127.0.0.1:7777", contract_id=None):
    """Test contract build endpoint"""
    if not contract_id:
        print("❌ No contract ID to build")
        return None
    
    print("🔨 Testing contract build...")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/soroban/build",
            json={"contract_id": contract_id},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Contract built: {result.get('build_id', 'Unknown')}")
            print(f"   WASM: {result.get('wasm_path', 'Unknown')}")
            return result
        else:
            print(f"❌ Build failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Build error: {e}")
        return None


def test_wallets(base_url="http://127.0.0.1:7777"):
    """Test wallet endpoints"""
    print("👛 Testing wallet access...")
    
    try:
        response = requests.get(f"{base_url}/api/v1/wallets/testnet", timeout=10)
        
        if response.status_code == 200:
            wallets = response.json()
            if wallets:
                wallet = wallets[0]
                print(f"✅ Found testnet wallet: {wallet.get('label', wallet['address'][:8] + '...')}")
                return wallet['address']
            else:
                print("❌ No testnet wallets found")
                return None
        else:
            print(f"❌ Wallet access failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Wallet error: {e}")
        return None


def test_contract_deploy(base_url="http://127.0.0.1:7777", build_result=None, wallet_address=None):
    """Test contract deployment endpoint"""
    if not build_result or not wallet_address:
        print("❌ Missing build result or wallet for deployment")
        return None
    
    print("🚀 Testing contract deployment...")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/soroban/deploy",
            json={
                "wasm_path": build_result["wasm_path"],
                "wallet_address": wallet_address
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Contract deployed: {result.get('contract_id', 'Unknown')}")
            print(f"   Network: {result.get('network', 'Unknown')}")
            print(f"   Explorer: {result.get('stellar_expert_url', 'Unknown')}")
            return result
        else:
            print(f"❌ Deployment failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return None


def main():
    """Run available tests"""
    base_url = "http://127.0.0.1:7777"
    
    print("🧪 Soroban Available Features Test")
    print("=" * 50)
    
    # Test 1: API Health
    print("1. Testing API connection...")
    if not test_api_health(base_url):
        print("❌ API server not running at", base_url)
        print("   Please start Metavinci first")
        return False
    
    print("✅ API server is running")
    
    # Test 2: Contract Generation
    print("\n2. Testing contract generation...")
    contract_name = test_contract_generation(base_url)
    if not contract_name:
        print("❌ Contract generation failed")
        return False
    
    # Note: Build and Deploy endpoints not yet implemented
    print("\n3. Build endpoint - Not yet implemented")
    print("4. Deploy endpoint - Not yet implemented")
    
    print("\n" + "=" * 50)
    print("🎉 Available tests passed!")
    print("\n📊 Results:")
    print(f"   Generated Contract: {contract_name}")
    print("\n📝 Note: Build and deploy endpoints need to be implemented")
    print("   See HEAVYMETADATA_SERVER.md section 4.3 for implementation status")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Pipeline test completed successfully!")
        else:
            print("\n❌ Pipeline test failed!")
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
