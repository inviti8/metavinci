# HEAVYMETADATA Server Integration Plan

## Implementation Checklist

### Phase 1: Metadata API Server

#### 1.1 Setup & Dependencies
- [x] Add FastAPI, uvicorn, pydantic to `requirements.txt`
- [x] Add dataclasses-json to `requirements.txt`
- [x] Verify dependencies install correctly

#### 1.2 Data Classes Module (`hvym_metadata.py`)
- [x] Create base data class with `dictionary` and `json` properties
- [x] Port `collection_data_class`
- [x] Port value property classes:
  - [x] `int_data_class`
  - [x] `float_data_class`
  - [x] `cremental_int_data_class`
  - [x] `cremental_float_data_class`
- [x] Port behavior classes:
  - [x] `behavior_data_class`
  - [x] `int_data_behavior_class`
  - [x] `float_data_behavior_class`
- [x] Port text/call classes:
  - [x] `text_data_class`
  - [x] `call_data_class`
- [x] Port mesh/node classes:
  - [x] `mesh_data_class`
  - [x] `mesh_set_data_class`
  - [x] `single_mesh_data_class`
  - [x] `single_node_data_class`
  - [x] `morph_set_data_class`
- [x] Port material classes:
  - [x] `mat_prop_data_class`
  - [x] `mat_set_data_class`
  - [x] `basic_material_class`
  - [x] `lambert_material_class`
  - [x] `phong_material_class`
  - [x] `standard_material_class`
  - [x] `pbr_material_class`
- [x] Port animation class:
  - [x] `anim_prop_data_class`
- [x] Port UI/widget classes:
  - [x] `widget_data_class`
  - [x] `slider_data_class`
  - [x] `menu_data_class`
  - [x] `action_data_class`
  - [x] `property_label_data_class`
- [x] Port interactable class:
  - [x] `interactable_data_class`

#### 1.3 API Server Worker (`api_server.py`)
- [x] Create `ApiServerWorker(QThread)` class
- [x] Implement server start/stop signals
- [x] Implement graceful shutdown
- [x] Configure CORS for localhost
- [x] Set up logging integration

#### 1.4 API Routes (`api_routes.py`)
- [x] Health check endpoint (`/api/v1/health`)
- [x] Status endpoint (`/api/v1/status`)
- [x] Collection endpoint (`/api/v1/collection`)
- [x] Value property endpoints:
  - [x] `/api/v1/property/int`
  - [x] `/api/v1/property/float`
  - [x] `/api/v1/property/text`
  - [x] `/api/v1/behavior`
- [x] Material endpoints:
  - [x] `/api/v1/material/basic`
  - [x] `/api/v1/material/lambert`
  - [x] `/api/v1/material/phong`
  - [x] `/api/v1/material/standard`
  - [x] `/api/v1/material/pbr`
  - [x] `/api/v1/mat-prop`
  - [x] `/api/v1/mat-set`
- [x] Mesh endpoints:
  - [x] `/api/v1/mesh`
  - [x] `/api/v1/mesh-set`
  - [x] `/api/v1/morph-set`
  - [x] `/api/v1/node`
- [x] Animation endpoint (`/api/v1/animation`)
- [x] UI endpoints:
  - [x] `/api/v1/menu`
  - [x] `/api/v1/action`
  - [x] `/api/v1/labels`
  - [x] `/api/v1/slider` - Base slider widget data
  - [x] `/api/v1/single/int` - Named int value (not slider)
  - [x] `/api/v1/single/float` - Named float value (not slider)
  - [x] `/api/v1/single/mesh` - Single mesh reference
- [x] Interactable endpoint (`/api/v1/interactable`)
- [x] Parse endpoints (from GLTF extension data):
  - [x] `/api/v1/parse/blender-collection` - Full collection (collection + menu + nodes + actions JSON)
  - [x] `/api/v1/parse/val-prop` - Raw Blender property → int/float data class
  - [x] `/api/v1/parse/behavior-val-prop` - Property with behaviors → behavior data class
  - [x] `/api/v1/parse/interactables` - Blender interactables → interactable data structures

#### 1.5 Metavinci Integration
- [x] Add API server initialization to `__init__`
- [x] Add server start on application launch
- [x] Add graceful shutdown on application quit
- [x] Add "Metadata API" submenu to tray:
  - [x] Status indicator
  - [x] "Open API Docs" action
  - [x] Port configuration option
  - [x] Restart server option
- [x] Store API port in TinyDB config
- [x] Add logging for API events

#### 1.6 Testing
- [x] Unit tests for data classes
- [x] Unit tests for API endpoints
- [x] Integration test: server start/stop
- [x] Integration test: endpoint responses
- [x] Manual test: Swagger UI at `/docs`
- [x] CLI comparison tests (37/40 passed - 3 failures are CLI bugs)

---

### Phase 2: Soroban Contract Generation

#### 2.1 Template System
- [x] Create `templates/soroban/` directory
- [x] Create `types.rs.j2` template
- [x] Create `lib.rs.j2` template
- [x] Create `storage.rs.j2` template
- [x] Create `Cargo.toml.j2` template
- [x] Create `test.rs.j2` template
- [x] Add Jinja2 to dependencies (if not present)

#### 2.2 Contract Generator Module (`soroban_generator.py`)
- [x] Template loader function
- [x] Type generation function
- [x] Contract generation function
- [x] Full project generation function
- [x] Validation for input data

#### 2.3 Soroban API Routes
- [x] `/api/v1/soroban/generate` - Full contract
- [x] `/api/v1/soroban/types` - Types only
- [x] `/api/v1/soroban/validate` - Validate configuration
- [x] `/api/v1/soroban/templates` - List templates

#### 2.4 Value Property Generation
- [x] Incremental function template
- [x] Decremental function template
- [x] Bicremental function template
- [x] Setter function template
- [x] Getter function template
- [x] Property config function template

#### 2.5 NFT Core Functions
- [x] `initialize()` template
- [x] `mint()` template
- [x] `transfer()` template
- [x] `balance_of()` template
- [x] `owner_of()` template
- [x] `total_supply()` template
- [x] `tokens_of()` template

#### 2.6 Testing
- [x] Unit tests for template rendering (added to test_api.py)
- [ ] Test generated contract compiles
- [ ] Test generated contract deploys to testnet
- [ ] Verify value property functions work correctly

---

### Documentation & Cleanup
- [ ] Update README with API documentation
- [x] Add example requests/responses (Soroban section added)
- [x] Document configuration options (Build Pipeline section added)
- [ ] Clean up any unused code

---

### Phase 3: Stellar Wallet Management

#### 3.1 Wallet Storage System ✅
- [x] Create `wallet_manager.py` module
- [x] Implement encrypted wallet storage (TinyDB with encryption)
- [x] Define wallet data structure:
  - Public key (address)
  - Encrypted secret key (mainnet only)
  - Network (testnet/mainnet)
  - Creation timestamp
  - Label/name
- [x] Implement wallet CRUD operations
- [x] Add to build pipeline (`build_cross_platform.py`)

#### 3.2 Wallet Generation ✅
- [x] Testnet wallet generation (auto-funded via Friendbot)
- [x] Mainnet wallet generation (password-protected)
- [x] Password encryption for mainnet secret keys
- [x] Wallet recovery from secret key

#### 3.3 Wallet API Endpoints (Testnet Only) ✅

> **Security Note:** API endpoints are restricted to testnet wallets only.
> Mainnet wallets must be created through the Metavinci UI for security.

- [x] Create API routes in `api_routes.py`
- [x] Implement testnet wallet creation endpoint
- [x] Implement wallet listing endpoint
- [x] Implement wallet details endpoint
- [x] Implement testnet wallet funding endpoint
- [x] Implement balance checking endpoint
- [x] Implement wallet recovery endpoint
- [x] Implement wallet deletion endpoint

#### 3.4 UI Integration ✅
- [x] Create wallet management UI in Metavinci
- [x] Implement wallet creation dialog with network selection
- [x] Implement wallet list view with copy/fund/delete actions
- [x] Add balance display capability
- [x] Add testnet funding button
- [x] Add wallet deletion confirmation
- [x] Add copy address functionality
- [x] Add wallet details dialog with public/private keys and seed phrase
- [x] Add network switching (testnet/mainnet selector)
- [x] Add password protection for mainnet wallets
- [x] Add seed phrase generation from private keys

#### 3.5 Testing
- [ ] Unit tests for wallet operations
- [ ] Integration tests with testnet
- [ ] Security testing
- [ ] UI tests for wallet management

#### 3.6 Documentation
- [ ] Update API documentation
- [ ] Add wallet management user guide
- [ ] Document security considerations

- [x] `POST /api/v1/wallet/testnet/create` - Create testnet wallet (auto-funded)
  - Parameters: label (optional)
  - Returns: address, funded status
- [x] `POST /api/v1/wallet/recover` - Recover wallet from secret key
  - Parameters: secret_key, network, label (optional), password (mainnet only)
  - Returns: address, network, funded status
- [x] `GET /api/v1/wallet/testnet/list` - List testnet wallets
- [x] `GET /api/v1/wallet/testnet/{address}` - Get testnet wallet details
- [x] `DELETE /api/v1/wallet/testnet/{address}` - Remove testnet wallet
- [x] `POST /api/v1/wallet/testnet/fund` - Fund testnet wallet via Friendbot
- [x] `GET /api/v1/wallet/testnet/balance/{address}` - Get testnet wallet balance

#### 3.4 Metavinci UI Integration ✅
- [x] Add "Wallet Management" submenu to tray
- [x] Network selector dropdown (testnet/mainnet, default: testnet)
- [x] "Create Wallet" dialog
  - Network selection
  - Label input
  - Password input (mainnet only, with confirmation)
- [x] "View Wallets" window
  - List of wallets with network, label, address, balance
  - Copy address button
  - Fund button (testnet only)
  - Delete button
- [x] Status indicator showing active wallet count

#### 3.5 Security Considerations ✅
- [x] Never store unencrypted mainnet secret keys (encrypted with Fernet)
- [x] Use secure password hashing (PBKDF2HMAC with SHA-256, 480k iterations)
- [x] Clear sensitive data from memory after use (handled by Python GC)
- [x] Warn users about mainnet operations (UI warnings displayed)
- [-] Backup/export functionality (encrypted) - Skipped for now

#### 3.6 Build Pipeline Updates (if needed) ✅
- [x] Include `wallet_manager.py` in build pipeline
- [x] Add wallet management dependencies to requirements.txt
- [x] Update build script to handle new wallet files
- [x] Ensure wallet data directory is created during installation
- [x] Add wallet manager imports to main application

---

### Phase 4: Contract Compilation & Deployment

> **Prerequisite:** Phase 3 (Wallet Management) must be completed first

#### 4.1 Contract Build System
- [ ] Create `contract_builder.py` module with ContractBuilder class
- [ ] Implement contract structure validation (Cargo.toml, src/lib.rs)
- [ ] Add Soroban CLI detection and version checking
- [ ] Create temporary build directory management
- [ ] Execute `soroban contract build` command with progress callbacks
- [ ] Capture build output, errors, and WASM file generation
- [ ] Return structured build results with metadata
- [ ] Add build artifact cleanup functionality
- [ ] Implement error handling for missing dependencies and build failures

#### 4.2 Contract Deployment System
- [ ] Create `contract_deployer.py` module with ContractDeployer class
- [ ] Implement wallet integration with WalletManager for authentication
- [ ] Add network configuration (testnet/mainnet/futurenet/local)
- [ ] Deploy compiled WASM to selected network with proper transaction building
- [ ] Implement wallet selection dialog for deployment authorization
- [ ] Add mainnet password protection and validation
- [ ] Return deployed contract ID and transaction hash
- [ ] Generate Stellar Expert URLs for deployed contracts
- [ ] Create `deployment_manager.py` for deployment record storage
- [ ] Store comprehensive deployment records (contract ID, network, timestamp, stellar_expert_url, deployment_wallet, metadata)
- [ ] Implement deployment status tracking and error handling
- [ ] Add balance checking and fee estimation

#### 4.3 Deployment API Endpoints (Testnet Only)

> **Security Note:** API deployment is restricted to testnet only.
> Mainnet deployments must be done through the Metavinci UI.

- [ ] `POST /api/v1/soroban/build` - Build contract from generated files
  - Input: Generated contract files (from `/soroban/generate`)
  - Output: Build status, WASM path or errors
- [ ] `POST /api/v1/soroban/deploy` - Deploy built contract to testnet
  - Input: WASM path, testnet wallet address
  - Output: Contract ID, transaction hash
- [ ] `POST /api/v1/soroban/generate-and-deploy` - Full pipeline (testnet)
  - Input: Contract config + testnet wallet
  - Output: Build status + deployment results
- [ ] `GET /api/v1/soroban/deployments` - List deployment records
  - Query params: network, wallet_address
  - Output: Deployment records with metadata

#### 4.4 UI Integration
- [x] Create WalletSelectionDialog for deployment authorization
- [x] Implement DeploymentCompletionDialog showing deployment results
- [x] Create DeploymentListDialog for viewing deployment history
- [x] Add "Soroban Deployments" to wallet tray menu
- [ ] Implement build/deploy progress dialogs with callbacks
- [x] Add network-specific filtering in deployment list
- [x] Implement copy-to-clipboard for contract IDs
- [x] Add Stellar Expert URL integration for contract exploration
- [x] Create deployment record management UI (view, delete, export)
- [x] Add deployment status indicators and color coding

#### 4.5 Soroban CLI Integration
- [ ] Detect Soroban CLI installation
- [ ] Prompt user to install if missing
- [ ] Verify Rust/Cargo toolchain
- [ ] Handle CLI version compatibility

#### 4.6 Testing
- [ ] Test contract compilation
- [ ] Test testnet deployment
- [ ] Test deployment record storage
- [ ] End-to-end: generate → build → deploy → verify

---

## Build Pipeline: Adding New Python Files

When adding new Python modules to the project, update `build_cross_platform.py` to ensure they are included in the PyInstaller build:

### 1. Add to Source Files List

In the `copy_source_files()` method, add the new file to the `source_files` list:

```python
source_files = [
    # ... existing files ...
    ('your_new_module.py', 'your_new_module.py'),
]
```

### 2. Add to Hidden Imports

In the `build_executable()` method, add the module to `api_hidden_imports`:

```python
api_hidden_imports = [
    # ... existing imports ...
    'your_new_module',
]
```

### 3. Add Any New Dependencies

If your module uses external packages not already in `requirements.txt`:
- Add them to `requirements.txt`
- Add them to `api_hidden_imports` if they need explicit inclusion

### 4. Add Data Directories (if applicable)

If your module uses data files (templates, configs, etc.), add the directory to:

**Source directories list:**
```python
directories = ['images', 'data', 'service', 'templates', 'your_data_dir']
```

**PyInstaller `--add-data` flags (platform-specific separators):**
```python
# Windows
pyinstaller_cmd.extend(['--add-data', 'your_data_dir;your_data_dir'])
# Unix
pyinstaller_cmd.extend(['--add-data', 'your_data_dir:your_data_dir'])
```

### 5. Handle Frozen Environment Paths

If your module loads files at runtime, handle both development and frozen (PyInstaller) environments:

```python
import sys
from pathlib import Path

def _get_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent
    return base_path / "your_data_dir"
```

### Current Build Pipeline Files

| File | Purpose | Build Updates Required |
|------|---------|----------------------|
| `hvym_metadata.py` | Data classes | Source file, hidden import |
| `api_server.py` | FastAPI server worker | Source file, hidden import |
| `api_routes.py` | API route definitions | Source file, hidden import |
| `soroban_generator.py` | Contract generation | Source file, hidden import, jinja2 import |
| `templates/` | Jinja2 templates | Data directory, --add-data |

---

*Last updated: 2026-01-19 - Phase 3 & 4 planned (Wallet Management & Deployment)*

---

## Overview

This document outlines the plan to add local API server functionality to Metavinci, enabling metadata generation endpoints that serve HEAVYMETA 3D asset metadata structures.

> **Note**: This plan focuses on **3D asset metadata only**. Contract/blockchain functionality (previously ICP, now Stellar Soroban) is out of scope until the Proprium metadata system is ported to Soroban.

## Objective

When Metavinci is running (in the system tray), expose a local HTTP API that allows external tools (Blender addons, web interfaces, other applications) to generate HEAVYMETA metadata structures for 3D assets without requiring the hvym CLI.

---

## Current State Analysis

### hvym CLI Data Classes (Source: `heavymeta-cli-dev/hvym.py`)

The hvym CLI contains data classes for 3D asset metadata generation. **Excluding contract/blockchain classes**, the relevant ones are:

| Category | Classes |
|----------|---------|
| **Collection** | `collection_data_class` |
| **Values** | `int_data_class`, `float_data_class`, `cremental_int_data_class`, `cremental_float_data_class` |
| **Behaviors** | `behavior_data_class`, `int_data_behavior_class`, `float_data_behavior_class` |
| **Text/Calls** | `text_data_class`, `call_data_class` |
| **Mesh/Nodes** | `mesh_data_class`, `mesh_set_data_class`, `single_mesh_data_class`, `single_node_data_class`, `morph_set_data_class` |
| **Animation** | `anim_prop_data_class` |
| **Materials** | `mat_prop_data_class`, `mat_set_data_class`, `basic_material_class`, `lambert_material_class`, `phong_material_class`, `standard_material_class`, `pbr_material_class` |
| **UI/Widgets** | `widget_data_class`, `slider_data_class`, `menu_data_class`, `action_data_class`, `property_label_data_class` |
| **Interactive** | `interactable_data_class` |

### Out of Scope (for now)

- `contract_data_class` - Blockchain contract configuration
- ICP/Motoko template generation
- Minting flows
- All blockchain-specific functionality

These will be addressed separately when Proprium metadata is ported to Stellar Soroban.

### Metavinci Application (Source: `metavinci/metavinci.py`)

- PyQt5 system tray application
- Runs continuously in background
- Extensive `QThread` patterns for async operations
- TinyDB for configuration persistence
- No existing HTTP server
- Binds to localhost for Pintheon services (port 9998/9999)

---

## Difficulty Assessment

**Overall Difficulty: MODERATE**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Data class extraction | Low | Copy/adapt from hvym.py |
| HTTP server integration | Low-Medium | FastAPI + uvicorn in QThread |
| Thread safety | Medium | Signal-slot pattern exists |
| API design | Low | RESTful JSON endpoints |
| Testing | Medium | Need mock requests |
| Packaging | Low | Add dependencies to requirements.txt |

**Estimated Effort: 2-3 days for core implementation**

---

## Architecture

### Proposed Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Metavinci (PyQt5)                     │
│  ┌─────────────────────────────────────────────────────┐│
│  │                  Main Thread (Qt)                   ││
│  │  - System Tray UI                                   ││
│  │  - Menu Actions                                     ││
│  │  - Signal Handlers                                  ││
│  └─────────────────────────────────────────────────────┘│
│                          │                              │
│                    Signals/Slots                        │
│                          │                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │              API Server Thread (QThread)            ││
│  │  ┌─────────────────────────────────────────────┐   ││
│  │  │         FastAPI + Uvicorn Server            │   ││
│  │  │  - Metadata generation endpoints            │   ││
│  │  │  - Status/health endpoints                  │   ││
│  │  │  - Bound to 127.0.0.1:PORT                  │   ││
│  │  └─────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Server Technology Choice

**Recommended: FastAPI + Uvicorn**

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** | Automatic OpenAPI docs, async support, modern, type hints | Requires uvicorn |
| Flask | Simple, well-known | Synchronous, no auto-docs |
| aiohttp | Fully async | More complex setup |
| http.server | No dependencies | Very basic, no routing |

FastAPI provides:
- Automatic JSON serialization of dataclasses
- OpenAPI/Swagger documentation at `/docs`
- Pydantic validation
- Easy async support

---

## Implementation Plan

### Phase 1: Data Classes Module

**Create: `metavinci/hvym_metadata.py`**

Extract and adapt data classes from hvym CLI:

```python
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from typing import Optional, List, Dict, Any
import json

@dataclass
class BaseDataClass:
    @property
    def dictionary(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def json(self) -> str:
        return json.dumps(self.dictionary)

@dataclass_json
@dataclass
class CollectionData(BaseDataClass):
    collectionName: str = ''
    collectionType: str = ''
    valProps: Dict = None
    textValProps: Dict = None
    callProps: Dict = None
    meshProps: Dict = None
    meshSets: Dict = None
    morphSets: Dict = None
    animProps: Dict = None
    matProps: Dict = None
    materialSets: Dict = None
    menuData: Dict = None
    propLabelData: Dict = None
    nodes: Dict = None
    actionProps: Dict = None

# ... additional classes
```

### Phase 2: API Server Worker

**Create: `metavinci/api_server.py`**

```python
from PyQt5.QtCore import QThread, pyqtSignal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

class ApiServerWorker(QThread):
    started = pyqtSignal()
    stopped = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, port: int = 7777, parent=None):
        super().__init__(parent)
        self.port = port
        self.server = None
        self._running = False

    def run(self):
        try:
            app = create_api_app()
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=self.port,
                log_level="warning"
            )
            self.server = uvicorn.Server(config)
            self._running = True
            self.started.emit()
            asyncio.run(self.server.serve())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._running = False
            self.stopped.emit()

    def stop(self):
        if self.server:
            self.server.should_exit = True

def create_api_app() -> FastAPI:
    app = FastAPI(
        title="HEAVYMETADATA API",
        description="Local metadata generation service",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # localhost only anyway
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from . import api_routes
    app.include_router(api_routes.router)

    return app
```

### Phase 3: API Routes

**Create: `metavinci/api_routes.py`**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .hvym_metadata import *

router = APIRouter(prefix="/api/v1", tags=["metadata"])

# ============ Request Models ============

class CollectionRequest(BaseModel):
    collectionName: str
    collectionType: str = "multi"
    valProps: Optional[Dict] = None
    textValProps: Optional[Dict] = None
    # ... etc

class IntPropertyRequest(BaseModel):
    name: str
    default: int = 0
    min: int = 0
    max: int = 100
    immutable: bool = False
    show: bool = True
    prop_slider_type: str = "RANGE"
    prop_action_type: str = "Setter"

class MaterialRequest(BaseModel):
    material_type: str  # basic, lambert, phong, standard, pbr
    color: str = "#FFFFFF"
    # ... type-specific fields

# ============ Endpoints ============

@router.get("/health")
async def health_check():
    return {"status": "running", "service": "heavymetadata"}

@router.get("/status")
async def get_status():
    return {
        "api_version": "1.0.0",
        "endpoints": [
            "/api/v1/collection",
            "/api/v1/property/int",
            "/api/v1/property/float",
            "/api/v1/property/text",
            "/api/v1/material/{type}",
            "/api/v1/animation",
            "/api/v1/mesh",
            "/api/v1/mesh-set",
            "/api/v1/interactable",
        ]
    }

# ---- Collection ----

@router.post("/collection")
async def create_collection(req: CollectionRequest):
    data = CollectionData(
        collectionName=req.collectionName,
        collectionType=req.collectionType,
        valProps=req.valProps or {},
        textValProps=req.textValProps or {},
        # ... etc
    )
    return data.dictionary

# ---- Value Properties ----

@router.post("/property/int")
async def create_int_property(req: IntPropertyRequest):
    data = IntData(
        name=req.name,
        default=req.default,
        min=req.min,
        max=req.max,
        immutable=req.immutable,
        show=req.show,
        widget_type="INT",
        prop_slider_type=req.prop_slider_type,
        prop_action_type=req.prop_action_type,
    )
    return data.dictionary

@router.post("/property/float")
async def create_float_property(req: FloatPropertyRequest):
    # Similar to int
    pass

@router.post("/property/text")
async def create_text_property(req: TextPropertyRequest):
    pass

# ---- Materials ----

@router.post("/material/basic")
async def create_basic_material(req: BasicMaterialRequest):
    data = BasicMaterial(color=req.color, ...)
    return data.dictionary

@router.post("/material/pbr")
async def create_pbr_material(req: PBRMaterialRequest):
    data = PBRMaterial(...)
    return data.dictionary

# ---- Mesh & Animation ----

@router.post("/mesh")
async def create_mesh_property(req: MeshRequest):
    pass

@router.post("/mesh-set")
async def create_mesh_set(req: MeshSetRequest):
    pass

@router.post("/animation")
async def create_animation_property(req: AnimationRequest):
    pass

# ---- Interactables ----

@router.post("/interactable")
async def create_interactable(req: InteractableRequest):
    pass

# ---- Parsing (from GLTF extension / Blender export) ----

class ValPropParseRequest(BaseModel):
    prop_action_type: str  # Immutable, Static, Incremental, Decremental, Bicremental, Setter
    prop_value_type: str = "Int"  # Int or Float
    prop_slider_type: str = "RANGE"
    show: bool = True
    prop_immutable: bool = False
    int_default: int = 0
    int_min: int = 0
    int_max: int = 100
    int_amount: int = 1
    float_default: float = 0.0
    float_min: float = 0.0
    float_max: float = 1.0
    float_amount: float = 0.1
    behavior_set: Optional[List] = None

class BlenderCollectionParseRequest(BaseModel):
    collection_name: str
    collection_type: str
    collection_id: str
    collection_json: Dict[str, Any]  # Raw Blender collection data
    menu_json: Dict[str, Any]        # Raw Blender menu data
    nodes_json: Dict[str, Any]       # Raw Blender nodes data
    actions_json: Dict[str, Any]     # Raw Blender actions data

class InteractablesParseRequest(BaseModel):
    obj_data: Dict[str, Any]  # Raw Blender interactables object data

@router.post("/parse/val-prop")
async def parse_val_prop(req: ValPropParseRequest):
    """Parse raw Blender value property into HVYM int/float data class"""
    # Logic from hvym CLI parse_val_prop()
    if req.prop_action_type in ['Immutable', 'Static']:
        if req.prop_value_type == 'Float':
            return FloatData(...).dictionary
        return IntData(...).dictionary
    else:
        if req.prop_value_type == 'Float':
            return CrementalFloatData(...).dictionary
        return CrementalIntData(...).dictionary

@router.post("/parse/behavior-val-prop")
async def parse_behavior_val_prop(req: ValPropParseRequest):
    """Parse property with behaviors into HVYM behavior data class"""
    # Logic from hvym CLI parse_behavior_val_prop()
    if req.prop_action_type in ['Immutable', 'Static']:
        return IntDataBehavior(...).dictionary
    return CrementalIntDataBehavior(...).dictionary

@router.post("/parse/blender-collection")
async def parse_blender_collection(req: BlenderCollectionParseRequest):
    """Parse full Blender collection export (collection + menu + nodes + actions) into HVYM format"""
    # Logic from hvym CLI parse_blender_hvym_collection()
    # Iterates through collection_json, menu_json, nodes_json, actions_json
    # Returns complete CollectionData structure
    pass

@router.post("/parse/interactables")
async def parse_interactables(req: InteractablesParseRequest):
    """Parse Blender interactables into HVYM interactable data structures"""
    # Logic from hvym CLI parse_blender_hvym_interactables()
    pass
```

### Phase 4: Integration with Metavinci

**Modify: `metavinci/metavinci.py`**

```python
# Add to imports
from api_server import ApiServerWorker

# Add to Metavinci.__init__ (around line 1541)
def __init__(self):
    # ... existing init code ...

    # Initialize API server
    self.api_server = None
    self.API_PORT = self._get_config('api_port', 7777)
    self._start_api_server()

    # Add to tray menu
    self._add_api_menu_items()

def _start_api_server(self):
    """Start the local metadata API server"""
    self.api_server = ApiServerWorker(port=self.API_PORT, parent=self)
    self.api_server.started.connect(self._on_api_started)
    self.api_server.stopped.connect(self._on_api_stopped)
    self.api_server.error.connect(self._on_api_error)
    self.api_server.start()

def _stop_api_server(self):
    """Stop the API server gracefully"""
    if self.api_server and self.api_server.isRunning():
        self.api_server.stop()
        self.api_server.wait(5000)  # Wait up to 5 seconds

def _on_api_started(self):
    logging.info(f"HEAVYMETADATA API started on port {self.API_PORT}")
    self._update_api_menu_state(running=True)

def _on_api_stopped(self):
    logging.info("HEAVYMETADATA API stopped")
    self._update_api_menu_state(running=False)

def _on_api_error(self, error: str):
    logging.error(f"HEAVYMETADATA API error: {error}")

def _add_api_menu_items(self):
    """Add API server controls to tray menu"""
    api_menu = QMenu("Metadata API", self.menu)

    self.api_status_action = QAction("Status: Starting...", self)
    self.api_status_action.setEnabled(False)
    api_menu.addAction(self.api_status_action)

    api_menu.addSeparator()

    open_docs_action = QAction("Open API Docs", self)
    open_docs_action.triggered.connect(
        lambda: webbrowser.open(f"http://127.0.0.1:{self.API_PORT}/docs")
    )
    api_menu.addAction(open_docs_action)

    # ... restart, port config options

    self.menu.insertMenu(self.exit_action, api_menu)

# Add to quit handler
def _quit_application(self):
    self._stop_api_server()
    # ... existing quit code ...
```

### Phase 5: Dependencies

**Update: `requirements.txt`**

```
# Existing dependencies...
PyQt5==5.15.0
requests>=2.32.5
tinydb>=4.8.0

# New API server dependencies
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0
dataclasses-json>=0.6.0
```

---

## API Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/status` | API status and available endpoints |
| GET | `/docs` | OpenAPI/Swagger documentation |
| POST | `/api/v1/collection` | Generate collection metadata |
| POST | `/api/v1/property/int` | Generate integer property |
| POST | `/api/v1/property/float` | Generate float property |
| POST | `/api/v1/property/text` | Generate text property |
| POST | `/api/v1/behavior` | Generate behavior definition |
| POST | `/api/v1/material/basic` | Generate basic material |
| POST | `/api/v1/material/lambert` | Generate lambert material |
| POST | `/api/v1/material/phong` | Generate phong material |
| POST | `/api/v1/material/standard` | Generate standard material |
| POST | `/api/v1/material/pbr` | Generate PBR material |
| POST | `/api/v1/mat-prop` | Generate material property reference |
| POST | `/api/v1/mat-set` | Generate material set |
| POST | `/api/v1/mesh` | Generate mesh property |
| POST | `/api/v1/mesh-set` | Generate mesh set |
| POST | `/api/v1/morph-set` | Generate morph set |
| POST | `/api/v1/node` | Generate node reference |
| POST | `/api/v1/animation` | Generate animation property |
| POST | `/api/v1/interactable` | Generate interactable config |
| POST | `/api/v1/menu` | Generate menu configuration |
| POST | `/api/v1/action` | Generate action configuration |
| POST | `/api/v1/labels` | Generate property labels |
| POST | `/api/v1/slider` | Generate base slider widget data |
| POST | `/api/v1/single/int` | Generate named int value (not slider) |
| POST | `/api/v1/single/float` | Generate named float value (not slider) |
| POST | `/api/v1/single/mesh` | Generate single mesh reference |
| POST | `/api/v1/parse/blender-collection` | Parse full Blender collection export (collection + menu + nodes + actions) |
| POST | `/api/v1/parse/val-prop` | Parse raw Blender value property → int/float data class |
| POST | `/api/v1/parse/behavior-val-prop` | Parse property with behaviors → behavior data class |
| POST | `/api/v1/parse/interactables` | Parse Blender interactables → interactable structures |
| **Soroban** | | |
| POST | `/api/v1/soroban/generate` | Generate complete Soroban smart contract |
| POST | `/api/v1/soroban/types` | Generate only type definitions |
| POST | `/api/v1/soroban/validate` | Validate contract configuration |
| GET | `/api/v1/soroban/templates` | List available contract templates |

---

## Soroban Contract Generation

### Example Request

```bash
curl -X POST http://127.0.0.1:7777/api/v1/soroban/generate \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "SpaceWarriors",
    "symbol": "SWARS",
    "max_supply": 10000,
    "nft_type": "HVYC",
    "write_to_disk": true,
    "val_props": {
        "health": {
            "default": 100,
            "min": 0,
            "max": 100,
            "amount": 10,
            "prop_action_type": "Bicremental"
        },
        "power": {
            "default": 50,
            "min": 0,
            "max": 200,
            "amount": 5,
            "prop_action_type": "Incremental"
        }
    }
  }'
```

### Example Response

```json
{
    "success": true,
    "contract_name": "SpaceWarriors",
    "files": {
        "Cargo.toml": "...",
        "src/lib.rs": "...",
        "src/types.rs": "...",
        "src/storage.rs": "...",
        "src/test.rs": "..."
    },
    "output_path": "C:/Users/.../AppData/Local/Temp/soroban_contracts/space_warriors_abc12345",
    "build_command": "soroban contract build",
    "deploy_command": "soroban contract deploy --wasm target/wasm32-unknown-unknown/release/space_warriors.wasm --network testnet"
}
```

**Note:** When `write_to_disk` is `true` (default), the generated contract files are written to `output_path` on disk, ready for compilation with `soroban contract build`. Set `write_to_disk: false` to return files in memory only without writing to disk.

### Value Property Action Types

| Action Type | Generated Functions | Description |
|-------------|---------------------|-------------|
| `Incremental` | `increment_<name>()`, `get_<name>()` | Value can only increase |
| `Decremental` | `decrement_<name>()`, `get_<name>()` | Value can only decrease |
| `Bicremental` | `increment_<name>()`, `decrement_<name>()`, `get_<name>()` | Value can increase or decrease |
| `Setter` | `set_<name>()`, `get_<name>()` | Direct value assignment |
| `Static` | None | Value baked into metadata, no contract functions |

### Building & Deploying Generated Contracts

```bash
# Save generated files to a directory
mkdir my_contract && cd my_contract
# (save Cargo.toml to ./Cargo.toml)
# (save src/*.rs files to ./src/)

# Build the contract
soroban contract build

# Deploy to testnet
soroban contract deploy \
  --wasm target/wasm32-unknown-unknown/release/my_contract.wasm \
  --network testnet
```

---

## File Structure (New Files)

```
metavinci/
├── metavinci.py              # Modified - API server integration
├── hvym_metadata.py          # NEW - Data classes
├── api_server.py             # NEW - Server worker thread
├── api_routes.py             # NEW - FastAPI routes
├── soroban_generator.py      # NEW - Soroban contract generator
├── requirements.txt          # Modified - new dependencies
├── build_cross_platform.py   # Modified - includes templates
└── templates/
    └── soroban/
        ├── Cargo.toml.j2     # Cargo build configuration
        ├── lib.rs.j2         # Main contract implementation
        ├── types.rs.j2       # Type definitions & errors
        ├── storage.rs.j2     # Storage key definitions
        └── test.rs.j2        # Unit test scaffolding
```

---

## Testing Plan

### Unit Tests

```python
# tests/test_metadata.py
def test_collection_data():
    data = CollectionData(collectionName="Test", collectionType="multi")
    assert data.dictionary["collectionName"] == "Test"

def test_int_property():
    data = IntData(name="health", default=100, min=0, max=100)
    assert data.dictionary["default"] == 100
```

### Integration Tests

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from api_server import create_api_app

client = TestClient(create_api_app())

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_create_collection():
    response = client.post("/api/v1/collection", json={
        "collectionName": "TestNFT",
        "collectionType": "multi"
    })
    assert response.status_code == 200
    assert response.json()["collectionName"] == "TestNFT"
```

---

## Security Considerations

1. **Localhost Only**: Bind to `127.0.0.1`, never `0.0.0.0`
2. **No Authentication Required**: Local service, trusted environment
3. **CORS Enabled**: Allow browser-based tools to access API
4. **No Sensitive Data**: Metadata generation only, no secrets
5. **Rate Limiting**: Optional, for resource protection

---

## Phase 2: Stellar Soroban Contract Generation

### Overview

Once the metadata API is operational, the next phase adds **automated Soroban smart contract generation** based on Proprium data structures. This ports the ICP/Motoko contract generation system to Stellar's Soroban (Rust-based).

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Proprium Content Flow                         │
│                                                                  │
│  Blender Addon                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │  Metavinci   │──► Metadata API (Phase 1)                      │
│  │  (running)   │                                                │
│  └──────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐   3D Asset    ┌─────────────────────────────┐ │
│  │  Pintheon    │ ────────────► │  IPFS                       │ │
│  │  (IPFS node) │   + Metadata  │  Returns CID                │ │
│  └──────────────┘               └─────────────────────────────┘ │
│       │                                    │                     │
│       │ Collection                         │ CID                 │
│       │ Config                             │                     │
│       ▼                                    ▼                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Soroban Contract (Generated)                 │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  NFT Storage          │  Value Properties           │ │   │
│  │  │  - owner: Address     │  - health: u64              │ │   │
│  │  │  - id: u64            │  - power: u64               │ │   │
│  │  │  - metadata_cid: CID  │  - level: u64               │ │   │
│  │  │                       │  (generated per prop)       │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Generated Functions (per value property)           │ │   │
│  │  │  - increment_health()  - get_health()               │ │   │
│  │  │  - decrement_health()  - set_power()                │ │   │
│  │  │  - mint() / transfer() / balance_of()               │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### What Gets Generated

For each Proprium collection, the system generates a complete Soroban contract:

#### 1. Type Definitions (`types.rs`)

```rust
use soroban_sdk::{contracttype, Address, String};

#[contracttype]
pub struct ValueProperty {
    pub default: u64,
    pub min: u64,
    pub max: u64,
    pub amount: u64,
}

#[contracttype]
pub struct Nft {
    pub owner: Address,
    pub id: u64,
    pub metadata_cid: String,  // IPFS CID from Pintheon
}

#[contracttype]
pub enum Error {
    NotOwner,
    InvalidTokenId,
    OutOfRange,
    AlreadyMinted,
}

// Generated per valProp:
{% for name in data.valProps.keys() %}
#[contracttype]
pub struct {{name | capitalize}}Prop {
    pub value: u64,
    pub token_id: u64,
}
{% endfor %}
```

#### 2. Contract Implementation (`lib.rs`)

```rust
#![no_std]
use soroban_sdk::{contract, contractimpl, Address, Env, String, Vec};

mod types;
use types::*;

#[contract]
pub struct PropriumNft;

#[contractimpl]
impl PropriumNft {
    // ============ Initialization ============

    pub fn initialize(env: Env, admin: Address, name: String, symbol: String, max_supply: u64) {
        // Store contract metadata
    }

    // ============ NFT Core ============

    pub fn mint(env: Env, to: Address, metadata_cid: String) -> Result<u64, Error> {
        to.require_auth();
        // Mint logic, initialize value properties
    }

    pub fn transfer(env: Env, from: Address, to: Address, token_id: u64) -> Result<(), Error> {
        from.require_auth();
        // Transfer logic
    }

    pub fn balance_of(env: Env, owner: Address) -> u64 {
        // Return token count
    }

    pub fn owner_of(env: Env, token_id: u64) -> Result<Address, Error> {
        // Return owner
    }

    // ============ Value Properties (Generated) ============

    {% for name, prop in data.valProps.items() %}
    {% if prop.prop_action_type in ['Incremental', 'Bicremental'] %}
    pub fn increment_{{name}}(env: Env, owner: Address, token_id: u64) -> Result<u64, Error> {
        owner.require_auth();
        let key = (token_id, "{{name}}");
        let current: u64 = env.storage().persistent().get(&key).unwrap_or({{prop.default}});
        let prop = Self::get_{{name}}_prop(env.clone());

        let new_val = current + prop.amount;
        if new_val > prop.max {
            return Err(Error::OutOfRange);
        }

        env.storage().persistent().set(&key, &new_val);
        Ok(new_val)
    }
    {% endif %}

    {% if prop.prop_action_type in ['Decremental', 'Bicremental'] %}
    pub fn decrement_{{name}}(env: Env, owner: Address, token_id: u64) -> Result<u64, Error> {
        owner.require_auth();
        let key = (token_id, "{{name}}");
        let current: u64 = env.storage().persistent().get(&key).unwrap_or({{prop.default}});
        let prop = Self::get_{{name}}_prop(env.clone());

        if current < prop.amount || current - prop.amount < prop.min {
            return Err(Error::OutOfRange);
        }

        let new_val = current - prop.amount;
        env.storage().persistent().set(&key, &new_val);
        Ok(new_val)
    }
    {% endif %}

    {% if prop.prop_action_type == 'Setter' %}
    pub fn set_{{name}}(env: Env, owner: Address, token_id: u64, value: u64) -> Result<u64, Error> {
        owner.require_auth();
        let prop = Self::get_{{name}}_prop(env.clone());

        if value < prop.min || value > prop.max {
            return Err(Error::OutOfRange);
        }

        let key = (token_id, "{{name}}");
        env.storage().persistent().set(&key, &value);
        Ok(value)
    }
    {% endif %}

    {% if prop.prop_action_type != 'Static' %}
    pub fn get_{{name}}(env: Env, token_id: u64) -> u64 {
        let key = (token_id, "{{name}}");
        env.storage().persistent().get(&key).unwrap_or({{prop.default}})
    }
    {% endif %}

    fn get_{{name}}_prop(env: Env) -> ValueProperty {
        ValueProperty {
            default: {{prop.default}},
            min: {{prop.min}},
            max: {{prop.max}},
            amount: {{prop.amount}},
        }
    }
    {% endfor %}
}
```

#### 3. Build Configuration (`Cargo.toml`)

```toml
[package]
name = "{{data.contract.name | lower | replace(' ', '_')}}"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
soroban-sdk = "20.0.0"

[dev-dependencies]
soroban-sdk = { version = "20.0.0", features = ["testutils"] }

[profile.release]
opt-level = "z"
overflow-checks = true
debug = 0
strip = "symbols"
debug-assertions = false
panic = "abort"
codegen-units = 1
lto = true
```

### API Endpoints (Phase 2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/soroban/generate` | Generate complete contract from collection data |
| POST | `/api/v1/soroban/types` | Generate only type definitions |
| POST | `/api/v1/soroban/contract` | Generate only contract implementation |
| GET | `/api/v1/soroban/templates` | List available contract templates |

### Request Example

```json
POST /api/v1/soroban/generate
{
  "collection": {
    "name": "Space Warriors",
    "symbol": "SWARS",
    "maxSupply": 10000
  },
  "valProps": {
    "health": {
      "default": 100,
      "min": 0,
      "max": 100,
      "amount": 10,
      "prop_action_type": "Bicremental"
    },
    "power": {
      "default": 50,
      "min": 0,
      "max": 200,
      "amount": 5,
      "prop_action_type": "Incremental"
    },
    "level": {
      "default": 1,
      "min": 1,
      "max": 99,
      "amount": 1,
      "prop_action_type": "Setter"
    }
  }
}
```

### Response

```json
{
  "success": true,
  "files": {
    "Cargo.toml": "...",
    "src/lib.rs": "...",
    "src/types.rs": "...",
    "src/test.rs": "..."
  },
  "build_command": "soroban contract build",
  "deploy_command": "soroban contract deploy --wasm target/wasm32-unknown-unknown/release/space_warriors.wasm --network testnet"
}
```

### Implementation Effort

| Task | Duration | Notes |
|------|----------|-------|
| Rust/Soroban templates | 1.5 days | Port Motoko templates to Rust |
| Type generation | 0.5 day | Straightforward mapping |
| Contract generation | 1 day | Value property functions |
| API endpoints | 0.5 day | Add to existing FastAPI |
| Testing | 1 day | Soroban test framework |
| **Total** | **4.5 days** | |

### Key Differences from ICP

| Aspect | ICP (Motoko) | Soroban (Rust) |
|--------|--------------|----------------|
| File storage | On-chain chunks | **Pintheon → IPFS CID** |
| Auth | Principal-based | Address + `require_auth()` |
| Storage | `stable var` + `Map` | `env.storage().persistent()` |
| Async | `async` functions | Synchronous |
| Cycles | Cycle management | No equivalent (fees in XLM) |

### Pintheon Integration

Content flow remains unchanged:
1. Creator uploads 3D asset via Pintheon
2. Pintheon pins to IPFS, returns CID
3. CID stored in Soroban contract's `metadata_cid` field
4. Content served via Pintheon's IPFS gateway

The Soroban contract never handles raw file data - only CID references.

---

## Future Enhancements

1. **WebSocket Support**: Real-time metadata updates
2. **GLTF Embedding**: Write metadata directly to GLB files
3. **Validation Service**: Validate existing HVYM metadata
4. **Batch Operations**: Generate multiple items in one request
5. **Export Formats**: JSON, YAML, TOML output options
6. **Contract Deployment**: Direct deployment via Soroban CLI integration
7. **Contract Verification**: Verify deployed contracts match generated source

---

## Timeline Estimate

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Extract data classes | 0.5 day |
| 2 | API server worker | 0.5 day |
| 3 | API routes implementation | 1 day |
| 4 | Metavinci integration | 0.5 day |
| 5 | Testing & debugging | 0.5 day |
| **Total** | | **3 days** |

---

## Conclusion

Adding local API functionality to Metavinci is a **moderate complexity** task that leverages existing patterns in the codebase. The FastAPI + QThread approach provides:

- Clean separation of concerns
- Automatic API documentation
- Type-safe request/response handling
- Non-blocking server operation
- Easy testing and debugging

The metadata generation endpoints will enable Blender addons and other tools to generate HVYM-compliant **3D asset metadata structures** without CLI dependency. This covers:

- Value properties (int, float, text)
- Materials (basic, lambert, phong, standard, PBR)
- Mesh and node references
- Animation properties
- Interactables and UI configuration

**Contract/blockchain functionality** (Stellar Soroban) will be added as a separate phase once the Proprium metadata system is ported from ICP.

---

## Appendix A: ICP/Motoko Contract System Reference

This appendix provides comprehensive documentation of the existing ICP/Motoko contract generation system in the hvym CLI. This serves as the reference implementation for porting to Stellar Soroban.

### A.1 Contract Data Class

**Location:** `heavymeta-cli-dev/hvym.py` (lines 678-722)

```python
@dataclass_json
@dataclass
class contract_data_class(base_data_class):
    """Base data class for contract data"""
    mintable: bool                  # Whether NFT is mintable
    nftType: str                    # Type: HVYC, HVYI, HVYA, HVYW, HVYO, HVYG, HVYAU
    nftChain: str                   # Blockchain: 'ICP' or 'EVM'
    nftPrice: float                 # NFT price
    premNftPrice: float             # Premium NFT price
    maxSupply: int                  # Maximum supply
    minterType: str                 # 'payable' or 'onlyOwner'
    minterName: str                 # Minter name
    minterDesc: str                 # Minter description
    minterImage: str                # Minter image path
    minterVersion: float            # Minter version
    enableContextMenus: bool        # Enable/disable context menus
    menuIndicatorsShown: bool       # Show/hide menu indicators
```

**NFT Types:**
| Type | Description |
|------|-------------|
| HVYC | Character/Avatar |
| HVYI | Item/Object |
| HVYA | Accessory |
| HVYW | Wearable |
| HVYO | Other |
| HVYG | Game Asset |
| HVYAU | Audio |

---

### A.2 Value Property System

#### Base Value Properties

```python
class int_data_class(slider_data_class):
    """Int data value property"""
    default: int       # Default value
    min: int           # Minimum value
    max: int           # Maximum value
    immutable: bool    # Cannot be edited after minting

class float_data_class(slider_data_class):
    """Float data value property"""
    default: float     # Default value
    min: float         # Minimum value
    max: float         # Maximum value
    immutable: bool    # Cannot be edited after minting
```

#### Incremental/Decremental Properties

```python
class cremental_int_data_class(int_data_class):
    """For Incremental/Decremental int properties"""
    amount: int        # Increment/decrement step size

class cremental_float_data_class(float_data_class):
    """For Incremental/Decremental float properties"""
    amount: float      # Increment/decrement step size
```

#### Behavior-Enabled Properties

```python
class int_data_behavior_class(int_data_class):
    """Int property with behaviors"""
    behaviors: list    # Associated behaviors

class cremental_int_data_behavior_class(cremental_int_data_class):
    """Incremental int with behaviors"""
    behaviors: list
```

#### Property Action Types

| Action Type | Description | Generated Functions |
|-------------|-------------|---------------------|
| Static | Read-only, cannot be modified | None (value baked in metadata) |
| Immutable | Set at mint time, cannot change | `get_` only |
| Setter | Direct value assignment | `get_`, `set_` |
| Incremental | Can only increase by fixed amount | `get_`, `increment_` |
| Decremental | Can only decrease by fixed amount | `get_`, `decrement_` |
| Bicremental | Can increase or decrease | `get_`, `increment_`, `decrement_` |

---

### A.3 Motoko Template System

**Template Location:** `heavymeta-cli-dev/templates/`
- `model_minter_backend_main_template.txt` - Main contract logic
- `model_minter_backend_types_template.txt` - Type definitions

**Template Engine:** Jinja2

```python
def _render_template(template_file, data, out_file_path):
    file_loader = FileSystemLoader(FILE_PATH / 'templates')
    env = Environment(loader=file_loader)
    template = env.get_template(template_file)

    with open(out_file_path, 'w') as f:
        output = template.render(data=data)
        f.write(output)
```

**Template Data Structure:**
```json
{
  "contract": {
    "nftName": "Collection Name",
    "nftType": "HVYC",
    "maxSupply": 1000
  },
  "valProps": {
    "health": {
      "default": 100,
      "min": 0,
      "max": 100,
      "amount": 10,
      "prop_action_type": "Bicremental"
    }
  },
  "creatorHash": "SHA256_HEX_OF_PRINCIPAL"
}
```

---

### A.4 Generated Contract Functions

#### Increment Function (Incremental/Bicremental)

```motoko
public func increment_{{name}}(user: Principal, token_id: Types.TokenId) : async ?Nat {
    let id = Nat64.toNat(token_id);
    let value = Map.get<Nat, Nat>({{name}}Props, nhash, id);
    let item = List.filter(nfts, func(token: Types.Nft) : Bool {
        token.owner == user and Nat64.toNat(token.id) == id
    });

    switch (value) {
        case (null) { return null; };
        case (?value) {
            if(value > {{name}}.max or value < {{name}}.min ){
                return null;
            }else{
                switch (item) {
                    case (null) { return null; };
                    case (?token) {
                        return Map.replace<Nat, Nat>(
                            {{name}}Props, nhash, id, value + {{name}}.amount
                        );
                    };
                };
            }
        };
    };
};
```

#### Decrement Function (Decremental/Bicremental)

```motoko
public func decrement_{{name}}(user: Principal, token_id: Types.TokenId) : async ?Nat {
    let id = Nat64.toNat(token_id);
    let value = Map.get<Nat, Nat>({{name}}Props, nhash, id);
    let item = List.filter(nfts, func(token: Types.Nft) : Bool {
        token.owner == user and Nat64.toNat(token.id) == id
    });

    switch (value) {
        case (null) { return null; };
        case (?value) {
            if(value > {{name}}.max or value < {{name}}.min ){
                return null;
            }else{
                switch (item) {
                    case (null) { return null; };
                    case (?token) {
                        return Map.replace<Nat, Nat>(
                            {{name}}Props, nhash, id, value - {{name}}.amount
                        );
                    };
                };
            }
        };
    };
};
```

#### Setter Function

```motoko
public func set_{{name}}(user: Principal, token_id: Types.TokenId, num : Nat) : async ?Nat {
    let id = Nat64.toNat(token_id);
    let value = Map.get<Nat, Nat>({{name}}Props, nhash, id);
    let item = List.filter(nfts, func(token: Types.Nft) : Bool {
        token.owner == user and Nat64.toNat(token.id) == id
    });

    switch (num) {
        case (null) { return null; };
        case (?num) {
            if(num > {{name}}.max or num < {{name}}.min ){
                return null;
            }else{
                switch (item) {
                    case (null) { return null; };
                    case (?token) {
                        return Map.replace<Nat, Nat>({{name}}Props, nhash, id, num);
                    };
                };
            }
        };
    };
};
```

#### Getter Query Function

```motoko
public query func get_{{name}}(user: Principal, token_id: Types.TokenId) : async ?Nat {
    let item = List.filter(nfts, func(token: Types.Nft) : Bool {
        token.owner == user and token.id == token_id
    });

    switch (item) {
        case (null) { return null; };
        case (?token) {
            return Map.get<Nat, Nat>({{name}}Props, nhash, Nat64.toNat(token_id));
        };
    };
};
```

---

### A.5 ICP-Specific Patterns

#### Principal Management

```motoko
import Principal "mo:base/Principal";

// Null address (non-existent principal)
let null_address : Principal = Principal.fromText("aaaaa-aa");

// Anonymous principal (unauthenticated)
let anonymous = Principal.fromText("2vxsx-fae");

// Authentication check
if (Principal.equal(caller, anonymous)){
    return #Err(#Unauthorized);
};
```

#### Creator Authentication via Hash

```motoko
stable var creator : Text = "{{data.creatorHash}}";

public shared func release(user: Principal) : async Types.Released {
    if (Principal.equal(user, anonymous)){ return false; };

    let hex = Hex.encode(
        SHA256.sha256(
            Blob.toArray(Text.encodeUtf8(Principal.toText(user)))
        ),
        #upper
    );

    if (hex != creator) {
        return false;
    } else if(hex == creator and released == false){
        custodians := List.push(user, custodians);
    };

    released := true;
    return released;
};
```

#### Custodian Pattern

```motoko
stable var custodians = List.nil<Principal>();

func isCustodian(caller: Principal) : Bool {
    List.some(custodians, func (custodian : Principal) : Bool {
        custodian == caller
    })
};
```

#### Cycles Management

```motoko
import Cycles "mo:base/ExperimentalCycles";

let limit = 20_000_000_000_000;  // 20 trillion cycles

public func wallet_receive() : async { accepted: Nat64 } {
    let available = Cycles.available();
    let accepted = Cycles.accept(Nat.min(available, limit));
    { accepted = Nat64.fromNat(accepted) };
};

public func wallet_balance() : async Nat {
    return Cycles.balance();
};
```

#### Stable Storage

```motoko
stable var nfts = List.nil<Types.Nft>();
stable var transactionId: Types.TransactionId = 0;
stable var {{name}}Props = Map.new<Nat, Types.{{name}}>();
stable var custodians = List.nil<Principal>();
stable var released: Types.Released = false;
```

---

### A.6 File Chunking System

The ICP contract implements chunked file upload for large 3D assets:

#### Chunk ID Generation
```motoko
func chunkId(fileId : FileId, chunkNum : Nat) : ChunkId {
    fileId # (Nat.toText(chunkNum))
};
```

#### File Registration
```motoko
public shared({ caller }) func putFile(fi: FileInfo) : async ?FileId {
    if (Principal.equal(caller, anonymous)){ return null; };
    do ? {
        let fileId = await generateRandom(fi.name);
        createFileInfo(fileId, fi)!;
    }
};
```

#### Chunk Storage
```motoko
public shared({ caller }) func putChunks(
    fileId : FileId,
    chunkNum : Nat,
    chunkData : Blob
) : async ?() {
    if (Principal.equal(caller, anonymous)){ return null; };
    do ? {
        state.chunks.put(chunkId(fileId, chunkNum), chunkData);
    }
};
```

#### Chunk Retrieval
```motoko
public query func getChunks(fileId : FileId, chunkNum: Nat) : async ?Blob {
    state.chunks.get(chunkId(fileId, chunkNum))
};
```

**File Metadata Structure:**
```motoko
public type FileInfo = {
    name: Text;
    createdAt: Time;
    chunkCount: Nat;
    size: Nat;
    extension: Text;
};
```

> **Soroban Note:** File chunking is NOT needed for Soroban. Content will be stored on IPFS via Pintheon, with only the CID reference stored in the contract.

---

### A.7 Core NFT Functions

#### Minting

```motoko
public shared({ caller }) func mint(
    to: Principal,
    imgId: Uploader.FileId,
    metadata: Types.MetadataDesc
) : async Types.MintReceipt {
    if (Principal.equal(caller, anonymous)){
        return #Err(#Unauthorized);
    };

    let newId = Nat64.fromNat(List.size(nfts));
    let nft : Types.Nft = {
        owner = to;
        id = newId;
        imageId = imgId;
        metadata = metadata;
    };

    nfts := List.push(nft, nfts);

    // Initialize all value properties at default
    Map.set({{name}}Props, nhash, transactionId, {{name}}.default);

    transactionId += 1;

    return #Ok({
        token_id = newId;
        id = transactionId;
    });
};
```

#### Transfer

```motoko
public shared({ caller }) func safeTransferFrom(
    from: Principal,
    to: Principal,
    token_id: Types.TokenId
) : async Types.TxReceipt {
    if (to == null_address) {
        return #Err(#ZeroAddress);
    } else {
        return transferFrom(from, to, token_id, caller);
    };
};

func transferFrom(
    from: Principal,
    to: Principal,
    token_id: Types.TokenId,
    caller: Principal
) : Types.TxReceipt {
    let item = List.find(nfts, func(token: Types.Nft) : Bool {
        token.id == token_id
    });
    switch (item) {
        case null { return #Err(#InvalidTokenId); };
        case (?token) {
            if (caller != token.owner and not isCustodian(caller)) {
                return #Err(#Unauthorized);
            } else if (Principal.notEqual(from, token.owner)) {
                return #Err(#Other);
            } else {
                nfts := List.map(nfts, func (item : Types.Nft) : Types.Nft {
                    if (item.id == token.id) {
                        { owner = to; id = item.id; imageId = item.imageId; metadata = token.metadata; }
                    } else { item };
                });
                transactionId += 1;
                return #Ok(transactionId);
            };
        };
    };
};
```

#### Balance & Ownership Queries

```motoko
public query func balanceOf(user: Principal) : async Nat64 {
    return Nat64.fromNat(
        List.size(
            List.filter(nfts, func(token: Types.Nft) : Bool { token.owner == user })
        )
    );
};

public query func ownerOf(token_id: Types.TokenId) : async Types.OwnerResult {
    let item = List.find(nfts, func(token: Types.Nft) : Bool { token.id == token_id });
    switch (item) {
        case (null) { return #Err(#InvalidTokenId); };
        case (?token) { return #Ok(token.owner); };
    };
};

public query func totalSupply() : async Nat64 {
    return Nat64.fromNat(List.size(nfts));
};
```

---

### A.8 Type Definitions

```motoko
public type HVYM_721_NFT = {
    logo: LogoResult;
    name: Text;
    symbol: Text;
    maxLimit : Nat16;
};

public type Nft = {
    owner: Principal;
    id: TokenId;
    imageId: ImageId;
    metadata: MetadataDesc;
};

public type TokenId = Nat64;
public type ImageId = Uploader.FileId;
public type TransactionId = Nat;
public type Released = Bool;

public type ValueProperty = {
    default: Nat;
    min: Nat;
    max: Nat;
    amount: Nat;
};

public type ApiError = {
    #Unauthorized;
    #InvalidTokenId;
    #ZeroAddress;
    #Other;
};

public type Result<S, E> = {
    #Ok : S;
    #Err : E;
};

public type MetadataVal = {
    #TextContent : Text;
    #BlobContent : Blob;
    #NatContent : Nat;
    #Nat8Content: Nat8;
    #Nat16Content: Nat16;
    #Nat32Content: Nat32;
    #Nat64Content: Nat64;
};
```

---

### A.9 Data Flow: GLB to Contract

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Blender Export                                               │
│     └─ GLB file with HVYM_nft_data extension                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. _load_hvym_data()                                            │
│     └─ Extract HVYM_nft_data JSON from GLB extensions           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. _build_template_data()                                       │
│     ├─ Parse contract configuration                              │
│     ├─ Extract mutable value properties                          │
│     └─ Generate creator hash from principal                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. _render_template() (Jinja2)                                  │
│     ├─ Generate main.mo from main_template.txt                   │
│     └─ Generate Types.mo from types_template.txt                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. dfx build                                                    │
│     └─ Compile Motoko to WASM                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. dfx deploy                                                   │
│     └─ Deploy canister to ICP network                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. Canister Running                                             │
│     └─ Ready for minting, transfers, property mutations          │
└─────────────────────────────────────────────────────────────────┘
```

---

### A.10 ICP to Soroban Mapping

| ICP Concept | Soroban Equivalent |
|-------------|-------------------|
| Principal | Address |
| Canister | Contract |
| Cycles | XLM (fees paid by invoker) |
| `stable var` | `env.storage().persistent()` |
| `shared({ caller })` | `env: Env` + `address.require_auth()` |
| `async` functions | Synchronous functions |
| List/Map (mo:base) | soroban_sdk::Map/Vec |
| `#Ok/#Err` variants | `Result<T, Error>` |
| File chunking (on-chain) | IPFS CID reference (off-chain via Pintheon) |
| `query func` | No equivalent (all reads cost fees) |
| Candid (.did) | Contract traits/ABI |

---

### A.11 Security Patterns Summary

| Pattern | ICP Implementation | Soroban Equivalent |
|---------|-------------------|-------------------|
| Anonymous check | `Principal.equal(caller, anonymous)` | Check against zero address |
| Owner verification | `token.owner == user` | `token.owner == address` |
| Custodian list | `List<Principal>` with `List.some()` | `Vec<Address>` with iteration |
| Creator hash | SHA256 of principal text | SHA256 of address bytes |
| Range validation | `value > max or value < min` | Same logic |
| Null address | `"aaaaa-aa"` principal | Soroban zero address |

---

### A.12 Key Implementation Notes for Soroban Port

1. **No File Chunking Needed:** Soroban contracts store only the IPFS CID from Pintheon, not raw file data.

2. **Authentication Pattern Change:** ICP uses `shared({ caller })` to capture caller; Soroban uses `address.require_auth()`.

3. **Storage Model:** ICP stable variables auto-persist; Soroban requires explicit `env.storage().persistent().set()`.

4. **No Free Queries:** ICP query functions are free; all Soroban calls consume fees.

5. **Error Handling:** ICP uses variant types (`#Ok/#Err`); Soroban uses Rust's `Result<T, E>`.

6. **Type System:** Motoko is garbage-collected with null safety; Rust/Soroban is ownership-based with explicit memory management.

7. **Deployment:** ICP uses `dfx deploy`; Soroban uses `soroban contract deploy --wasm`.

8. **Principal → Address:** ICP principals are text-encoded; Soroban addresses are 32-byte identifiers.

---

*This appendix documents the ICP/Motoko implementation as of 2026-01-19 for reference during the Soroban port.*
