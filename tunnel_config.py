"""
Tunnel configuration persistence.

Stores tunnel settings in TinyDB alongside existing Metavinci config.
"""

from typing import Optional, Dict, Any
from tinydb import TinyDB, Query


class TunnelConfigStore:
    """
    Persistent storage for tunnel configuration.

    Integrates with Metavinci's existing TinyDB database.
    """

    # Default configuration values
    DEFAULT_SERVER_URL = "wss://tunnel.heavymeta.art/connect"
    DEFAULT_SERVICES = ["pintheon"]
    DEFAULT_PORT_BINDINGS = {"pintheon": 9998}

    def __init__(self, db: TinyDB):
        """
        Initialize config store.

        Args:
            db: TinyDB instance (from Metavinci)
        """
        self.db = db
        self.query = Query()
        self._ensure_table()

    def _ensure_table(self):
        """Ensure tunnel config exists in database."""
        existing = self.db.search(self.query.type == 'tunnel_config')
        if not existing:
            self.db.insert({
                'type': 'tunnel_config',
                'server_url': self.DEFAULT_SERVER_URL,
                'server_address': '',  # Will be set when server is deployed
                'auto_connect': False,
                'services': self.DEFAULT_SERVICES,
                'port_bindings': self.DEFAULT_PORT_BINDINGS,
                'last_endpoint': None,
                'enabled': True
            })

    def get_config(self) -> Dict[str, Any]:
        """Get tunnel configuration."""
        result = self.db.search(self.query.type == 'tunnel_config')
        if result:
            return result[0]
        return {
            'server_url': self.DEFAULT_SERVER_URL,
            'server_address': '',
            'auto_connect': False,
            'services': self.DEFAULT_SERVICES,
            'port_bindings': self.DEFAULT_PORT_BINDINGS
        }

    def set_config(self, **kwargs):
        """Update tunnel configuration."""
        self.db.update(kwargs, self.query.type == 'tunnel_config')

    @property
    def server_url(self) -> str:
        """Get server WebSocket URL."""
        return self.get_config().get('server_url', self.DEFAULT_SERVER_URL)

    @server_url.setter
    def server_url(self, value: str):
        self.set_config(server_url=value)

    @property
    def server_address(self) -> str:
        """Get server Stellar address."""
        return self.get_config().get('server_address', '')

    @server_address.setter
    def server_address(self, value: str):
        self.set_config(server_address=value)

    @property
    def auto_connect(self) -> bool:
        """Get auto-connect setting."""
        return self.get_config().get('auto_connect', False)

    @auto_connect.setter
    def auto_connect(self, value: bool):
        self.set_config(auto_connect=value)

    @property
    def services(self) -> list:
        """Get requested services list."""
        return self.get_config().get('services', self.DEFAULT_SERVICES)

    @services.setter
    def services(self, value: list):
        self.set_config(services=value)

    @property
    def port_bindings(self) -> Dict[str, int]:
        """Get port bindings dictionary."""
        return self.get_config().get('port_bindings', self.DEFAULT_PORT_BINDINGS)

    def set_port_binding(self, service: str, port: int):
        """Set a port binding for a service."""
        bindings = self.port_bindings
        bindings[service] = port
        self.set_config(port_bindings=bindings)

    def remove_port_binding(self, service: str):
        """Remove a port binding."""
        bindings = self.port_bindings
        if service in bindings:
            del bindings[service]
            self.set_config(port_bindings=bindings)

    @property
    def enabled(self) -> bool:
        """Check if tunnel is enabled."""
        return self.get_config().get('enabled', True)

    @enabled.setter
    def enabled(self, value: bool):
        self.set_config(enabled=value)

    def get_last_endpoint(self) -> Optional[str]:
        """Get last known endpoint URL."""
        return self.get_config().get('last_endpoint')

    def set_last_endpoint(self, url: str):
        """Store last known endpoint URL."""
        self.set_config(last_endpoint=url)

    def clear_last_endpoint(self):
        """Clear last endpoint URL."""
        self.set_config(last_endpoint=None)

    def is_configured(self) -> bool:
        """Check if tunnel is properly configured."""
        config = self.get_config()
        return bool(config.get('server_address'))

    def to_tunnel_config(self):
        """Convert to TunnelConfig object for client.

        Returns:
            TunnelConfig: Configuration object for HVYMTunnelClient
        """
        # Try relative import first (when used as package), then absolute
        try:
            from .tunnel_client import TunnelConfig
        except ImportError:
            from tunnel_client import TunnelConfig

        config = self.get_config()
        return TunnelConfig(
            server_url=config.get('server_url', self.DEFAULT_SERVER_URL),
            server_address=config.get('server_address', ''),
            services=config.get('services', self.DEFAULT_SERVICES),
            local_pintheon_port=config.get('port_bindings', {}).get('pintheon', 9998)
        )
