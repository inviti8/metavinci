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
- [ ] Create `templates/soroban/` directory
- [ ] Create `types.rs.j2` template
- [ ] Create `lib.rs.j2` template
- [ ] Create `Cargo.toml.j2` template
- [ ] Create `test.rs.j2` template
- [ ] Add Jinja2 to dependencies (if not present)

#### 2.2 Contract Generator Module (`soroban_generator.py`)
- [ ] Template loader function
- [ ] Type generation function
- [ ] Contract generation function
- [ ] Full project generation function
- [ ] Validation for input data

#### 2.3 Soroban API Routes
- [ ] `/api/v1/soroban/generate` - Full contract
- [ ] `/api/v1/soroban/types` - Types only
- [ ] `/api/v1/soroban/contract` - Implementation only
- [ ] `/api/v1/soroban/templates` - List templates

#### 2.4 Value Property Generation
- [ ] Incremental function template
- [ ] Decremental function template
- [ ] Bicremental function template
- [ ] Setter function template
- [ ] Getter function template
- [ ] Property config function template

#### 2.5 NFT Core Functions
- [ ] `initialize()` template
- [ ] `mint()` template
- [ ] `transfer()` template
- [ ] `balance_of()` template
- [ ] `owner_of()` template

#### 2.6 Testing
- [ ] Unit tests for template rendering
- [ ] Test generated contract compiles
- [ ] Test generated contract deploys to testnet
- [ ] Verify value property functions work correctly

---

### Documentation & Cleanup
- [ ] Update README with API documentation
- [ ] Add example requests/responses
- [ ] Document configuration options
- [ ] Clean up any unused code

---

*Last updated: 2026-01-19*

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

---

## File Structure (New Files)

```
metavinci/
├── metavinci.py          # Modified - API server integration
├── hvym_metadata.py      # NEW - Data classes
├── api_server.py         # NEW - Server worker thread
├── api_routes.py         # NEW - FastAPI routes
└── requirements.txt      # Modified - new dependencies
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
