# HVYM Tunnel — Metavinci Integration Plan

## Overview

Replace the single Pinggy "Open Tunnel" action with a dual-provider **Open Tunnel** submenu offering:

- **Native** — HVYM Tunnler (`tunnel_client.py` / `tunnel_worker.py` / `tunnel_config.py`), using Stellar JWT authentication. Default server: `tunnel.hvym.link`. Supports connecting to **any** HVYM Tunnler instance via a custom server URL field.
- **Pinggy** — The existing third-party Pinggy tunnel, kept as a fallback

Both providers expose the local Pintheon gateway to the internet. Only one tunnel may be active at a time.

### Multi-Server Support

Multiple HVYM Tunnler instances may be deployed (e.g. regional servers, private instances). The default is `wss://tunnel.hvym.link/connect` but users can point to any compatible server via **Native Tunnel Settings**. When the server URL changes, the server's Stellar address is auto-discovered via the `/info` endpoint, so no manual address entry is needed in the typical case.

---

## Architecture

```
Metavinci (PyQt5 tray app)
├── Pintheon Gateway (Docker)
│   └── Kubo daemon @ localhost:5001
│   └── Flask gateway @ https://localhost:9998
│
├── Open Tunnel
│   ├── Native (HVYM Tunnler)          ← NEW
│   │   ├── TunnelManager (QObject)
│   │   │   └── TunnelWorker (QThread)
│   │   │       └── HVYMTunnelClient (async WebSocket)
│   │   │           └── wss://tunnel.hvym.link/connect
│   │   └── TunnelConfigStore (TinyDB)
│   │
│   └── Pinggy (existing)
│       └── subprocess.Popen → pinggy binary in terminal
│
├── Pinwheel (QThread worker)
├── Metadata API (FastAPI :7777)
└── Wallet Manager (TinyDB)
```

---

## Current State

### What exists but is **not wired in**

| File | Purpose | Status |
|------|---------|--------|
| `tunnel_client.py` | Async WebSocket client with Stellar JWT auth | Complete, unused |
| `tunnel_worker.py` | `TunnelWorker` (QThread) + `TunnelManager` (QObject) | Complete, unused |
| `tunnel_config.py` | `TunnelConfigStore` for TinyDB persistence | Complete, unused |

### What is **currently active** in the UI

All tunnel functionality runs through Pinggy:

| Component | Location | Purpose |
|-----------|----------|---------|
| `self.open_tunnel_action` | Action (line ~1669) | "Open Tunnel" — calls `_open_tunnel` |
| `self.set_tunnel_token_action` | Action (line ~1673) | "Set Pinggy Token" |
| `self.set_tunnel_tier_action` | Action (line ~1677) | "Set Pinggy Tier" |
| `_open_tunnel_direct()` | Method (line ~3634) | Launches Pinggy binary in terminal |
| `_set_tunnel_token_direct()` | Method (line ~3689) | Dialog for Pinggy token |
| `_set_tunnel_tier_direct()` | Method (line ~3712) | Dialog for Pinggy tier |
| `_get_pinggy_path()` | Method (line ~3615) | Platform-specific Pinggy binary path |
| `_is_tunnel_open()` | Method (line ~3626) | Checks `localhost:4300` (Pinggy debug port) |
| `self.TUNNEL_TOKEN` | Instance var | Pinggy auth token |
| `self.PINGGY_TIER` | Instance var | `'free'` or `'pro'` |
| `PintheonSetupWorker._install_pinggy()` | Worker method | Downloads Pinggy binary from S3 |

Menu location: **Tools → Pintheon → Open Tunnel** (single action)

Settings location: **Tools → Pintheon → Settings → Set Pinggy Token / Set Pinggy Tier**

---

## Prerequisites

### Import fix in `tunnel_worker.py`

`tunnel_worker.py` uses a relative import that will fail outside a package:

```python
# Line 21 — CURRENT (broken for standalone import)
from .tunnel_client import HVYMTunnelClient, TunnelConfig, TunnelState, TunnelEndpoint
```

Change to:

```python
# FIXED — works as standalone module
from tunnel_client import HVYMTunnelClient, TunnelConfig, TunnelState, TunnelEndpoint
```

### Dependency: `websockets`

`tunnel_client.py` requires the `websockets` package. Add to `requirements.txt`:

```
websockets>=12.0
```

Already present: `hvym-stellar`, `httpx`, `stellar-sdk`.

---

## Phase 1: Import Block + Optional Dependencies

### New file imports in `metavinci.py`

Add after the Pinwheel import block:

```python
# Try to import HVYM tunnel client
try:
    from tunnel_worker import TunnelWorker, TunnelManager
    from tunnel_client import TunnelState
    from tunnel_config import TunnelConfigStore
    HAS_HVYM_TUNNEL = True
except ImportError:
    HAS_HVYM_TUNNEL = False
    TunnelWorker = None
    TunnelManager = None
    TunnelConfigStore = None
```

---

## Phase 2: Instance Variables

Add to `__init__`, after the Pinwheel instance variables:

```python
# HVYM Tunnel
self.tunnel_manager = None
self.tunnel_config_store = None
self.HVYM_TUNNEL_ACTIVE = False
self.HVYM_TUNNEL_ENDPOINT = ''  # Public URL when connected

if HAS_HVYM_TUNNEL:
    self.tunnel_config_store = TunnelConfigStore(self.DB)
```

Existing Pinggy variables remain unchanged:

```python
self.TUNNEL_TOKEN = ''
self.PINGGY_TIER = 'free'
```

---

## Phase 3: Menu Restructure

### Current layout (single action)

```
Pintheon testnet
├── Settings
│   ├── Set Pinggy Token
│   └── Set Pinggy Tier
├── Start Pintheon
├── Stop Pintheon
├── Open Tunnel              ← single action, Pinggy only
└── Interface
    ├── Open Admin
    └── Open Homepage
```

### New layout (submenu with two providers)

```
Pintheon testnet
├── Settings
│   ├── Set Pinggy Token
│   └── Set Pinggy Tier
│   ├── ─────────
│   └── Native Tunnel Settings...
├── Start Pintheon
├── Stop Pintheon
├── Open Tunnel              ← submenu (replaces single action)
│   ├── Status: Disconnected
│   ├── ─────────
│   ├── Native (HVYM)
│   │   ├── Connect
│   │   ├── Disconnect       (visible when connected)
│   │   ├── Server: tunnel.hvym.link
│   │   └── Endpoint: https://GADDR...tunnel.hvym.link
│   ├── Pinggy
│   │   └── Open Pinggy Tunnel
│   ├── ─────────
│   └── Copy Endpoint URL    (visible when any tunnel is connected)
└── Interface
    ├── Open Admin
    └── Open Homepage
```

### 3a. Replace the existing `open_tunnel_action` definition

Currently (line ~1669):

```python
self.open_tunnel_action = QAction(self.tunnel_icon, "Open Tunnel", self)
self.open_tunnel_action.triggered.connect(self._open_tunnel)
self.open_tunnel_action.setVisible(self.PINTHEON_ACTIVE)
```

Remove this single action and replace it with action definitions for the new submenu items. These are defined here but added to the menu in `_setup_pintheon_menu`:

```python
# --- Native (HVYM) tunnel actions ---
self.hvym_tunnel_connect_action = QAction(self.tunnel_icon, "Connect", self)
self.hvym_tunnel_connect_action.triggered.connect(self._start_hvym_tunnel)

self.hvym_tunnel_disconnect_action = QAction(self.tunnel_icon, "Disconnect", self)
self.hvym_tunnel_disconnect_action.triggered.connect(self._stop_hvym_tunnel)
self.hvym_tunnel_disconnect_action.setVisible(False)

self.hvym_tunnel_server_action = QAction("Server: tunnel.hvym.link", self)
self.hvym_tunnel_server_action.setEnabled(False)

self.hvym_tunnel_endpoint_action = QAction("Endpoint: --", self)
self.hvym_tunnel_endpoint_action.setEnabled(False)
self.hvym_tunnel_endpoint_action.setVisible(False)

# --- Pinggy tunnel action ---
self.pinggy_tunnel_action = QAction(self.tunnel_icon, "Open Pinggy Tunnel", self)
self.pinggy_tunnel_action.triggered.connect(self._open_tunnel)

# --- Shared tunnel actions ---
self.tunnel_status_action = QAction("Status: Disconnected", self)
self.tunnel_status_action.setEnabled(False)

self.tunnel_copy_endpoint_action = QAction("Copy Endpoint URL", self)
self.tunnel_copy_endpoint_action.triggered.connect(self._copy_tunnel_endpoint)
self.tunnel_copy_endpoint_action.setVisible(False)
```

### 3b. Build the Open Tunnel submenu in `_setup_pintheon_menu`

Replace the current `self.tray_pintheon_menu.addAction(self.open_tunnel_action)` line with the new submenu construction:

```python
# Replace:
#   self.tray_pintheon_menu.addAction(self.open_tunnel_action)
# With:

self.open_tunnel_menu = self.tray_pintheon_menu.addMenu("Open Tunnel")
self.open_tunnel_menu.setIcon(self.tunnel_icon)

# Status line
self.open_tunnel_menu.addAction(self.tunnel_status_action)
self.open_tunnel_menu.addSeparator()

# Native (HVYM) submenu
if HAS_HVYM_TUNNEL:
    self.native_tunnel_menu = self.open_tunnel_menu.addMenu("Native (HVYM)")
    self.native_tunnel_menu.setIcon(self.tunnel_icon)
    self.native_tunnel_menu.addAction(self.hvym_tunnel_connect_action)
    self.native_tunnel_menu.addAction(self.hvym_tunnel_disconnect_action)
    self.native_tunnel_menu.addAction(self.hvym_tunnel_server_action)
    self.native_tunnel_menu.addAction(self.hvym_tunnel_endpoint_action)

    # Show configured server in menu
    if self.tunnel_config_store:
        url = self.tunnel_config_store.server_url
        # Extract domain from wss://domain/connect
        domain = url.split("://")[1].split("/")[0] if "://" in url else url
        self.hvym_tunnel_server_action.setText(f"Server: {domain}")

# Pinggy submenu
self.pinggy_tunnel_menu = self.open_tunnel_menu.addMenu("Pinggy")
self.pinggy_tunnel_menu.setIcon(self.tunnel_icon)
self.pinggy_tunnel_menu.addAction(self.pinggy_tunnel_action)

self.open_tunnel_menu.addSeparator()

# Copy endpoint (visible when any tunnel is connected)
self.open_tunnel_menu.addAction(self.tunnel_copy_endpoint_action)
```

### 3c. Add Native Tunnel settings to Pintheon Settings submenu

In `_setup_pintheon_menu`, after the existing Pinggy settings entries:

```python
self.pintheon_settings_menu.addAction(self.set_tunnel_token_action)
self.pintheon_settings_menu.addAction(self.set_tunnel_tier_action)

# Native tunnel settings (new)
if HAS_HVYM_TUNNEL:
    self.pintheon_settings_menu.addSeparator()
    self.native_tunnel_settings_action = QAction(self.cog_icon, "Native Tunnel Settings...", self)
    self.native_tunnel_settings_action.triggered.connect(self._show_hvym_tunnel_settings)
    self.pintheon_settings_menu.addAction(self.native_tunnel_settings_action)
```

### 3d. Update visibility logic

The current `_refresh_pintheon_ui_state` toggles `self.open_tunnel_action.setVisible(...)`.

Replace that with:

```python
# Replace:
#   self.open_tunnel_action.setVisible(self.PINTHEON_ACTIVE and len(self.TUNNEL_TOKEN) >= 7)
# With:
if hasattr(self, 'open_tunnel_menu'):
    self.open_tunnel_menu.setEnabled(self.PINTHEON_ACTIVE)
```

The "Open Tunnel" submenu should always be visible when Pintheon is installed, but disabled when Pintheon is not running. The individual providers handle their own precondition checks (Pinggy checks for token, Native checks for wallet).

Similarly, in `_update_ui_on_pintheon_started`:

```python
# Replace:
#   self.open_tunnel_action.setVisible(len(self.TUNNEL_TOKEN) >= 7)
# With:
if hasattr(self, 'open_tunnel_menu'):
    self.open_tunnel_menu.setEnabled(True)
```

And in `_update_ui_on_pintheon_stopped`:

```python
# Replace:
#   self.open_tunnel_action.setVisible(False)
# With:
if hasattr(self, 'open_tunnel_menu'):
    self.open_tunnel_menu.setEnabled(False)
```

---

## Phase 4: Native Tunnel Lifecycle Methods

```python
# =========================================================================
# HVYM Native Tunnel Methods
# =========================================================================

def _start_hvym_tunnel(self):
    """Start the native HVYM tunnel."""
    if not HAS_HVYM_TUNNEL:
        self.open_msg_dialog('HVYM tunnel client not available.\n'
                             'Ensure tunnel_client.py, tunnel_worker.py, '
                             'and tunnel_config.py are present.')
        return

    if not self.PINTHEON_ACTIVE:
        self.open_msg_dialog('Pintheon must be running before opening a tunnel.')
        return

    if self.HVYM_TUNNEL_ACTIVE:
        self.open_msg_dialog('Native tunnel is already connected.')
        return

    # Need a wallet for Stellar JWT authentication
    wallet_keypair = self._get_hvym_tunnel_wallet()
    if not wallet_keypair:
        return

    # Build config from TunnelConfigStore
    config = self.tunnel_config_store.to_tunnel_config()

    if not config.server_address:
        # Try fetching server address from /info endpoint
        server_address = self._fetch_tunnel_server_address(config.server_url)
        if server_address:
            self.tunnel_config_store.server_address = server_address
            config.server_address = server_address
        else:
            self.open_msg_dialog('Tunnel server address not configured.\n'
                                 'Open Native Tunnel Settings to configure.')
            return

    # Set the local Pintheon port
    config.local_pintheon_port = getattr(self, 'PINTHEON_PORT', 9998)

    # Create TunnelManager and start
    self.tunnel_manager = TunnelManager(self)
    self.tunnel_manager.set_wallet(wallet_keypair)
    self.tunnel_manager.set_server(config.server_url, config.server_address)
    self.tunnel_manager.add_port_binding("pintheon", config.local_pintheon_port)

    # Connect signals
    self.tunnel_manager.state_changed.connect(self._on_hvym_tunnel_state_changed)
    self.tunnel_manager.connected.connect(self._on_hvym_tunnel_connected)
    self.tunnel_manager.disconnected.connect(self._on_hvym_tunnel_disconnected)
    self.tunnel_manager.error.connect(self._on_hvym_tunnel_error)

    if not self.tunnel_manager.start_tunnel():
        self.open_msg_dialog('Failed to start native tunnel. Check logs.')
        return

    self.tunnel_status_action.setText("Status: Connecting...")
    logging.info("Starting HVYM native tunnel")


def _stop_hvym_tunnel(self):
    """Stop the native HVYM tunnel."""
    if self.tunnel_manager:
        self.tunnel_manager.stop_tunnel()
        self.tunnel_manager = None
        logging.info("HVYM native tunnel stopped")


def _on_hvym_tunnel_state_changed(self, state_str: str):
    """Handle tunnel state change signal."""
    display_state = state_str.replace('_', ' ').title()
    self.tunnel_status_action.setText(f"Status: {display_state}")
    logging.info(f"HVYM tunnel state: {state_str}")


def _on_hvym_tunnel_connected(self, endpoint_url: str):
    """Handle native tunnel connected signal."""
    self.HVYM_TUNNEL_ACTIVE = True
    self.HVYM_TUNNEL_ENDPOINT = endpoint_url

    # Update UI
    self.tunnel_status_action.setText("Status: Connected (Native)")
    self.hvym_tunnel_connect_action.setVisible(False)
    self.hvym_tunnel_disconnect_action.setVisible(True)
    self.hvym_tunnel_endpoint_action.setText(f"Endpoint: {endpoint_url}")
    self.hvym_tunnel_endpoint_action.setVisible(True)
    self.tunnel_copy_endpoint_action.setVisible(True)

    # Persist last endpoint
    if self.tunnel_config_store:
        self.tunnel_config_store.set_last_endpoint(endpoint_url)

    logging.info(f"HVYM tunnel connected: {endpoint_url}")
    self.tray_icon.showMessage(
        "HVYM Tunnel",
        f"Connected: {endpoint_url}",
        QSystemTrayIcon.Information,
        5000
    )


def _on_hvym_tunnel_disconnected(self):
    """Handle native tunnel disconnected signal."""
    self.HVYM_TUNNEL_ACTIVE = False
    self.HVYM_TUNNEL_ENDPOINT = ''

    # Update UI
    self.tunnel_status_action.setText("Status: Disconnected")
    self.hvym_tunnel_connect_action.setVisible(True)
    self.hvym_tunnel_disconnect_action.setVisible(False)
    self.hvym_tunnel_endpoint_action.setVisible(False)
    self.tunnel_copy_endpoint_action.setVisible(False)

    if self.tunnel_config_store:
        self.tunnel_config_store.clear_last_endpoint()


def _on_hvym_tunnel_error(self, error: str):
    """Handle native tunnel error signal."""
    logging.error(f"HVYM tunnel error: {error}")
    self.tunnel_status_action.setText("Status: Error")
    QMessageBox.warning(self, "HVYM Tunnel Error",
                        f"Native tunnel error:\n{error}")
```

---

## Phase 5: Wallet Integration for Native Tunnel

The native tunnel authenticates via Stellar JWT. It needs a `Stellar25519KeyPair` from `hvym_stellar`.

```python
def _get_hvym_tunnel_wallet(self):
    """Get a Stellar25519KeyPair for tunnel authentication.

    Uses the same wallet selection strategy as Pinwheel:
    1. Check TinyDB for a stored tunnel wallet address
    2. If none, show wallet selection dialog
    3. Build Stellar25519KeyPair from the secret key

    Returns:
        Stellar25519KeyPair or None if cancelled/unavailable
    """
    if not HAS_STELLAR_SDK or not HAS_WALLET_MANAGER:
        self.open_msg_dialog('Stellar SDK and Wallet Manager are required '
                             'for native tunnel authentication.')
        return None

    # Check for stored tunnel wallet preference
    tunnel_wallet_addr = ''
    try:
        result = self.DB.search(self.QUERY.type == 'app_data')
        if result and 'tunnel_wallet' in result[0]:
            tunnel_wallet_addr = result[0]['tunnel_wallet']
    except Exception:
        pass

    # If no stored preference, prompt user
    if not tunnel_wallet_addr:
        wm = WalletManager()
        wallets = wm.list_wallets(network=self.PINTHEON_NETWORK)
        if not wallets:
            self.open_msg_dialog(f'No {self.PINTHEON_NETWORK} wallets found.\n'
                                 'Create a wallet first via Wallet Management.')
            return None

        labels = [f"{w.label} ({w.address[:8]}...{w.address[-4:]})" for w in wallets]
        choice, ok = QInputDialog.getItem(
            self, "Select Tunnel Wallet",
            "Choose a wallet for HVYM tunnel authentication:",
            labels, 0, False
        )
        if not ok or not choice:
            return None

        idx = labels.index(choice)
        tunnel_wallet_addr = wallets[idx].address
        self.DB.update({'tunnel_wallet': tunnel_wallet_addr},
                       self.QUERY.type == 'app_data')

    # Get secret key
    wm = WalletManager()
    try:
        wallet = wm.get_wallet(tunnel_wallet_addr)
    except Exception:
        self.open_msg_dialog('Stored tunnel wallet not found. Please re-select.')
        self.DB.update({'tunnel_wallet': ''}, self.QUERY.type == 'app_data')
        return None

    if wallet.encrypted:
        password, ok = QInputDialog.getText(
            self, "Wallet Password",
            f"Enter password for wallet {wallet.label}:",
            QLineEdit.Password
        )
        if not ok or not password:
            return None
        try:
            secret = wm.get_secret_key(wallet.address, password)
        except Exception:
            self.open_msg_dialog('Invalid password.')
            return None
    else:
        secret = wallet.secret_key

    # Build Stellar25519KeyPair
    try:
        from stellar_sdk import Keypair
        kp = Keypair.from_secret(secret)
        return Stellar25519KeyPair(kp)
    except Exception as e:
        self.open_msg_dialog(f'Failed to create keypair: {e}')
        return None
```

---

## Phase 6: Server Address Discovery

The native tunnel needs the server's Stellar address for JWT audience. This can be fetched automatically from the server's `/info` endpoint:

```python
def _fetch_tunnel_server_address(self, server_ws_url: str) -> str:
    """Fetch the tunnel server's Stellar address from its /info endpoint.

    Converts wss://tunnel.hvym.link/connect → https://tunnel.hvym.link/info

    Returns:
        Server Stellar address string, or empty string on failure.
    """
    try:
        # Convert WebSocket URL to HTTP info endpoint
        info_url = server_ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
        info_url = info_url.rsplit('/connect', 1)[0] + '/info'

        response = requests.get(info_url, timeout=10, verify=True)
        response.raise_for_status()
        data = response.json()
        server_address = data.get('server_address', '')
        if server_address:
            logging.info(f"Fetched tunnel server address: {server_address}")
        return server_address
    except Exception as e:
        logging.warning(f"Failed to fetch tunnel server info: {e}")
        return ''
```

---

## Phase 7: Settings Dialog

Supports connecting to any HVYM Tunnler instance. The default is `wss://tunnel.hvym.link/connect` but users can enter the URL of any compatible server (regional, private, self-hosted).

```python
def _show_hvym_tunnel_settings(self):
    """Show dialog for native tunnel configuration.

    Allows the user to point to any HVYM Tunnler server.
    Default: wss://tunnel.hvym.link/connect
    """
    if not self.tunnel_config_store:
        self.open_msg_dialog('Native tunnel not available.')
        return

    config = self.tunnel_config_store.get_config()

    # Server URL — custom tunnel server support
    server_url, ok = QInputDialog.getText(
        self, "Native Tunnel Settings",
        "Tunnel server URL:\n"
        "(default: wss://tunnel.hvym.link/connect)\n\n"
        "Enter the WebSocket URL of any HVYM Tunnler server:",
        text=config.get('server_url', TunnelConfigStore.DEFAULT_SERVER_URL)
    )
    if not ok:
        return

    server_url = server_url.strip()
    self.tunnel_config_store.server_url = server_url

    # Try to auto-discover server address via /info endpoint
    server_address = self._fetch_tunnel_server_address(server_url)
    if server_address:
        self.tunnel_config_store.server_address = server_address
        # Update server display in menu
        domain = server_url.split("://")[1].split("/")[0] if "://" in server_url else server_url
        self.hvym_tunnel_server_action.setText(f"Server: {domain}")
        self.open_msg_dialog(f'Server configured.\n'
                             f'URL: {server_url}\n'
                             f'Address: {server_address}')
    else:
        # Manual entry fallback (server may be offline or non-standard)
        addr, ok2 = QInputDialog.getText(
            self, "Server Stellar Address",
            "Could not auto-detect server address.\n"
            "Enter the tunnel server's Stellar address (G...):",
            text=config.get('server_address', '')
        )
        if ok2 and addr:
            self.tunnel_config_store.server_address = addr.strip()
            domain = server_url.split("://")[1].split("/")[0] if "://" in server_url else server_url
            self.hvym_tunnel_server_action.setText(f"Server: {domain}")
            self.open_msg_dialog(f'Server configured.\n'
                                 f'URL: {server_url}\n'
                                 f'Address: {addr.strip()}')
```

---

## Phase 8: Shared Utilities

```python
def _copy_tunnel_endpoint(self):
    """Copy the active tunnel endpoint URL to clipboard."""
    endpoint = ''
    if self.HVYM_TUNNEL_ACTIVE:
        endpoint = self.HVVM_TUNNEL_ENDPOINT
    else:
        # Pinggy doesn't provide a programmatic endpoint URL,
        # but if we tracked it, use that
        pass

    if endpoint:
        import pyperclip
        pyperclip.copy(endpoint)
        self.tray_icon.showMessage("Tunnel", "Endpoint URL copied to clipboard",
                                   QSystemTrayIcon.Information, 3000)
    else:
        self.open_msg_dialog('No tunnel endpoint available.')


def _is_any_tunnel_active(self) -> bool:
    """Check if any tunnel (Native or Pinggy) is active."""
    if self.HVYM_TUNNEL_ACTIVE:
        return True
    if self._is_tunnel_open():  # Pinggy
        return True
    return False
```

---

## Phase 9: Shutdown Integration

### `_quit_application`

Add native tunnel stop before Pinwheel:

```python
def _quit_application(self):
    """Clean shutdown of the application."""
    # Stop HVYM tunnel
    if HAS_HVYM_TUNNEL and self.tunnel_manager:
        self._stop_hvym_tunnel()

    # Stop Pinwheel daemon
    if HAS_PINWHEEL and self.pinwheel_worker:
        self._stop_pinwheel()

    # Stop API server
    if HAS_API_SERVER and self.api_server:
        self._stop_api_server()

    qApp.quit()
```

### `_stop_pintheon`

The native tunnel depends on Pintheon (same as Pinwheel). Add auto-stop:

```python
def _stop_pintheon(self, confirm=True):
    stop = True
    if confirm:
        stop = self.open_confirm_dialog('Stop Pintheon Gateway?')
    if stop:
        # Stop HVYM tunnel (depends on Pintheon)
        if HAS_HVYM_TUNNEL and self.HVYM_TUNNEL_ACTIVE:
            self._stop_hvym_tunnel()

        # Stop Pinwheel (depends on Pintheon's Kubo)
        if HAS_PINWHEEL and self.PINWHEEL_ACTIVE:
            self._stop_pinwheel()

        if self._stop_pintheon_direct():
            self.PINTHEON_ACTIVE = False
            self._update_ui_on_pintheon_stopped()
        else:
            self.open_msg_dialog('Failed to stop Pintheon. Check logs for details.')
```

---

## Phase 10: Build Pipeline

### `build_cross_platform.py` — `copy_source_files()`

Add the tunnel files:

```python
# HVYM tunnel client
('tunnel_client.py', 'tunnel_client.py'),
('tunnel_worker.py', 'tunnel_worker.py'),
('tunnel_config.py', 'tunnel_config.py'),
```

### `build_cross_platform.py` — hidden imports

```python
# HVYM tunnel client
'tunnel_client',
'tunnel_worker',
'tunnel_config',
'websockets',
'websockets.client',
```

### `requirements.txt`

```
websockets>=12.0
```

---

## Phase 11: TinyDB Schema Additions

New fields in the `app_data` document:

```json
{
    "type": "app_data",
    "tunnel_wallet": "GABCDEF..."
}
```

New document (`tunnel_config` type), managed by `TunnelConfigStore`:

```json
{
    "type": "tunnel_config",
    "server_url": "wss://tunnel.hvym.link/connect",
    "server_address": "GBCN2RKVT3YEGSCDC4IPPHRGJYGQN3RDQGTMEBF4WM4FVR4TZMKNAO64",
    "auto_connect": false,
    "services": ["pintheon"],
    "port_bindings": {"pintheon": 9998},
    "last_endpoint": null,
    "enabled": true
}
```

**`server_url`** is user-configurable via **Native Tunnel Settings**. Default is `wss://tunnel.hvym.link/connect` but can point to any HVYM Tunnler instance (e.g. `wss://us-west.tunnel.hvym.link/connect`, `wss://tunnel.my-org.com/connect`). When changed, `server_address` is auto-discovered via the new server's `/info` endpoint.

---

## Phase 12: Auto-connect (optional)

If `auto_connect` is true in `TunnelConfigStore`, start the native tunnel when Pintheon starts:

```python
def _update_ui_on_pintheon_started(self):
    # ... existing code ...

    # Auto-connect native tunnel if configured
    if HAS_HVYM_TUNNEL and self.tunnel_config_store:
        if self.tunnel_config_store.auto_connect and self.tunnel_config_store.is_configured():
            QTimer.singleShot(3000, self._start_hvym_tunnel)  # 3s delay
```

---

## Tray Menu Layout (Final)

```
System Tray Menu
├── Tools
│   ├── Installations
│   │   ├── Install Pintheon
│   │   ├── Install press
│   │   └── Update press
│   ├── Press
│   │   └── Run press
│   └── Pintheon testnet
│       ├── Settings
│       │   ├── Set Pinggy Token
│       │   ├── Set Pinggy Tier
│       │   ├── ─────────
│       │   └── Native Tunnel Settings...
│       ├── Start Pintheon / Stop Pintheon
│       ├── Open Tunnel                          ← SUBMENU
│       │   ├── Status: Disconnected
│       │   ├── ─────────
│       │   ├── Native (HVYM)
│       │   │   ├── Connect
│       │   │   ├── Disconnect
│       │   │   ├── Server: tunnel.hvym.link     ← reflects configured server
│       │   │   └── Endpoint: https://G...tunnel.hvym.link
│       │   ├── Pinggy
│       │   │   └── Open Pinggy Tunnel
│       │   ├── ─────────
│       │   └── Copy Endpoint URL
│       └── Interface
│           ├── Open Admin
│           └── Open Homepage
├── Pinwheel
│   └── ...
├── Metadata API
│   └── ...
├── Wallet Management
│   └── ...
└── Exit
```

---

## Dependency Chain

```
Metavinci starts
  → User clicks "Start Pintheon"
    → Docker container starts
      → Open Tunnel menu becomes enabled
        → User opens "Native (HVYM) → Connect"
          → Wallet selected (or stored preference used)
          → Stellar25519KeyPair built from secret
          → TunnelManager.start_tunnel()
            → TunnelWorker thread starts
              → HVYMTunnelClient.connect()
                → wss://tunnel.hvym.link/connect
                → Challenge-response auth (Stellar JWT)
                → auth_ok → endpoint URL received
                → Port bindings sent (pintheon → 9998)
                → Request forwarding loop active
                → UI updated: "Status: Connected (Native)"
        → OR User opens "Pinggy → Open Pinggy Tunnel"
          → Token/tier checked
          → Pinggy binary launched in terminal (unchanged)

Metavinci quits
  → _quit_application()
    → _stop_hvym_tunnel() → TunnelManager.stop_tunnel()
    → _stop_pinwheel()
    → _stop_api_server()
    → qApp.quit()
```

---

## File Summary

| File | Action | Changes |
|------|--------|---------|
| `tunnel_worker.py` | FIX | Change relative import to absolute (`from tunnel_client import ...`) |
| `metavinci.py` | MODIFY | Import block, instance vars, menu restructure, lifecycle methods, wallet integration, settings, shutdown |
| `build_cross_platform.py` | MODIFY | Add tunnel files to `copy_source_files()` and hidden imports |
| `requirements.txt` | MODIFY | Add `websockets>=12.0` |

---

## Testing Checklist

- [ ] Native tunnel: Connect → verify endpoint URL shown in menu
- [ ] Native tunnel: Disconnect → verify UI resets to "Disconnected"
- [ ] Native tunnel: Connect with encrypted mainnet wallet → password prompt
- [ ] Native tunnel: Server address auto-discovery via `/info`
- [ ] Native tunnel: Settings dialog persists server URL to TinyDB
- [ ] Pinggy tunnel: "Open Pinggy Tunnel" still works exactly as before
- [ ] Pinggy tunnel: Token and tier settings unchanged
- [ ] Open Tunnel menu disabled when Pintheon not running
- [ ] Open Tunnel menu enabled when Pintheon starts
- [ ] Stop Pintheon → native tunnel auto-disconnects
- [ ] Exit Metavinci → native tunnel cleanly stopped
- [ ] Copy Endpoint URL → clipboard contains public URL
- [ ] Build: All three tunnel files included in PyInstaller output
- [ ] Build: `websockets` resolved as hidden import
- [ ] Graceful degradation: If `tunnel_client.py` missing, only Pinggy shown
- [ ] Reconnection: Kill server briefly → client reconnects automatically
- [ ] Tray notification on successful native tunnel connection
