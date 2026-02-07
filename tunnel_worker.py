"""
Qt Thread wrapper for HVYM Tunnel Client.

Provides PyQt5 signals for tunnel events and runs the async
client in a background thread.
"""

import asyncio
import logging
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal, QObject

try:
    from hvym_stellar import Stellar25519KeyPair
    HVYM_STELLAR_AVAILABLE = True
except ImportError:
    HVYM_STELLAR_AVAILABLE = False
    Stellar25519KeyPair = None

from .tunnel_client import HVYMTunnelClient, TunnelConfig, TunnelState, TunnelEndpoint


class TunnelWorker(QThread):
    """
    Background worker for tunnel connection.

    Signals:
        state_changed(str): Tunnel state changed
        connected(str): Connected with endpoint URL
        disconnected(): Connection lost
        error(str): Error occurred
        endpoint_ready(str): Public endpoint URL available

    Example:
        # In Metavinci class
        self.tunnel_worker = TunnelWorker(self.stellar_keypair)
        self.tunnel_worker.connected.connect(self._on_tunnel_connected)
        self.tunnel_worker.error.connect(self._on_tunnel_error)
        self.tunnel_worker.start()
    """

    # Signals
    state_changed = pyqtSignal(str)
    connected = pyqtSignal(str)      # endpoint URL
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    endpoint_ready = pyqtSignal(str)  # endpoint URL

    def __init__(
        self,
        wallet: 'Stellar25519KeyPair',
        config: TunnelConfig = None,
        parent: QObject = None
    ):
        """
        Initialize tunnel worker.

        Args:
            wallet: Stellar25519KeyPair for authentication
            config: Optional tunnel configuration
            parent: Qt parent object
        """
        super().__init__(parent)
        self.wallet = wallet
        self.config = config or TunnelConfig()
        self._client: Optional[HVYMTunnelClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._logger = logging.getLogger("TunnelWorker")

        # Port bindings to apply when client is created
        self._pending_bindings: dict = {}

    @property
    def is_connected(self) -> bool:
        """Check if tunnel is connected."""
        return self._client is not None and self._client.is_connected

    @property
    def endpoint_url(self) -> Optional[str]:
        """Get current endpoint URL."""
        if self._client and self._client.endpoint:
            return self._client.endpoint.url
        return None

    @property
    def stellar_address(self) -> str:
        """Get client's Stellar address."""
        return self.wallet.base_stellar_keypair().public_key

    def bind_port(self, service: str, local_port: int):
        """Bind a local port to a service."""
        self._pending_bindings[service] = local_port
        if self._client:
            self._client.bind_port(service, local_port)

    def run(self):
        """Thread entry point - runs async event loop."""
        self._logger.info("Tunnel worker starting")

        # Create new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            # Create client
            self._client = HVYMTunnelClient(self.wallet, self.config)

            # Apply pending port bindings
            for service, port in self._pending_bindings.items():
                self._client.bind_port(service, port)

            # Wire up callbacks to emit Qt signals
            self._client.on_state_changed = self._on_state_changed
            self._client.on_connected = self._on_connected
            self._client.on_disconnected = self._on_disconnected
            self._client.on_error = self._on_error
            self._client.on_endpoint_ready = self._on_endpoint_ready

            # Run connection loop
            self._loop.run_until_complete(self._client.connect())

        except Exception as e:
            self._logger.error(f"Tunnel worker error: {e}")
            self.error.emit(str(e))

        finally:
            if self._loop:
                self._loop.close()
            self._logger.info("Tunnel worker stopped")

    def stop(self):
        """Stop the tunnel connection."""
        if self._client:
            self._client.disconnect_sync()

        # Wait for thread to finish
        self.wait(5000)

    def _on_state_changed(self, state: TunnelState):
        """Handle state change from client."""
        self.state_changed.emit(state.value)

    def _on_connected(self, endpoint: TunnelEndpoint):
        """Handle connection from client."""
        self.connected.emit(endpoint.url)

    def _on_disconnected(self):
        """Handle disconnection from client."""
        self.disconnected.emit()

    def _on_error(self, message: str):
        """Handle error from client."""
        self.error.emit(message)

    def _on_endpoint_ready(self, url: str):
        """Handle endpoint ready from client."""
        self.endpoint_ready.emit(url)


class TunnelManager(QObject):
    """
    High-level tunnel manager for Metavinci.

    Manages tunnel lifecycle, configuration persistence,
    and integration with Pintheon.

    Example:
        self.tunnel_manager = TunnelManager(self)
        self.tunnel_manager.set_wallet(self.stellar_keypair)
        self.tunnel_manager.connected.connect(self._update_pintheon_gateway)
        self.tunnel_manager.start_tunnel()
    """

    # Signals (forwarded from worker)
    state_changed = pyqtSignal(str)
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._wallet: Optional['Stellar25519KeyPair'] = None
        self._worker: Optional[TunnelWorker] = None
        self._config = TunnelConfig()
        self._logger = logging.getLogger("TunnelManager")

        # Default port bindings
        self._default_bindings = {
            "pintheon": 9998,
        }

    def set_wallet(self, wallet: 'Stellar25519KeyPair'):
        """Set the wallet for authentication."""
        self._wallet = wallet

    def set_server(self, server_url: str, server_address: str):
        """Configure tunnel server."""
        self._config.server_url = server_url
        self._config.server_address = server_address

    def set_services(self, services: list):
        """Set services to request."""
        self._config.services = services

    def add_port_binding(self, service: str, port: int):
        """Add a port binding."""
        self._default_bindings[service] = port

    @property
    def is_connected(self) -> bool:
        """Check if tunnel is connected."""
        return self._worker is not None and self._worker.is_connected

    @property
    def endpoint_url(self) -> Optional[str]:
        """Get current endpoint URL."""
        if self._worker:
            return self._worker.endpoint_url
        return None

    @property
    def stellar_address(self) -> Optional[str]:
        """Get client's Stellar address."""
        if self._wallet:
            return self._wallet.base_stellar_keypair().public_key
        return None

    def start_tunnel(self) -> bool:
        """
        Start the tunnel connection.

        Returns:
            True if tunnel started, False if missing wallet or already running
        """
        if not HVYM_STELLAR_AVAILABLE:
            self._logger.error("hvym_stellar not available")
            self.error.emit("hvym_stellar library not installed")
            return False

        if not self._wallet:
            self._logger.error("Cannot start tunnel: no wallet configured")
            self.error.emit("No wallet configured for tunnel authentication")
            return False

        if self._worker and self._worker.isRunning():
            self._logger.warning("Tunnel already running")
            return False

        # Check server address is configured
        if not self._config.server_address:
            self._logger.error("Server address not configured")
            self.error.emit("Tunnel server address not configured")
            return False

        self._logger.info("Starting tunnel...")

        # Create worker
        self._worker = TunnelWorker(self._wallet, self._config, self)

        # Connect signals
        self._worker.state_changed.connect(self.state_changed.emit)
        self._worker.connected.connect(self._on_connected)
        self._worker.disconnected.connect(self.disconnected.emit)
        self._worker.error.connect(self.error.emit)

        # Add default port bindings
        for service, port in self._default_bindings.items():
            self._worker.bind_port(service, port)

        # Start worker thread
        self._worker.start()
        return True

    def stop_tunnel(self):
        """Stop the tunnel connection."""
        if self._worker:
            self._logger.info("Stopping tunnel...")
            self._worker.stop()
            self._worker = None

    def _on_connected(self, endpoint_url: str):
        """Handle connection."""
        self._logger.info(f"Tunnel connected: {endpoint_url}")
        self.connected.emit(endpoint_url)
