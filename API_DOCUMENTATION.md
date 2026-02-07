# Metavinci API Documentation

## Overview
Metavinci provides a RESTful API for generating HEAVYMETA 3D asset metadata and managing Soroban smart contracts. The API runs on `http://127.0.0.1:7777` by default.

## Base URL
```
http://127.0.0.1:7777/api/v1
```

## Authentication
Currently, most endpoints are open. Wallet management endpoints require proper wallet setup.

---

## Soroban Contract Endpoints

### Generate Contract
Generate a complete Soroban smart contract from configuration.

**Endpoint:** `POST /api/v1/soroban/generate`

**Request Body:**
```json
{
    "contract_name": "MyNFTCollection",
    "symbol": "MNFT",
    "max_supply": 10000,
    "nft_type": "HVYC",
    "val_props": {
        "health": {
            "prop_name": "health",
            "prop_type": "Int",
            "prop_action_type": "Incremental",
            "initial_value": 100,
            "min_value": 0,
            "max_value": 100
        },
        "level": {
            "prop_name": "level",
            "prop_type": "Int", 
            "prop_action_type": "Setter",
            "initial_value": 1,
            "min_value": 1,
            "max_value": 100
        }
    },
    "write_to_disk": true,
    "output_dir": "/custom/path/optional"
}
```

**Response:**
```json
{
    "success": true,
    "contract_name": "MyNFTCollection",
    "files": {
        "Cargo.toml": "...",
        "src/lib.rs": "...",
        "src/types.rs": "...",
        "src/storage.rs": "...",
        "src/test.rs": "..."
    },
    "output_path": "C:/Users/.../AppData/Local/Temp/soroban_contracts/my_nft_collection_abc12345",
    "build_command": "soroban contract build",
    "deploy_command": "soroban contract deploy --wasm target/wasm32-unknown-unknown/release/my_nft_collection.wasm --network testnet"
}
```

**Example Usage:**
```bash
curl -X POST http://127.0.0.1:7777/api/v1/soroban/generate \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "SpaceWarriors",
    "symbol": "SWARS",
    "max_supply": 10000,
    "nft_type": "HVYC",
    "val_props": {
        "health": {
            "prop_name": "health",
            "prop_type": "Int",
            "prop_action_type": "Incremental",
            "initial_value": 100,
            "min_value": 0,
            "max_value": 100
        }
    }
  }'
```

---

### Build Contract
Build a generated Soroban contract from source files.

**Endpoint:** `POST /api/v1/soroban/build`

**Request Body:**
```json
{
    "contract_path": "/path/to/contract/directory"
}
```

**Response:**
```json
{
    "success": true,
    "build_id": "abc123def456",
    "wasm_path": "/tmp/soroban_build_abc123/target/wasm32-unknown-unknown/release/space_warriors.wasm",
    "wasm_size": 524288,
    "build_output": "Compiling contract...\nBuild completed successfully",
    "error": null
}
```

**Example Usage:**
```bash
# First generate a contract to get the path
GENERATE_RESPONSE=$(curl -s -X POST http://127.0.0.1:7777/api/v1/soroban/generate \
  -H "Content-Type: application/json" \
  -d '{"contract_name": "TestContract", "symbol": "TEST", "max_supply": 1000, "nft_type": "HVYC"}')

# Extract the output path
CONTRACT_PATH=$(echo $GENERATE_RESPONSE | jq -r '.output_path')

# Build the contract
curl -X POST http://127.0.0.1:7777/api/v1/soroban/build \
  -H "Content-Type: application/json" \
  -d "{\"contract_path\": \"$CONTRACT_PATH\"}"
```

---

### Deploy Contract
Deploy a compiled Soroban contract to testnet.

**Endpoint:** `POST /api/v1/soroban/deploy`

**Request Body:**
```json
{
    "wasm_path": "/path/to/contract.wasm",
    "wallet_address": "GABCD...",
    "network": "testnet"
}
```

**Response:**
```json
{
    "success": true,
    "deployment_id": "def456ghi789",
    "contract_id": "CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
    "network": "testnet",
    "stellar_expert_url": "https://stellar.expert/explorer/testnet/contract/CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
    "error": null
}
```

**Example Usage:**
```bash
# First build a contract to get the WASM path
BUILD_RESPONSE=$(curl -s -X POST http://127.0.0.1:7777/api/v1/soroban/build \
  -H "Content-Type: application/json" \
  -d "{\"contract_path\": \"/path/to/contract\"}")

# Extract the WASM path
WASM_PATH=$(echo $BUILD_RESPONSE | jq -r '.wasm_path')

# Get a testnet wallet address
WALLET_ADDRESS="GABCD...EFGH"

# Deploy the contract
curl -X POST http://127.0.0.1:7777/api/v1/soroban/deploy \
  -H "Content-Type: application/json" \
  -d "{
    \"wasm_path\": \"$WASM_PATH\",
    \"wallet_address\": \"$WALLET_ADDRESS\",
    \"network\": \"testnet\"
  }"
```

---

### Generate and Build (Pipeline)
Generate and build a contract in one step.

**Endpoint:** `POST /api/v1/soroban/generate-and-build`

**Request Body:**
```json
{
    "contract_name": "MyNFTCollection",
    "symbol": "MNFT",
    "max_supply": 10000,
    "nft_type": "HVYC",
    "val_props": {
        "health": {
            "prop_name": "health",
            "prop_type": "Int",
            "prop_action_type": "Incremental",
            "initial_value": 100
        }
    }
}
```

**Response:**
```json
{
    "success": true,
    "contract_name": "MyNFTCollection",
    "output_path": "/tmp/soroban_contracts/my_nft_collection_abc12345",
    "wasm_path": "/tmp/soroban_build_def456/target/wasm32-unknown-unknown/release/my_nft_collection.wasm",
    "wasm_size": 524288,
    "build_command": "soroban contract build",
    "deploy_command": "soroban contract deploy --wasm target/wasm32-unknown-unknown/release/my_nft_collection.wasm --network testnet"
}
```

**Example Usage:**
```bash
curl -X POST http://127.0.0.1:7777/api/v1/soroban/generate-and-build \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "SpaceWarriors",
    "symbol": "SWARS",
    "max_supply": 10000,
    "nft_type": "HVYC",
    "val_props": {
        "health": {
            "prop_name": "health",
            "prop_type": "Int",
            "prop_action_type": "Incremental",
            "initial_value": 100
        }
    }
  }'
```

---

### List Deployments
List all Soroban contract deployments with optional filtering.

**Endpoint:** `GET /api/v1/soroban/deployments`

**Query Parameters:**
- `network` (optional): Filter by network (`testnet`, `mainnet`, `futurenet`)
- `wallet_address` (optional): Filter by wallet address
- `status` (optional): Filter by status (`success`, `failed`, `pending`, `error`)

**Response:**
```json
{
    "success": true,
    "deployments": [
        {
            "deployment_id": "def456ghi789",
            "contract_id": "CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
            "network": "testnet",
            "wallet_address": "GABCD...EFGH",
            "deployment_wallet": "Test Wallet",
            "stellar_expert_url": "https://stellar.expert/explorer/testnet/contract/CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
            "timestamp": "2026-01-20T14:30:00.000Z",
            "status": "success",
            "wasm_size": 524288,
            "fees_paid": 100
        }
    ],
    "total": 1
}
```

**Example Usage:**
```bash
# List all deployments
curl -X GET http://127.0.0.1:7777/api/v1/soroban/deployments

# Filter by network
curl -X GET "http://127.0.0.1:7777/api/v1/soroban/deployments?network=testnet"

# Filter by wallet
curl -X GET "http://127.0.0.1:7777/api/v1/soroban/deployments?wallet_address=GABCD...EFGH"

# Filter by status
curl -X GET "http://127.0.0.1:7777/api/v1/soroban/deployments?status=success"
```

---

### Get Deployment
Get a specific deployment record by ID.

**Endpoint:** `GET /api/v1/soroban/deployments/{deployment_id}`

**Response:**
```json
{
    "success": true,
    "deployment": {
        "deployment_id": "def456ghi789",
        "contract_id": "CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
        "network": "testnet",
        "wallet_address": "GABCD...EFGH",
        "deployment_wallet": "Test Wallet",
        "stellar_expert_url": "https://stellar.expert/explorer/testnet/contract/CA7D5K7A4K2L5X5Y6Z8W9J3B4M2K1P2R3",
        "timestamp": "2026-01-20T14:30:00.000Z",
        "status": "success",
        "wasm_size": 524288,
        "fees_paid": 100
    }
}
```

**Example Usage:**
```bash
curl -X GET http://127.0.0.1:7777/api/v1/soroban/deployments/def456ghi789
```

---

### Delete Deployment
Delete a deployment record.

**Endpoint:** `DELETE /api/v1/soroban/deployments/{deployment_id}`

**Response:**
```json
{
    "success": true,
    "message": "Deployment record deleted"
}
```

**Example Usage:**
```bash
curl -X DELETE http://127.0.0.1:7777/api/v1/soroban/deployments/def456ghi789
```

---

## Wallet Management Endpoints

### List Wallets
List all wallets for a specific network.

**Endpoint:** `GET /api/v1/wallets/{network}`

**Path Parameters:**
- `network`: Network name (`testnet`, `mainnet`)

**Response:**
```json
[
    {
        "address": "GABCD...EFGH",
        "network": "testnet",
        "label": "My Test Wallet",
        "created_at": "2026-01-20T10:00:00.000Z"
    }
]
```

**Example Usage:**
```bash
# List testnet wallets
curl -X GET http://127.0.0.1:7777/api/v1/wallets/testnet

# List mainnet wallets
curl -X GET http://127.0.0.1:7777/api/v1/wallets/mainnet
```

---

## Value Property Types

### Prop Action Types
- **Setter**: Direct value assignment (generates `set_<name>` and `get_<name>`)
- **Incremental**: Can only increase (generates `increment_<name>` and `get_<name>`)
- **Decremental**: Can only decrease (generates `decrement_<name>` and `get_<name>`)
- **Bicremental**: Can increase or decrease (generates `increment_<name>`, `decrement_<name>`, and `get_<name>`)

### Prop Types
- **Int**: Integer values
- **Float**: Floating-point values
- **String**: Text values
- **Bool**: Boolean values

---

## Error Responses

All endpoints return consistent error responses:

```json
{
    "detail": "Error description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `403`: Forbidden (mainnet deployment via API)
- `404`: Not Found (wallet/deployment not found)
- `422`: Validation Error (missing required fields)
- `500`: Internal Server Error

---

## Testing Examples

### Complete Pipeline Test
```bash
# 1. Generate contract
curl -X POST http://127.0.0.1:7777/api/v1/soroban/generate \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "TestContract",
    "symbol": "TEST",
    "max_supply": 1000,
    "nft_type": "HVYC",
    "val_props": {
        "counter": {
            "prop_name": "counter",
            "prop_type": "Int",
            "prop_action_type": "Incremental",
            "initial_value": 0
        }
    }
  }'

# 2. Build contract (using output path from step 1)
curl -X POST http://127.0.0.1:7777/api/v1/soroban/build \
  -H "Content-Type: application/json" \
  -d '{"contract_path": "/tmp/soroban_contracts/test_contract_abc12345"}'

# 3. Deploy contract (using WASM path from step 2)
curl -X POST http://127.0.0.1:7777/api/v1/soroban/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "wasm_path": "/tmp/soroban_build_def456/target/wasm32-unknown-unknown/release/test_contract.wasm",
    "wallet_address": "GABCD...EFGH",
    "network": "testnet"
  }'
```

### Quick Test with Python
```python
import requests

# Generate contract
contract_response = requests.post(
    "http://127.0.0.1:7777/api/v1/soroban/generate",
    json={
        "contract_name": "QuickTest",
        "symbol": "QT",
        "max_supply": 100,
        "nft_type": "HVYC",
        "val_props": {
            "counter": {
                "prop_name": "counter",
                "prop_type": "Int",
                "prop_action_type": "Incremental",
                "initial_value": 0
            }
        }
    }
)

if contract_response.status_code == 200:
    contract_data = contract_response.json()
    print(f"Contract generated: {contract_data['contract_name']}")
    
    # Build contract
    build_response = requests.post(
        "http://127.0.0.1:7777/api/v1/soroban/build",
        json={"contract_path": contract_data["output_path"]}
    )
    
    if build_response.status_code == 200:
        build_data = build_response.json()
        print(f"Contract built: {build_data['wasm_path']}")
```

---

## Interactive API Documentation

When Metavinci is running, you can access the interactive API documentation at:
```
http://127.0.0.1:7777/docs
```

This provides a Swagger UI where you can:
- Explore all endpoints
- Test requests directly in your browser
- View request/response schemas
- Download OpenAPI specification

---

## Security Notes

1. **API Deployment Restriction**: Contract deployment via API is restricted to testnet only. Mainnet deployments must be done through the Metavinci UI for security reasons.

2. **Wallet Security**: Testnet wallets are stored unencrypted for convenience. Mainnet wallets require password protection.

3. **File Paths**: All file paths are validated to prevent directory traversal attacks.

4. **Rate Limiting**: Currently not implemented, but consider for production use.

---

## Troubleshooting

### Common Issues

1. **"Soroban CLI not found"**
   - Install Stellar CLI: `cargo install stellar-cli`
   - Ensure it's in your system PATH

2. **"Contract path not found"**
   - Ensure the contract was generated first
   - Check the `output_path` from the generate response

3. **"WASM file not found"**
   - Verify the build completed successfully
   - Check build output for errors

4. **"Wallet not found"**
   - Create a wallet using the Metavinci UI first
   - Ensure you're using the correct network (testnet/mainnet)

### Getting Help

For additional support:
1. Check the Metavinci logs in your AppData directory
2. Use the interactive API docs at `http://127.0.0.1:7777/docs`
3. Review the generated contract files in the output directory
