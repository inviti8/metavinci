"""
Tests for HVYM Tunnel Client.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTunnelConfig:
    """Test TunnelConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        from tunnel_client import TunnelConfig

        config = TunnelConfig()

        assert config.server_url == "wss://tunnel.heavymeta.art/connect"
        assert config.services == ["pintheon"]
        assert config.reconnect_delay == 1.0
        assert config.max_reconnect_delay == 60.0
        assert config.jwt_lifetime == 3600

    def test_custom_config(self):
        """Test custom configuration."""
        from tunnel_client import TunnelConfig

        config = TunnelConfig(
            server_url="wss://custom.example.com/connect",
            server_address="GSERVER123",
            services=["pintheon", "ipfs"],
            jwt_lifetime=7200
        )

        assert config.server_url == "wss://custom.example.com/connect"
        assert config.server_address == "GSERVER123"
        assert config.services == ["pintheon", "ipfs"]
        assert config.jwt_lifetime == 7200


class TestTunnelState:
    """Test TunnelState enum."""

    def test_states(self):
        """Test state values."""
        from tunnel_client import TunnelState

        assert TunnelState.DISCONNECTED.value == "disconnected"
        assert TunnelState.CONNECTING.value == "connecting"
        assert TunnelState.AUTHENTICATING.value == "authenticating"
        assert TunnelState.CONNECTED.value == "connected"
        assert TunnelState.RECONNECTING.value == "reconnecting"
        assert TunnelState.ERROR.value == "error"


class TestHVYMTunnelClient:
    """Test HVYMTunnelClient."""

    @pytest.fixture
    def wallet(self):
        """Create test wallet."""
        from stellar_sdk import Keypair
        from hvym_stellar import Stellar25519KeyPair
        return Stellar25519KeyPair(Keypair.random())

    @pytest.fixture
    def config(self):
        """Create test config."""
        from stellar_sdk import Keypair
        from tunnel_client import TunnelConfig
        return TunnelConfig(
            server_url="wss://test.example.com/connect",
            server_address=Keypair.random().public_key
        )

    def test_client_creation(self, wallet, config):
        """Test client initialization."""
        from tunnel_client import HVYMTunnelClient, TunnelState

        client = HVYMTunnelClient(wallet, config)

        assert client.state == TunnelState.DISCONNECTED
        assert client.stellar_address == wallet.base_stellar_keypair().public_key
        assert not client.is_connected
        assert client.endpoint is None

    def test_jwt_creation(self, wallet, config):
        """Test JWT token creation."""
        from tunnel_client import HVYMTunnelClient

        client = HVYMTunnelClient(wallet, config)
        jwt = client._create_jwt()

        # JWT should have 3 parts
        parts = jwt.split('.')
        assert len(parts) == 3

    def test_jwt_creation_with_challenge(self, wallet, config):
        """Test JWT token creation with challenge."""
        from tunnel_client import HVYMTunnelClient
        import json
        import base64

        client = HVYMTunnelClient(wallet, config)
        challenge = "test_challenge_value_12345"
        jwt = client._create_jwt(challenge=challenge)

        # JWT should have 3 parts
        parts = jwt.split('.')
        assert len(parts) == 3

        # Decode payload and check challenge
        payload_b64 = parts[1]
        # Add padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += '=' * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        assert payload.get("challenge") == challenge

    def test_port_binding(self, wallet, config):
        """Test port binding."""
        from tunnel_client import HVYMTunnelClient

        client = HVYMTunnelClient(wallet, config)
        client.bind_port("pintheon", 9998)

        assert "pintheon" in client._port_bindings
        assert client._port_bindings["pintheon"] == 9998

    def test_unbind_port(self, wallet, config):
        """Test port unbinding."""
        from tunnel_client import HVYMTunnelClient

        client = HVYMTunnelClient(wallet, config)
        client.bind_port("pintheon", 9998)
        client.unbind_port("pintheon")

        assert "pintheon" not in client._port_bindings

    def test_build_endpoint_url(self, wallet, config):
        """Test endpoint URL building."""
        from tunnel_client import HVYMTunnelClient

        client = HVYMTunnelClient(wallet, config)
        url = client._build_endpoint_url()

        assert url.startswith("https://")
        assert client.stellar_address in url

    def test_state_change_callback(self, wallet, config):
        """Test state change callback."""
        from tunnel_client import HVYMTunnelClient, TunnelState

        client = HVYMTunnelClient(wallet, config)

        callback_states = []
        client.on_state_changed = lambda s: callback_states.append(s)

        client._set_state(TunnelState.CONNECTING)
        client._set_state(TunnelState.CONNECTED)

        assert len(callback_states) == 2
        assert callback_states[0] == TunnelState.CONNECTING
        assert callback_states[1] == TunnelState.CONNECTED

    @pytest.mark.asyncio
    async def test_disconnect(self, wallet, config):
        """Test disconnect."""
        from tunnel_client import HVYMTunnelClient, TunnelState

        client = HVYMTunnelClient(wallet, config)
        await client.disconnect()

        assert client.state == TunnelState.DISCONNECTED
        assert not client.is_connected


class TestTunnelEndpoint:
    """Test TunnelEndpoint dataclass."""

    def test_endpoint_creation(self):
        """Test endpoint creation."""
        from tunnel_client import TunnelEndpoint

        endpoint = TunnelEndpoint(
            url="https://GTEST123.tunnel.heavymeta.art",
            stellar_address="GTEST123",
            server_address="GSERVER456",
            services=["pintheon"]
        )

        assert endpoint.url == "https://GTEST123.tunnel.heavymeta.art"
        assert endpoint.stellar_address == "GTEST123"
        assert endpoint.server_address == "GSERVER456"
        assert endpoint.services == ["pintheon"]


class TestTunnelConfigStore:
    """Test TunnelConfigStore."""

    @pytest.fixture
    def mock_db(self):
        """Create mock TinyDB."""
        from tinydb import TinyDB
        from tinydb.storages import MemoryStorage
        return TinyDB(storage=MemoryStorage)

    def test_config_store_initialization(self, mock_db):
        """Test config store creates default config."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)
        config = store.get_config()

        assert 'server_url' in config
        assert 'server_address' in config
        assert 'services' in config

    def test_server_url_property(self, mock_db):
        """Test server_url property."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)

        assert store.server_url == TunnelConfigStore.DEFAULT_SERVER_URL

        store.server_url = "wss://custom.example.com/connect"
        assert store.server_url == "wss://custom.example.com/connect"

    def test_server_address_property(self, mock_db):
        """Test server_address property."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)

        assert store.server_address == ""

        store.server_address = "GSERVER123"
        assert store.server_address == "GSERVER123"

    def test_port_bindings(self, mock_db):
        """Test port bindings."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)

        # Default binding
        assert store.port_bindings.get("pintheon") == 9998

        # Add binding
        store.set_port_binding("ipfs", 8082)
        assert store.port_bindings.get("ipfs") == 8082

        # Remove binding
        store.remove_port_binding("ipfs")
        assert "ipfs" not in store.port_bindings

    def test_last_endpoint(self, mock_db):
        """Test last endpoint storage."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)

        assert store.get_last_endpoint() is None

        store.set_last_endpoint("https://GTEST.tunnel.heavymeta.art")
        assert store.get_last_endpoint() == "https://GTEST.tunnel.heavymeta.art"

        store.clear_last_endpoint()
        assert store.get_last_endpoint() is None

    def test_is_configured(self, mock_db):
        """Test is_configured check."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)

        # Not configured without server address
        assert not store.is_configured()

        # Configured with server address
        store.server_address = "GSERVER123"
        assert store.is_configured()

    def test_to_tunnel_config(self, mock_db):
        """Test conversion to TunnelConfig."""
        from tunnel_config import TunnelConfigStore

        store = TunnelConfigStore(mock_db)
        store.server_address = "GSERVER123"
        store.server_url = "wss://test.example.com/connect"

        tunnel_config = store.to_tunnel_config()

        assert tunnel_config.server_address == "GSERVER123"
        assert tunnel_config.server_url == "wss://test.example.com/connect"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
