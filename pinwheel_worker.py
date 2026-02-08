"""
Pinwheel Daemon Worker

QThread wrapper that runs the PinnerDaemon async loop in a background thread.
Follows the same pattern as ApiServerWorker (api_server.py).
"""

import asyncio
import logging
from typing import Optional

try:
    from hvym_pinner.daemon import PinnerDaemon
    from hvym_pinner.models.config import DaemonConfig, DaemonMode, HunterConfig
    PINNER_AVAILABLE = True
except ImportError:
    PINNER_AVAILABLE = False
    PinnerDaemon = None
    DaemonConfig = None
    DaemonMode = None
    HunterConfig = None

try:
    from PyQt5.QtCore import QThread, pyqtSignal
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QThread = object
    pyqtSignal = lambda *args: None


class PinwheelWorker(QThread):
    """
    QThread worker that runs the Pinwheel (PinnerDaemon) async loop.

    Signals:
        started_signal: Emitted when Pinwheel starts successfully
        stopped_signal: Emitted when Pinwheel stops
        error_signal: Emitted with error message on failure
        status_signal: Emitted with status string on state changes
    """

    if PYQT5_AVAILABLE:
        started_signal = pyqtSignal()
        stopped_signal = pyqtSignal()
        error_signal = pyqtSignal(str)
        status_signal = pyqtSignal(str)

    def __init__(self, config: 'DaemonConfig', parent=None):
        if PYQT5_AVAILABLE:
            super().__init__(parent)
        else:
            super().__init__()
        self.config = config
        self.daemon: Optional['PinnerDaemon'] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def data_api(self):
        """Direct access to the daemon's DataAggregator (thread-safe reads)."""
        if self.daemon:
            return self.daemon.data_api
        return None

    def run(self):
        """Main thread execution — starts the PinnerDaemon async loop."""
        if not PINNER_AVAILABLE:
            self._emit_error("hvym-pinwheel not installed")
            return

        try:
            self.daemon = PinnerDaemon(self.config)
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._running = True
            self._emit_started()
            logging.info("Pinwheel daemon starting")

            self._loop.run_until_complete(self.daemon.start())

        except Exception as e:
            self._emit_error(f"Pinner daemon error: {e}")
        finally:
            self._running = False
            if self._loop:
                self._loop.close()
            self.daemon = None
            self._emit_stopped()
            logging.info("Pinwheel daemon stopped")

    def stop(self):
        """Request graceful daemon shutdown."""
        if self.daemon and self._running and self._loop:
            asyncio.run_coroutine_threadsafe(self.daemon.stop(), self._loop)
            logging.info("Pinwheel daemon shutdown requested")

    def get_dashboard_sync(self) -> Optional[dict]:
        """Fetch dashboard snapshot from the Pinwheel thread (blocking).

        Call from the main Qt thread to get current status.
        Returns dict or None if Pinwheel isn't running.
        """
        if not self.daemon or not self._loop or not self._running:
            return None
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.daemon.data_api.get_dashboard(), self._loop
            )
            snapshot = future.result(timeout=5)
            return snapshot.to_dict()
        except Exception as e:
            logging.warning(f"Failed to get Pinwheel dashboard: {e}")
            return None

    # Signal helpers (same pattern as ApiServerWorker)
    def _emit_started(self):
        if PYQT5_AVAILABLE and hasattr(self, 'started_signal'):
            self.started_signal.emit()

    def _emit_stopped(self):
        if PYQT5_AVAILABLE and hasattr(self, 'stopped_signal'):
            self.stopped_signal.emit()

    def _emit_error(self, msg: str):
        if PYQT5_AVAILABLE and hasattr(self, 'error_signal'):
            self.error_signal.emit(msg)

    def _emit_status(self, msg: str):
        if PYQT5_AVAILABLE and hasattr(self, 'status_signal'):
            self.status_signal.emit(msg)


def build_pinner_config(
    keypair_secret: str,
    network: str = "testnet",
    contract_id: str = "",
    factory_contract_id: str = "",
    mode: str = "auto",
    min_price: int = 10_000_000,  # stroops (1 XLM)
    db_path: str = "",
    hunter_enabled: bool = False,
) -> 'DaemonConfig':
    """Build a DaemonConfig from Metavinci's current state."""
    from hvym_pinner.models.config import DaemonConfig, DaemonMode, HunterConfig

    rpc_urls = {
        "testnet": "https://soroban-testnet.stellar.org",
        "mainnet": "https://soroban.stellar.org",
    }
    passphrases = {
        "testnet": "Test SDF Network ; September 2015",
        "mainnet": "Public Global Stellar Network ; September 2015",
    }

    if not db_path:
        from pathlib import Path
        db_path = str(Path.home() / "pintheon_data" / "pinner.db")

    return DaemonConfig(
        mode=DaemonMode(mode),
        rpc_url=rpc_urls.get(network, rpc_urls["testnet"]),
        network_passphrase=passphrases.get(network, passphrases["testnet"]),
        network=network,
        contract_id=contract_id,
        factory_contract_id=factory_contract_id,
        keypair_secret=keypair_secret,
        kubo_rpc_url="http://127.0.0.1:5001",
        db_path=db_path,
        min_price=min_price,
        hunter=HunterConfig(enabled=hunter_enabled),
    )
