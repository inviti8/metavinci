#!/usr/bin/env python3
"""
Test Script for Soroban Build & Deploy Pipeline
Tests the complete flow: generate -> build -> deploy
"""

import requests
import json
import time
import sys
from pathlib import Path


class SorobanPipelineTest:
    """Test class for Soroban build and deploy pipeline"""
    
    def __init__(self, base_url="http://127.0.0.1:7777"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_contract_id = None
        self.build_result = None
        self.deployment_result = None
    
    def test_api_connection(self):
        """Test if API server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ API server is running")
                return True
            else:
                print(f"❌ API server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API server: {e}")
            return False
    
    def generate_test_contract(self):
        """Generate a test contract using the API"""
        print("\n🔨 Generating test contract...")
        
        contract_config = {
            "name": "TestIncrementContract",
            "description": "A simple increment contract for testing",
            "functions": [
                {
                    "name": "increment",
                    "description": "Increment the counter",
                    "parameters": [],
                    "returns": "u32"
                },
                {
                    "name": "get_value",
                    "description": "Get the current counter value",
                    "parameters": [],
                    "returns": "u32"
                }
            ],
            "storage": [
                {
                    "name": "counter",
                    "type": "u32",
                    "description": "Counter value"
                }
            ],
            "network": "testnet"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/soroban/generate",
                json=contract_config,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_contract_id = result.get("contract_id")
                print(f"✅ Contract generated successfully")
                print(f"   Contract ID: {self.test_contract_id}")
                print(f"   Files generated: {len(result.get('files', []))}")
                return True
            else:
                print(f"❌ Contract generation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Contract generation request failed: {e}")
            return False
    
    def build_contract(self):
        """Build the generated contract using the API"""
        print("\n🔨 Building contract...")
        
        if not self.test_contract_id:
            print("❌ No contract ID available for building")
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/soroban/build",
                json={"contract_id": self.test_contract_id},
                timeout=60  # Build can take time
            )
            
            if response.status_code == 200:
                self.build_result = response.json()
                print(f"✅ Contract built successfully")
                print(f"   Build ID: {self.build_result.get('build_id')}")
                print(f"   WASM path: {self.build_result.get('wasm_path')}")
                print(f"   Build time: {self.build_result.get('metadata', {}).get('build_time', 'Unknown')}")
                return True
            else:
                print(f"❌ Contract build failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Contract build request failed: {e}")
            return False
    
    def deploy_contract(self):
        """Deploy the built contract using the API"""
        print("\n🚀 Deploying contract...")
        
        if not self.build_result or not self.build_result.get("wasm_path"):
            print("❌ No build result available for deployment")
            return False
        
        # First, get available testnet wallets
        try:
            wallets_response = requests.get(f"{self.api_base}/wallets/testnet")
            if wallets_response.status_code != 200:
                print("❌ Failed to get testnet wallets")
                return False
            
            wallets = wallets_response.json()
            if not wallets:
                print("❌ No testnet wallets available. Please create a testnet wallet first.")
                return False
            
            # Use the first available testnet wallet
            test_wallet = wallets[0]
            wallet_address = test_wallet["address"]
            print(f"   Using wallet: {test_wallet.get('label', wallet_address[:8] + '...')}")
            print(f"   Address: {wallet_address}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get wallets: {e}")
            return False
        
        # Deploy the contract
        deploy_payload = {
            "wasm_path": self.build_result["wasm_path"],
            "wallet_address": wallet_address
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/soroban/deploy",
                json=deploy_payload,
                timeout=120  # Deployment can take time
            )
            
            if response.status_code == 200:
                self.deployment_result = response.json()
                print(f"✅ Contract deployed successfully!")
                print(f"   Contract ID: {self.deployment_result.get('contract_id')}")
                print(f"   Network: {self.deployment_result.get('network')}")
                print(f"   Transaction Hash: {self.deployment_result.get('transaction_hash')}")
                print(f"   Stellar Expert URL: {self.deployment_result.get('stellar_expert_url')}")
                return True
            else:
                print(f"❌ Contract deployment failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Contract deployment request failed: {e}")
            return False
    
    def test_full_pipeline(self):
        """Test the complete Soroban pipeline"""
        print("🧪 Starting Soroban Build & Deploy Pipeline Test")
        print("=" * 60)
        
        # Step 1: Test API connection
        if not self.test_api_connection():
            print("\n❌ Pipeline test failed: API server not available")
            return False
        
        # Step 2: Generate contract
        if not self.generate_test_contract():
            print("\n❌ Pipeline test failed: Contract generation")
            return False
        
        # Step 3: Build contract
        if not self.build_contract():
            print("\n❌ Pipeline test failed: Contract building")
            return False
        
        # Step 4: Deploy contract
        if not self.deploy_contract():
            print("\n❌ Pipeline test failed: Contract deployment")
            return False
        
        # Success!
        print("\n" + "=" * 60)
        print("🎉 Pipeline test completed successfully!")
        print("\n📊 Test Summary:")
        print(f"   Contract Generated: {self.test_contract_id}")
        print(f"   Build Result: {self.build_result.get('build_id') if self.build_result else 'None'}")
        print(f"   Deployed Contract: {self.deployment_result.get('contract_id') if self.deployment_result else 'None'}")
        print(f"   Network: {self.deployment_result.get('network') if self.deployment_result else 'None'}")
        
        if self.deployment_result and self.deployment_result.get('stellar_expert_url'):
            print(f"\n🔗 View deployed contract: {self.deployment_result['stellar_expert_url']}")
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data (optional)"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Note: This would require cleanup endpoints which may not be implemented yet
            print("   Cleanup endpoints not yet implemented")
            print("   Test data will remain for inspection")
        except Exception as e:
            print(f"   Cleanup failed: {e}")


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Soroban build and deploy pipeline")
    parser.add_argument(
        "--url", 
        default="http://127.0.0.1:7777",
        help="Base URL for Metavinci API (default: http://127.0.0.1:7777)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test data after successful test"
    )
    
    args = parser.parse_args()
    
    # Create and run test
    test = SorobanPipelineTest(base_url=args.url)
    
    try:
        success = test.test_full_pipeline()
        
        if args.cleanup and success:
            test.cleanup_test_data()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
