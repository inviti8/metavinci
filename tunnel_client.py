"""
HVYM Tunnel Client - Native tunnel implementation for Metavinci.

Replaces Pinggy with Stellar-authenticated WebSocket tunneling.
"""

import asyncio
import json
import logging
import time
import httpx
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    import websockets
    from websockets import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older versions
        import websockets
        from websockets.client import WebSocketClientProtocol
        WEBSOCKETS_AVAILABLE = True
    except ImportError:
        WEBSOCKETS_AVAILABLE = False
        WebSocketClientProtocol = None

try:
    from hvym_stellar import Stellar25519KeyPair, StellarJWTToken
    HVYM_STELLAR_AVAILABLE = True
except ImportError:
    HVYM_STELLAR_AVAILABLE = False
    Stellar25519KeyPair = None
    StellarJWTToken = None


class TunnelState(Enum):
    """Tunnel connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class TunnelEndpoint:
    """Represents the public tunnel endpoint."""
    url: str                    # https://GADDR....tunnel.heavymeta.art
    stellar_address: str        # Client's Stellar address
    server_address: str         # Server's Stellar address
    services: List[str]         # Bound services


@dataclass
class TunnelConfig:
    """Tunnel configuration."""
    server_url: str = "wss://tunnel.heavymeta.art/connect"
    server_address: str = ""    # Server's Stellar address (for JWT audience)
    services: List[str] = None
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    reconnect_multiplier: float = 2.0
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    jwt_lifetime: int = 3600    # 1 hour
    local_pintheon_port: int = 9998

    def __post_init__(self):
        if self.services is None:
            self.services = ["pintheon"]


class HVYMTunnelClient:
    """
    Native HVYM tunnel client.

    Establishes authenticated WebSocket connection to HVYM Tunnler server
    using Stellar JWT tokens for authentication.

    Example:
        wallet = Stellar25519KeyPair(Keypair.from_secret("S..."))
        client = HVYMTunnelClient(wallet)

        # Set callbacks
        client.on_connected = lambda ep: print(f"Connected: {ep.url}")
        client.on_disconnected = lambda: print("Disconnected")

        # Connect (blocking)
        await client.connect()

        # Or connect in background
        asyncio.create_task(client.connect())
    """

    def __init__(
        self,
        wallet: 'Stellar25519KeyPair',
        config: TunnelConfig = None
    ):
        """
        Initialize tunnel client.

        Args:
            wallet: Stellar25519KeyPair for authentication
            config: Optional tunnel configuration
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library required: pip install websockets")
        if not HVYM_STELLAR_AVAILABLE:
            raise ImportError("hvym_stellar library required")

        self.wallet = wallet
        self.config = config or TunnelConfig()

        # Connection state
        self._state = TunnelState.DISCONNECTED
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._endpoint: Optional[TunnelEndpoint] = None
        self._reconnect_delay = self.config.reconnect_delay

        # Control flags
        self._should_reconnect = True
        self._stop_requested = False

        # Bound local ports
        self._port_bindings: Dict[str, int] = {}  # service_name -> local_port

        # Active streams for request/response
        self._streams: Dict[int, asyncio.Queue] = {}
        self._next_stream_id = 1

        # Callbacks
        self.on_state_changed: Optional[Callable[[TunnelState], None]] = None
        self.on_connected: Optional[Callable[[TunnelEndpoint], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_endpoint_ready: Optional[Callable[[str], None]] = None

        # Logger
        self._logger = logging.getLogger("HVYMTunnelClient")

    @property
    def state(self) -> TunnelState:
        """Get current tunnel state."""
        return self._state

    @property
    def endpoint(self) -> Optional[TunnelEndpoint]:
        """Get tunnel endpoint (if connected)."""
        return self._endpoint

    @property
    def stellar_address(self) -> str:
        """Get client's Stellar address."""
        return self.wallet.base_stellar_keypair().public_key

    @property
    def is_connected(self) -> bool:
        """Check if tunnel is connected."""
        return self._state == TunnelState.CONNECTED

    def _set_state(self, state: TunnelState):
        """Update state and notify callback."""
        old_state = self._state
        self._state = state
        self._logger.info(f"State changed: {old_state.value} -> {state.value}")
        if self.on_state_changed:
            try:
                self.on_state_changed(state)
            except Exception as e:
                self._logger.error(f"Error in state_changed callback: {e}")

    def _create_jwt(self, challenge: str = None) -> str:
        """Create Stellar-signed JWT for authentication.

        Args:
            challenge: Server challenge to bind to this JWT (replay protection)
        """
        # Build custom claims
        custom_claims = {}
        if challenge:
            custom_claims["challenge"] = challenge

        token = StellarJWTToken(
            keypair=self.wallet,
            audience=self.config.server_address,
            services=self.config.services,
            expires_in=self.config.jwt_lifetime,
            claims=custom_claims if custom_claims else None
        )
        return token.to_jwt()

    def _build_endpoint_url(self) -> str:
        """Build public endpoint URL from Stellar address."""
        # Extract domain from server URL
        domain = "tunnel.heavymeta.art"
        if "://" in self.config.server_url:
            parts = self.config.server_url.split("://")[1].split("/")[0]
            domain = parts
        return f"https://{self.stellar_address}.{domain}"

    async def connect(self):
        """
        Connect to tunnel server.

        This method runs the connection loop, handling reconnection
        automatically. Call disconnect() to stop.
        """
        self._stop_requested = False
        self._should_reconnect = True

        while not self._stop_requested:
            try:
                await self._connect_once()
            except Exception as e:
                self._logger.error(f"Connection error: {e}")
                self._set_state(TunnelState.ERROR)
                if self.on_error:
                    try:
                        self.on_error(str(e))
                    except Exception:
                        pass

            # Handle reconnection
            if self._should_reconnect and not self._stop_requested:
                self._set_state(TunnelState.RECONNECTING)
                self._logger.info(f"Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)

                # Exponential backoff
                self._reconnect_delay = min(
                    self._reconnect_delay * self.config.reconnect_multiplier,
                    self.config.max_reconnect_delay
                )
            else:
                break

        self._set_state(TunnelState.DISCONNECTED)
        if self.on_disconnected:
            try:
                self.on_disconnected()
            except Exception:
                pass

    async def _connect_once(self):
        """Establish single connection attempt."""
        self._set_state(TunnelState.CONNECTING)

        self._logger.info(f"Connecting to {self.config.server_url}")

        # Connect without auth header (challenge-response flow)
        async with websockets.connect(
            self.config.server_url,
            ping_interval=self.config.ping_interval,
            ping_timeout=self.config.ping_timeout,
            close_timeout=10
        ) as websocket:
            self._websocket = websocket
            self._set_state(TunnelState.AUTHENTICATING)

            # Wait for challenge from server
            challenge_msg = await asyncio.wait_for(
                websocket.recv(),
                timeout=30
            )
            challenge_data = json.loads(challenge_msg)

            if challenge_data.get("type") != "auth_challenge":
                error_msg = challenge_data.get('error', 'Expected auth_challenge')
                raise Exception(f"Unexpected message: {error_msg}")

            challenge_id = challenge_data.get("challenge_id")
            challenge_value = challenge_data.get("challenge")
            server_address = challenge_data.get("server_address")

            if not challenge_id or not challenge_value:
                raise Exception("Invalid challenge: missing challenge_id or challenge")

            # Update server address if provided
            if server_address and not self.config.server_address:
                self.config.server_address = server_address

            self._logger.debug(f"Received challenge: {challenge_id[:8]}...")

            # Create JWT with challenge bound
            jwt = self._create_jwt(challenge=challenge_value)

            # Send auth response
            await websocket.send(json.dumps({
                "type": "auth_response",
                "challenge_id": challenge_id,
                "jwt": jwt
            }))

            self._logger.debug("Sent auth response")

            # Wait for auth confirmation
            auth_response = await asyncio.wait_for(
                websocket.recv(),
                timeout=30
            )
            auth_data = json.loads(auth_response)

            if auth_data.get("type") == "auth_failed":
                error_msg = auth_data.get('error', 'Unknown')
                raise Exception(f"Authentication failed: {error_msg}")

            if auth_data.get("type") != "auth_ok":
                error_msg = auth_data.get('error', auth_data.get('reason', 'Unknown'))
                raise Exception(f"Unexpected response: {error_msg}")

            # Build endpoint info
            self._endpoint = TunnelEndpoint(
                url=auth_data.get("endpoint", self._build_endpoint_url()),
                stellar_address=self.stellar_address,
                server_address=auth_data.get("server_address", self.config.server_address),
                services=auth_data.get("services", self.config.services)
            )

            # Reset reconnect delay on successful connection
            self._reconnect_delay = self.config.reconnect_delay

            self._set_state(TunnelState.CONNECTED)
            self._logger.info(f"Connected! Endpoint: {self._endpoint.url}")

            if self.on_connected:
                try:
                    self.on_connected(self._endpoint)
                except Exception as e:
                    self._logger.error(f"Error in connected callback: {e}")

            if self.on_endpoint_ready:
                try:
                    self.on_endpoint_ready(self._endpoint.url)
                except Exception as e:
                    self._logger.error(f"Error in endpoint_ready callback: {e}")

            # Bind configured services
            for service, port in self._port_bindings.items():
                await self._send_bind(service, port)

            # Main message loop
            await self._message_loop(websocket)

    async def _message_loop(self, websocket: WebSocketClientProtocol):
        """Handle incoming messages."""
        try:
            async for message in websocket:
                await self._handle_message(message)
        except websockets.ConnectionClosed as e:
            self._logger.info(f"Connection closed: {e.code} {e.reason}")
        except Exception as e:
            self._logger.error(f"Message loop error: {e}")
            raise

    async def _handle_message(self, message: str):
        """Process incoming message from server."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ping":
                await self._websocket.send(json.dumps({"type": "pong"}))

            elif msg_type == "tunnel_request":
                # Forward request to local service
                await self._handle_tunnel_request(data)

            elif msg_type == "bind_ok":
                service = data.get("service")
                self._logger.info(f"Service bound: {service}")

            elif msg_type == "error":
                self._logger.error(f"Server error: {data.get('message')}")
                if self.on_error:
                    self.on_error(data.get("message", "Unknown server error"))

            else:
                self._logger.debug(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            self._logger.warning(f"Invalid JSON message: {message[:100]}")

    async def _handle_tunnel_request(self, data: dict):
        """Handle incoming tunnel request - forward to local service."""
        stream_id = data.get("stream_id")
        request = data.get("request", {})

        # Get the service from path or default to pintheon
        service = "pintheon"
        local_port = self._port_bindings.get(service, self.config.local_pintheon_port)

        try:
            # Forward request to local service
            response = await self._forward_to_local(local_port, request)

            # Send response back through tunnel
            await self._websocket.send(json.dumps({
                "type": "tunnel_response",
                "stream_id": stream_id,
                "response": response
            }))

        except Exception as e:
            self._logger.error(f"Error forwarding request: {e}")
            # Send error response
            await self._websocket.send(json.dumps({
                "type": "tunnel_response",
                "stream_id": stream_id,
                "response": {
                    "status_code": 502,
                    "headers": {"Content-Type": "text/plain"},
                    "body": f"Local service error: {e}"
                }
            }))

    async def _forward_to_local(self, port: int, request: dict) -> dict:
        """Forward HTTP request to local service."""
        method = request.get("method", "GET")
        path = request.get("path", "/")
        query_string = request.get("query_string", "")
        headers = request.get("headers", {})
        body = request.get("body", "")

        # Build URL
        url = f"http://127.0.0.1:{port}{path}"
        if query_string:
            url += f"?{query_string}"

        # Remove hop-by-hop headers
        hop_headers = [
            "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers",
            "transfer-encoding", "upgrade", "host"
        ]
        clean_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in hop_headers
        }

        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=clean_headers,
                content=body.encode() if body else None
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

    async def _send_bind(self, service: str, local_port: int):
        """Send bind request to server."""
        if not self._websocket:
            return

        message = {
            "type": "bind",
            "service": service,
            "local_port": local_port
        }
        await self._websocket.send(json.dumps(message))
        self._logger.info(f"Binding {service} -> localhost:{local_port}")

    def bind_port(self, service: str, local_port: int):
        """
        Bind a local port to a service name.

        Args:
            service: Service name (e.g., "pintheon")
            local_port: Local port to expose
        """
        self._port_bindings[service] = local_port

        # If already connected, send bind immediately
        if self.is_connected and self._websocket:
            asyncio.create_task(self._send_bind(service, local_port))

    def unbind_port(self, service: str):
        """Unbind a service."""
        if service in self._port_bindings:
            del self._port_bindings[service]

    async def disconnect(self):
        """Disconnect from tunnel server."""
        self._stop_requested = True
        self._should_reconnect = False

        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        self._endpoint = None
        self._set_state(TunnelState.DISCONNECTED)

    def disconnect_sync(self):
        """Synchronous disconnect (for use from Qt thread)."""
        self._stop_requested = True
        self._should_reconnect = False

        if self._websocket:
            try:
                # Try to get current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule close on event loop
                    asyncio.run_coroutine_threadsafe(
                        self._websocket.close(),
                        loop
                    )
                else:
                    # Run close directly
                    loop.run_until_complete(self._websocket.close())
            except Exception:
                pass
