# Metavinci CLI Removal Refactor Plan

This document tracks the progress of removing the hvym-cli dependency from metavinci and implementing the functionality directly.

## Overview

**Goal**: Remove all calls to `hvym-cli-dev` and implement the logic directly in metavinci for better reliability, user feedback, and reduced complexity.

**Current State**: metavinci calls the hvym CLI via subprocess for various operations. This causes issues with:
- GUI popups blocking when CLI is run as subprocess
- No real-time output streaming
- Complex error handling across process boundaries
- Dependency management issues

---

## Progress Tracking

### Completed ✅

| Feature | Status | Notes |
|---------|--------|-------|
| `pintheon-setup` | ✅ Done | Replaced with `PintheonSetupWorker` - direct Docker/Pinggy calls |
| `pintheon-start` | ✅ Done | `_start_pintheon_direct()` - direct Docker start/run |
| `pintheon-stop` | ✅ Done | `_stop_pintheon_direct()` - direct Docker stop |
| `pintheon-open` | ✅ Done | `_open_pintheon_admin()` - direct webbrowser.open() |
| `pintheon-image-exists` | ✅ Done | `_pintheon_image_exists()` - direct Docker images check |
| `docker-installed` | ✅ Done | `_check_docker_installed()` - direct Docker version check |
| `installation-stats` | ✅ Done | `_get_installation_stats()` - direct local state query |
| `pintheon-tunnel-open` | ✅ Done | `_open_tunnel_direct()` - opens pinggy in new terminal |
| `is-pintheon-tunnel-open` | ✅ Done | `_is_tunnel_open()` - checks localhost:4300 |
| `pinggy-set-token` | ✅ Done | `_set_tunnel_token_direct()` - Qt input dialog |
| `pinggy-set-tier` | ✅ Done | `_set_tunnel_tier_direct()` - Qt selection dialog |
| `pintheon-set-network` | ✅ Done | `_set_pintheon_network_direct()` - Qt selection dialog |

### In Progress 🔄

| Feature | Status | Notes |
|---------|--------|-------|

### Completed Cleanup ✅

| Item | Status | Notes |
|------|--------|-------|
| Remove unused hvym_* wrappers | ✅ Done | Removed 16+ unused methods |
| Update _update_install_stats() | ✅ Done | Uses _get_installation_stats() directly |
| Simplify _installation_check() | ✅ Done | No longer requires CLI verification |
| Verify _subprocess_hvym usage | ✅ Done | Kept for Stellar ops & update-npm-modules |

### All Phases Complete ✅

All CLI removal tasks have been completed.

### Intentionally Kept 🔒

| Feature | Reason |
|---------|--------|
| hvym_press Installation | Separate tool, not the CLI |
| `HVYM_IMG` | Just an image path (metavinci.png) |
| `hvym_stellar` library | Python package for Stellar 25519 keys |

---

## Detailed Implementation Plan

### Phase 1: Pintheon Operations (High Priority)

These are the most commonly used features and currently cause the most issues.

#### 1.1 `pintheon-start` → `_start_pintheon_direct()` ✅ DONE
**Implementation**:
- [x] Check if container exists: `docker ps -a --filter name=^pintheon$`
- [x] If exists: `docker start pintheon`
- [x] If not: create and start with `docker run -d`
- [x] Return success/failure boolean

#### 1.2 `pintheon-stop` → `_stop_pintheon_direct()` ✅ DONE
**Implementation**:
- [x] Run: `docker stop pintheon`
- [x] Return success/failure boolean

#### 1.3 `pintheon-open` → `_open_pintheon_admin()` ✅ DONE
**Implementation**:
- [x] Open browser with `webbrowser.open('https://127.0.0.1:9999/admin')`

#### 1.4 `pintheon-image-exists` → `_pintheon_image_exists()` ✅ DONE
**Implementation**:
- [x] Build image name with `_get_pintheon_image_name()`
- [x] Check with `docker images -q {image_name}`
- [x] Return boolean

#### 1.5 Additional utility methods added:
- `_check_docker_installed()` - Docker version check
- `_docker_container_exists(name)` - Check if any container exists
- `_docker_container_running(name)` - Check if container is running
- `_docker_image_exists(image_name)` - Generic image check
- `_get_pintheon_image_name()` - Build arch-specific image name
- `_get_docker_volume_path(local_path)` - Cross-platform volume path
- `_get_installation_stats()` - All stats without CLI
- `_open_pintheon_homepage()` - Open main page

#### Original reference - `pintheon-image-exists`:
```python
def pintheon_image_exists():
    image = REPO + '/' + _pintheon_dapp() + ':' + PINTHEON_VERSION
    click.echo(_docker_image_exists(image))
```
**Implementation**:
- [ ] Run: `docker images -q metavinci/pintheon-{network}-linux-{arch}:latest`
- [ ] Return True if output is non-empty

---

### Phase 2: Pintheon Tunnel (High Priority)

#### 2.1 `pintheon-tunnel-open` → `_open_tunnel_direct()`
**Current CLI call**: `hvym pintheon-tunnel-open` (non-blocking)
**What it does**:
```python
def pintheon_tunnel_open():
    token = _pinggy_token()
    tier = _pinggy_tier()
    port = _pintheon_port()

    if tier == 'pro':
        command = f'{PINGGY} -t -p {port} -R0:localhost:{port} tcp+tls a.]pinggy.io:443 -i -o {HOME} -k {token}'
    else:
        command = f'{PINGGY} -t -p {port} tcp+tls a.pinggy.io:443 -i -o {HOME}'

    _call(command)  # Non-blocking
```
**Implementation**:
- [ ] Get pinggy path from platform paths
- [ ] Get token/tier from config
- [ ] Run pinggy command as background process
- [ ] Track process for later termination

#### 2.2 `is-pintheon-tunnel-open` → `_is_tunnel_open()`
**Current CLI call**: `hvym is-pintheon-tunnel-open`
**What it does**: Checks if pinggy process is running
**Implementation**:
- [ ] Check if tracked pinggy process is still running
- [ ] Or check process list for pinggy

#### 2.3 `pinggy-set-token` → `_set_tunnel_token_direct()`
**Current CLI call**: `hvym pinggy-set-token`
**What it does**: Shows popup to enter token, saves to TinyDB
**Implementation**:
- [ ] Show Qt input dialog
- [ ] Save to metavinci's own config

#### 2.4 `pinggy-set-tier` → `_set_tunnel_tier_direct()`
**Current CLI call**: `hvym pinggy-set-tier`
**What it does**: Shows popup to select tier (pro/free), saves to TinyDB
**Implementation**:
- [ ] Show Qt selection dialog
- [ ] Save to metavinci's own config

#### 2.5 `pinggy-token` / `pinggy-tier` → Config getters
**Implementation**:
- [ ] Read from metavinci's config instead of CLI

---

### Phase 3: Configuration & Stats (Medium Priority)

#### 3.1 `installation-stats` → `_get_installation_stats()`
**Current CLI call**: `hvym installation-stats`
**What it does**:
```python
def installation_stats():
    stats = {
        'docker_installed': _check_docker_installed(),
        'pintheon_image_exists': _docker_image_exists(...),
        'pinggy_tier': _pinggy_tier(),
        'pinggy_token': _pinggy_token(),
        'pintheon_network': _pintheon_network()
    }
    click.echo(json.dumps(stats))
```
**Implementation**:
- [ ] Check Docker: `docker --version`
- [ ] Check image: `docker images -q {image_name}`
- [ ] Get config values from metavinci config
- [ ] Return dict directly (no JSON parsing needed)

#### 3.2 `pintheon-set-network` → `_set_pintheon_network_direct()`
**Current CLI call**: `hvym pintheon-set-network`
**What it does**: Shows popup to select network (testnet/mainnet)
**Implementation**:
- [ ] Show Qt selection dialog
- [ ] Save to config
- [ ] Note: Changing network requires re-pulling image

#### 3.3 `docker-installed` → `_check_docker_installed()`
**Already implemented** in `PintheonSetupWorker._check_docker_installed()`
- [ ] Extract to shared utility method

---

### Phase 4: Stellar Operations

These are wallet management features with complex GUI dialogs.

**Dependencies Required**:
- `stellar_sdk` - Stellar keypair generation (`pip install stellar-sdk`)
- Custom dialog classes (implemented in metavinci)
- Encrypted TinyDB storage (already in metavinci)

**GUI Components to Create**:
- `StellarUserPasswordDialog` - Username + password input with icon
- `StellarPasswordDialog` - Password-only input with icon
- `StellarAccountSelectDialog` - Dropdown selection with icon
- `StellarCopyTextDialog` - Display seed phrase with copy button

#### 4.1 `stellar-new-account` → `new_stellar_account()` ✅ DONE
**What it does**: Creates a new Stellar wallet account
**Implementation**:
- [x] Show user/password dialog (account name + passphrase)
- [x] Show password confirmation dialog
- [x] Validate passwords match
- [x] Generate Stellar keypair using `stellar_sdk.Keypair.random()`
- [x] Derive 25519 keypair using `hvym_stellar.Stellar25519KeyPair`
- [x] Hash password for storage
- [x] Store account in TinyDB: `{name, public, 25519_pub, active, pw_hash, network}`
- [x] Display seed phrase in copy dialog (CRITICAL: user must save this!)
- [x] Set new account as active

#### 4.2 `stellar-set-account` → `change_stellar_account()` ✅ DONE
**What it does**: Select which Stellar account is active
**Implementation**:
- [x] Get list of accounts from DB
- [x] Show dropdown selection dialog
- [x] Update `active` flag on selected account
- [x] Show confirmation message

#### 4.3 `stellar-remove-account` → `remove_stellar_account()` ✅ DONE
**What it does**: Remove a Stellar account from the wallet
**Implementation**:
- [x] Get list of accounts from DB
- [x] Show dropdown selection dialog
- [x] Show password verification dialog
- [x] Verify password hash matches
- [x] Remove account from DB
- [x] If accounts remain, set first as active
- [x] Show confirmation message

#### 4.4 `stellar-new-testnet-account` → `new_stellar_testnet_account()` ✅ DONE
**What it does**: Creates a new Stellar testnet account with funding
**Implementation**:
- [x] Same steps as `stellar-new-account`
- [x] Call Friendbot API to fund: `https://horizon-testnet.stellar.org/friendbot?addr={public_key}`
- [x] Show funding result message

#### 4.5 Database Schema ✅ IMPLEMENTED
```python
STELLAR_ACCOUNTS_TABLE = {
    'data_type': 'STELLAR_ID',
    'name': str,           # Account name
    'public': str,         # Stellar public key
    '25519_pub': str,      # Ed25519 public key (via hvym_stellar.Stellar25519KeyPair)
    'active': bool,        # Is this the active account?
    'pw_hash': str,        # SHA256 hashed passphrase (for verification)
    'network': str         # 'testnet' or 'mainnet'
}

---

### Phase 5: Cleanup (Final) ✅ DONE

#### 5.1 Remove CLI Installation Features ✅
- [x] Remove `HvymInstallWorker` class
- [x] Remove `get_latest_hvym_release_asset_url()` function
- [x] Remove `download_and_install_hvym_cli()` function
- [x] Remove `_install_hvym()` / `_update_hvym()` / `_delete_hvym()` methods
- [x] Remove `_on_hvym_install_success()` / `_on_hvym_update_success()` callbacks
- [x] Remove `self.HVYM` path tracking
- [x] Remove macOS HVYM fallback code
- [x] Remove `_log_hvym_path()` method
- [x] Remove install/update menu actions (`install_hvym_action`, `update_hvym_action`)
- [x] Remove `_subprocess_hvym()` method
- [x] Remove `_update_ui_on_hvym_installed()` method
- [x] Remove CLI check from `_installation_check()`
- [x] Remove CLI update from `update_tools()`

#### 5.2 Remove Unused Code ✅
- [x] Remove `hvym_*` method wrappers (done in Phase 3)
- [x] Clean up docstrings referencing CLI

#### 5.3 Kept Items
- `HVYM_IMG` - Just an image path (metavinci.png), not CLI-related
- `hvym_press` code - Separate tool, not the CLI
- `hvym_stellar` import - Python library for Stellar 25519 keys

---

## Configuration Migration

Currently, hvym CLI stores config in TinyDB at a CLI-specific path. We need to either:

**Option A**: Migrate config to metavinci's own config system
- Pros: Self-contained, no CLI dependency
- Cons: Need to handle migration for existing users

**Option B**: Share config with CLI (if CLI is still needed for Blender)
- Pros: Seamless if user also uses Blender addon
- Cons: Still has cross-dependency

**Recommended**: Option A - move all config into metavinci's existing config system.

Config values to migrate:
- `pinggy_token` - Tunnel authentication token
- `pinggy_tier` - pro/free tier selection
- `pintheon_port` - Default 9998
- `pintheon_network` - testnet/mainnet

---

## Files to Modify

| File | Changes |
|------|---------|
| `metavinci.py` | Main refactoring - remove CLI calls, add direct implementations |
| `platform_manager.py` | May need updates for pinggy paths |

---

## Testing Checklist

After each phase, verify:
- [ ] Pintheon can be installed (Docker image pulled, container created)
- [ ] Pintheon can be started
- [ ] Pintheon can be stopped
- [ ] Pintheon admin interface opens in browser
- [ ] Tunnel can be opened (if token configured)
- [ ] Tunnel token can be set
- [ ] Tunnel tier can be changed
- [ ] Network can be changed
- [ ] UI updates correctly for all states

---

## Notes

- The `hvym_press` tool is separate and may still need CLI for Blender integration
- Some CLI commands (custom prompts, splash, etc.) are only used by the CLI itself
- The Blender addon may still need the CLI - consider keeping CLI install for that use case

---

## Session Log

### Session 1
- [x] Identified CLI hanging issue with `pintheon-setup`
- [x] Created `PintheonSetupWorker` with direct Docker implementation
- [x] Created `OutputWindow` for streaming output display
- [x] Fixed image name to include OS (`linux-amd64`)
- [x] Created this planning document
- [x] **Phase 1 Complete**: Implemented all Pintheon operations directly
  - `_start_pintheon_direct()` - Docker start/run
  - `_stop_pintheon_direct()` - Docker stop
  - `_open_pintheon_admin()` / `_open_pintheon_homepage()` - Browser open
  - `_pintheon_image_exists()` - Docker image check
  - `_check_docker_installed()` - Docker availability
  - `_get_installation_stats()` - All stats without CLI
  - Various helper methods for Docker operations
- [x] Updated `_start_pintheon()`, `_stop_pintheon()`, `_open_pintheon()` to use direct methods
- [x] Added `PINTHEON_PORT` instance variable
- [x] **Phase 2 Complete**: Implemented all Tunnel/Pinggy operations directly
  - `_get_pinggy_path()` - Platform-specific pinggy binary path
  - `_is_tunnel_open()` - Check tunnel via localhost:4300
  - `_open_tunnel_direct()` - Open pinggy in new terminal window (Windows/macOS/Linux)
  - `_set_tunnel_token_direct()` - Qt QInputDialog for token input
  - `_set_tunnel_tier_direct()` - Qt QInputDialog.getItem for tier selection
  - `_set_pintheon_network_direct()` - Qt dialog for network selection
- [x] Added `QInputDialog` import for Qt dialogs
- [x] Added `PINGGY_TIER` instance variable
- [x] Updated `_open_tunnel()`, `_set_tunnel_token()`, `_set_tunnel_tier()`, `_set_pintheon_network()` to use direct methods

### Session 2
- [x] **Phase 3 Complete**: Removed unused CLI wrappers
  - Removed 16+ unused `hvym_*` methods: `splash()`, `hvym_check()`, `hvym_pintheon_exists()`, `hvym_tunnel_token_exists()`, `hvym_start_pintheon()`, `hvym_open_pintheon()`, `hvym_stop_pintheon()`, `hvym_open_tunnel()`, `hvym_set_tunnel_token()`, `hvym_set_tunnel_tier()`, `hvym_get_tunnel_tier()`, `hvym_set_pintheon_network()`, `hvym_get_pintheon_network()`, `hvym_is_tunnel_open()`, `hvym_docker_installed()`, `hvym_install_stats()`
  - Updated `_update_install_stats()` to use `_get_installation_stats()` directly
  - Simplified `_installation_check()` to not require CLI verification
  - Kept `_subprocess_hvym()` for Stellar operations and `update-npm-modules`
  - Kept hvym CLI install/update infrastructure for Blender addon compatibility

### Session 3
- [x] **Phase 4 Complete**: Implemented all Stellar operations directly
  - Created custom Qt dialog classes:
    - `StellarUserPasswordDialog` - Account name + passphrase input
    - `StellarPasswordDialog` - Password verification
    - `StellarAccountSelectDialog` - Dropdown account selection
    - `StellarCopyTextDialog` - Seed phrase display with copy button
    - `StellarMessageDialog` - Simple message display
  - Implemented direct Stellar methods:
    - `new_stellar_account()` - Creates new mainnet account with keypair generation
    - `change_stellar_account()` - Select active account from dropdown
    - `remove_stellar_account()` - Remove account with password verification
    - `new_stellar_testnet_account()` - Creates testnet account with Friendbot funding
  - Added helper methods:
    - `_get_stellar_accounts_table()` - Database table access
    - `_get_stellar_account_names()` - List all account names
    - `_get_active_stellar_account()` - Get currently active account
    - `_hash_password()` / `_verify_password()` - Password security
  - Added `stellar-sdk>=9.0.0` to requirements.txt
  - Added `hvym_stellar>=0.11` to requirements.txt for 25519 keypair derivation
  - Added `hashlib` import for password hashing
  - Stellar SDK + hvym_stellar are optional dependencies (graceful fallback if not installed)

### Session 4
- [x] **Phase 5 Complete**: Removed all CLI installation infrastructure
  - Removed `HvymInstallWorker` class
  - Removed `get_latest_hvym_release_asset_url()` function
  - Removed `download_and_install_hvym_cli()` function (~260 lines)
  - Removed `self.HVYM` path initialization and macOS fallback code
  - Removed `_log_hvym_path()` method
  - Removed `_install_hvym()`, `_update_hvym()`, `_delete_hvym()` methods
  - Removed success callback methods for hvym install/update
  - Removed `install_hvym_action` and `update_hvym_action` menu items
  - Removed `_subprocess_hvym()` method
  - Removed `_update_ui_on_hvym_installed()` method
  - Updated `update_tools()` to remove CLI update calls
  - Simplified `_installation_check()` to remove CLI references
  - Updated docstring to remove CLI worker references

### Session 5
- [x] **Supporting File Cleanup Complete**:
  - `platform_manager.py`: Removed `get_hvym_path()` method
  - `platform_manager.py`: Removed `get_install_script_url()` method
  - `macos_install_helper.py`: Removed all hvym CLI install methods:
    - `install_hvym_cli()`, `_download_hvym_cli()`, `_get_latest_hvym_release_url()`
    - `_install_binary()`, `_verify_installation()`, `check_installation_status()`
    - `uninstall_hvym_cli()`, `get_install_info()`
  - `macos_install_helper.py`: Removed `self.hvym_path` from `__init__`
  - `macos_install_helper.py`: Updated `get_installation_status()` for hvym_press
  - `macos_install_helper.py`: Updated `check_macos_permissions()` for hvym_press
  - `macos_install_helper.py`: Updated `main()` to test hvym_press instead
  - `macos_install_helper.py`: Removed unused `sys` import

## CLI Removal Complete! 🎉

All hvym CLI dependencies have been removed from metavinci. The application now:
- Handles all Pintheon operations directly via Docker commands
- Handles all Tunnel/Pinggy operations directly
- Handles all Stellar operations directly with `stellar-sdk` and `hvym_stellar`
- Only keeps `hvym_press` as a separate downloadable tool (not the CLI)

---

## Build Pipeline Verification Tasks

After the CLI removal overhaul, the following tasks should be completed to ensure the build pipeline is sound.

### 1. Supporting File Cleanup ✅

| File | Task | Status |
|------|------|--------|
| `platform_manager.py` | Remove `get_hvym_path()` method | ✅ |
| `platform_manager.py` | Remove `get_install_script_url()` method (CLI script URL) | ✅ |
| `macos_install_helper.py` | Remove hvym CLI install methods, keep hvym_press methods | ✅ |
| `macos_install_helper.py` | Remove `install_hvym_cli()`, `_download_hvym_cli()`, `_get_latest_hvym_release_url()` | ✅ |
| `macos_install_helper.py` | Remove `_install_binary()`, `_verify_installation()`, `check_installation_status()` | ✅ |
| `macos_install_helper.py` | Remove `uninstall_hvym_cli()`, `get_install_info()` | ✅ |
| `macos_install_helper.py` | Update `__init__` to remove `self.hvym_path` | ✅ |

### 2. Build Configuration Verification ⬜

| Task | Description | Status |
|------|-------------|--------|
| Verify `build.py` | Ensure correct dependency files are copied | ⬜ |
| Verify `setup.py` | Confirm MSI/installer config is correct | ⬜ |
| Verify `requirements.txt` | Confirm all dependencies are present (`stellar-sdk`, `hvym_stellar`) | ⬜ |
| Check for unused imports | Remove any unused imports in `metavinci.py` | ⬜ |

### 3. Syntax & Import Verification ⬜

| Task | Command | Status |
|------|---------|--------|
| Python syntax check | `python -m py_compile metavinci.py` | ⬜ |
| Import verification | `python -c "import metavinci"` | ⬜ |
| Platform manager import | `python -c "from platform_manager import PlatformManager"` | ⬜ |
| Stellar SDK import | `python -c "from stellar_sdk import Keypair"` | ⬜ |
| hvym_stellar import | `python -c "from hvym_stellar import Stellar25519KeyPair"` | ⬜ |

### 4. Functional Testing ⬜

#### Pintheon Operations
| Test | Description | Status |
|------|-------------|--------|
| Docker check | `_check_docker_installed()` returns correct value | ⬜ |
| Image check | `_pintheon_image_exists()` works correctly | ⬜ |
| Container start | `_start_pintheon_direct()` starts container | ⬜ |
| Container stop | `_stop_pintheon_direct()` stops container | ⬜ |
| Admin open | `_open_pintheon_admin()` opens browser | ⬜ |
| Setup flow | Full Pintheon setup with `PintheonSetupWorker` | ⬜ |

#### Tunnel Operations
| Test | Description | Status |
|------|-------------|--------|
| Tunnel status | `_is_tunnel_open()` returns correct value | ⬜ |
| Token dialog | `_set_tunnel_token_direct()` shows dialog | ⬜ |
| Tier dialog | `_set_tunnel_tier_direct()` shows dialog | ⬜ |
| Network dialog | `_set_pintheon_network_direct()` shows dialog | ⬜ |
| Open tunnel | `_open_tunnel_direct()` opens tunnel (if token configured) | ⬜ |

#### Stellar Operations
| Test | Description | Status |
|------|-------------|--------|
| New account | `new_stellar_account()` creates account with 25519 keypair | ⬜ |
| Change account | `change_stellar_account()` switches active account | ⬜ |
| Remove account | `remove_stellar_account()` removes with password verification | ⬜ |
| Testnet account | `new_stellar_testnet_account()` creates and funds via Friendbot | ⬜ |

#### hvym_press Operations (kept)
| Test | Description | Status |
|------|-------------|--------|
| Install press | `_install_press()` downloads and installs | ⬜ |
| Update press | `_update_press()` updates installation | ⬜ |
| Run press | `run_press()` launches hvym_press | ⬜ |

### 5. Build & Package Testing ⬜

| Platform | Task | Status |
|----------|------|--------|
| Windows | Run `python build.py --windows` | ⬜ |
| Windows | Test built executable launches | ⬜ |
| Windows | Test MSI installer (`python setup.py bdist_msi`) | ⬜ |
| macOS | Run `python build.py --mac` | ⬜ |
| macOS | Test built executable launches | ⬜ |
| macOS | Verify code signing (if applicable) | ⬜ |
| Linux | Run `python build.py` | ⬜ |
| Linux | Test built executable launches | ⬜ |

### 6. UI Verification ⬜

| Test | Description | Status |
|------|-------------|--------|
| Tray menu | No "Install hvym" or "Update hvym" menu items visible | ⬜ |
| Pintheon menu | All Pintheon operations work from tray menu | ⬜ |
| Stellar menu | All Stellar operations work from tray menu | ⬜ |
| Press menu | hvym_press installation/update works | ⬜ |
| Dialogs | All custom dialogs (Stellar, Pintheon setup) display correctly | ⬜ |

### 7. Error Handling Verification ⬜

| Test | Description | Status |
|------|-------------|--------|
| No Docker | Graceful error when Docker not installed | ⬜ |
| No Stellar SDK | Graceful fallback message if stellar-sdk not installed | ⬜ |
| No network | Graceful error on network failures | ⬜ |
| Bad password | Correct error message on wrong Stellar password | ⬜ |

---

## Files Modified in Refactor

| File | Changes |
|------|---------|
| `metavinci.py` | Removed CLI code, added direct implementations |
| `requirements.txt` | Added `stellar-sdk>=9.0.0`, `hvym_stellar>=0.11` |
| `platform_manager.py` | Removed `get_hvym_path()`, `get_install_script_url()` |
| `macos_install_helper.py` | Removed hvym CLI install methods, kept hvym_press methods |
| `REMOVE_CLI.md` | This planning document |
