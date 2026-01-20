#!/usr/bin/env python3
"""
Test script for wallet API endpoints.
Run this script to verify the wallet API is working correctly.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_wallet_api():
    """Test all wallet API endpoints."""
    
    print("Testing Wallet API Endpoints")
    print("=" * 50)
    
    # Test health check first
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Make sure the Metavinci API server is running on port 8000")
        return
    
    # Test wallet creation
    print("\n2. Creating testnet wallet...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/wallet/testnet/create",
            json={"label": "Test Wallet API"}
        )
        if response.status_code == 200:
            wallet_data = response.json()
            wallet_address = wallet_data["address"]
            print(f"✅ Wallet created: {wallet_address}")
            print(f"   Label: {wallet_data['label']}")
            print(f"   Funded: {wallet_data['funded']}")
        else:
            print(f"❌ Wallet creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Wallet creation error: {e}")
        return
    
    # Wait a moment for funding
    time.sleep(2)
    
    # Test wallet recovery
    print("\n3. Testing wallet recovery...")
    try:
        # First, we need to get a secret key to test recovery
        # We'll create a temporary wallet just to get its secret key
        import stellar_keypair
        kp = stellar_keypair.Keypair.random()
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/wallet/recover",
            json={
                "secret_key": kp.secret,
                "network": "testnet",
                "label": "Recovered Test Wallet"
            }
        )
        if response.status_code == 200:
            recovered_wallet = response.json()
            print(f"✅ Wallet recovered: {recovered_wallet['address']}")
            print(f"   Label: {recovered_wallet['label']}")
            print(f"   Funded: {recovered_wallet['funded']}")
            recovered_address = recovered_wallet['address']
        else:
            print(f"❌ Wallet recovery failed: {response.status_code}")
            print(f"   Response: {response.text}")
            recovered_address = None
    except ImportError:
        print("⚠️  Skipping recovery test (stellar_keypair not available)")
        recovered_address = None
    except Exception as e:
        print(f"❌ Wallet recovery error: {e}")
        recovered_address = None
    
    # Test wallet list
    print("\n4. Listing testnet wallets...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/wallet/testnet/list")
        if response.status_code == 200:
            wallets = response.json()
            print(f"✅ Found {wallets['count']} testnet wallets")
            for wallet in wallets["wallets"]:
                print(f"   - {wallet['label']}: {wallet['address']}")
        else:
            print(f"❌ List wallets failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List wallets error: {e}")
    
    # Test get wallet details
    print("\n5. Getting wallet details...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/wallet/testnet/{wallet_address}")
        if response.status_code == 200:
            wallet = response.json()
            print(f"✅ Wallet details retrieved")
            print(f"   Address: {wallet['address']}")
            print(f"   Label: {wallet['label']}")
            print(f"   Balance: {wallet.get('balance', 'N/A')}")
        else:
            print(f"❌ Get wallet failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get wallet error: {e}")
    
    # Test get balance
    print("\n6. Getting wallet balance...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/wallet/testnet/balance/{wallet_address}")
        if response.status_code == 200:
            balance_data = response.json()
            print(f"✅ Balance retrieved")
            print(f"   Balance: {balance_data['balance']}")
        else:
            print(f"❌ Get balance failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get balance error: {e}")
    
    # Test fund wallet (if not already funded)
    print("\n7. Funding wallet...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/wallet/testnet/fund",
            json={"address": wallet_address}
        )
        if response.status_code == 200:
            fund_result = response.json()
            print(f"✅ Fund request processed")
            print(f"   Funded: {fund_result['funded']}")
            print(f"   Message: {fund_result['message']}")
        else:
            print(f"❌ Fund wallet failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Fund wallet error: {e}")
    
    # Test wallet deletion
    print("\n8. Deleting wallet...")
    try:
        response = requests.delete(f"{API_BASE_URL}/api/v1/wallet/testnet/{wallet_address}")
        if response.status_code == 200:
            delete_result = response.json()
            print(f"✅ Wallet deleted")
            print(f"   Message: {delete_result['message']}")
        else:
            print(f"❌ Delete wallet failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Delete wallet error: {e}")
    
    # Clean up recovered wallet if it was created
    if recovered_address:
        print("\n9. Cleaning up recovered wallet...")
        try:
            response = requests.delete(f"{API_BASE_URL}/api/v1/wallet/testnet/{recovered_address}")
            if response.status_code == 200:
                print("✅ Recovered wallet deleted")
            else:
                print(f"⚠️  Could not delete recovered wallet: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
    
    print("\n" + "=" * 50)
    print("Wallet API tests completed!")

if __name__ == "__main__":
    test_wallet_api()
