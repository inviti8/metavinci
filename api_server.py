"""
HEAVYMETADATA API Server

FastAPI + Uvicorn server running in a QThread for integration with the Metavinci PyQt5 application.
Provides local HTTP API endpoints for generating HEAVYMETA 3D asset metadata.

Can also run standalone for testing without PyQt5.
"""

import asyncio
import logging
import threading
from typing import Optional

# Try to import FastAPI first (needed for both modes)
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI/uvicorn not installed. API server will be disabled.")

# PyQt5 is only needed for the QThread-based worker (metavinci integration)
# Make it optional for standalone testing
try:
    from PyQt5.QtCore import QThread, pyqtSignal
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QThread = object  # Dummy base class for standalone mode
    pyqtSignal = lambda *args: None  # Dummy signal


class ApiServerWorker(QThread):
    """
    QThread worker that runs the FastAPI/Uvicorn server.

    Signals:
        started_signal: Emitted when server successfully starts
        stopped_signal: Emitted when server stops
        error_signal: Emitted with error message on failure
    """

    # Define signals only if PyQt5 is available
    if PYQT5_AVAILABLE:
        started_signal = pyqtSignal()
        stopped_signal = pyqtSignal()
        error_signal = pyqtSignal(str)

    def __init__(self, port: int = 7777, parent=None):
        """
        Initialize the API server worker.

        :param port: Port to bind the server to (default: 7777)
        :param parent: Parent QObject
        """
        if PYQT5_AVAILABLE:
            super().__init__(parent)
        else:
            super().__init__()
        self.port = port
        self.server: Optional[uvicorn.Server] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _emit_started(self):
        """Safely emit started signal if available."""
        if PYQT5_AVAILABLE and hasattr(self, 'started_signal'):
            self.started_signal.emit()

    def _emit_stopped(self):
        """Safely emit stopped signal if available."""
        if PYQT5_AVAILABLE and hasattr(self, 'stopped_signal'):
            self.stopped_signal.emit()

    def _emit_error(self, msg: str):
        """Safely emit error signal if available."""
        if PYQT5_AVAILABLE and hasattr(self, 'error_signal'):
            self.error_signal.emit(msg)

    @property
    def is_running(self) -> bool:
        """Check if server is currently running."""
        return self._running

    def run(self):
        """Main thread execution - starts the uvicorn server."""
        if not FASTAPI_AVAILABLE:
            self._emit_error("FastAPI/uvicorn not installed")
            return

        try:
            # Create FastAPI app
            app = create_api_app()

            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=self.port,
                log_level="warning",
                access_log=False,
            )

            self.server = uvicorn.Server(config)

            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._running = True
            self._emit_started()

            logging.info(f"HEAVYMETADATA API server starting on http://127.0.0.1:{self.port}")

            # Run the server
            self._loop.run_until_complete(self.server.serve())

        except OSError as e:
            if "address already in use" in str(e).lower() or e.errno == 10048:
                self._emit_error(f"Port {self.port} is already in use")
            else:
                self._emit_error(f"Server error: {str(e)}")
        except Exception as e:
            self._emit_error(f"Server error: {str(e)}")
        finally:
            self._running = False
            if self._loop:
                self._loop.close()
            self._emit_stopped()
            logging.info("HEAVYMETADATA API server stopped")

    def stop(self):
        """Request graceful server shutdown."""
        if self.server and self._running:
            self.server.should_exit = True
            logging.info("HEAVYMETADATA API server shutdown requested")

    def restart(self, new_port: Optional[int] = None):
        """
        Restart the server, optionally on a new port.

        :param new_port: New port to use (optional)
        """
        if new_port is not None:
            self.port = new_port
        self.stop()
        self.wait(5000)  # Wait up to 5 seconds for shutdown
        self.start()


def create_api_app() -> 'FastAPI':
    """
    Create and configure the FastAPI application.

    :returns: Configured FastAPI application instance
    """
    from api_routes import router

    app = FastAPI(
        title="HEAVYMETADATA API",
        description="Local API server for generating HEAVYMETA 3D asset metadata structures",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Localhost only, so allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        return {
            "service": "HEAVYMETADATA API",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "running"
        }

    return app


# For standalone testing
if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        app = create_api_app()
        uvicorn.run(app, host="127.0.0.1", port=7777)
    else:
        print("FastAPI/uvicorn not installed. Run: pip install fastapi uvicorn[standard]")
