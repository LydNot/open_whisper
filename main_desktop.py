"""Open Whisper desktop application using PyWebView."""

import webview
import threading
import uvicorn
import time
from backend.app import app
from backend.constants import DEFAULT_SERVER_PORT

def start_server() -> None:
    """Start the FastAPI server in a background thread."""
    uvicorn.run(app, host="localhost", port=DEFAULT_SERVER_PORT, log_level="error")

if __name__ == '__main__':
    # Start FastAPI backend in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(1)

    # Create desktop window with PyWebView
    webview.create_window(
        'Open Whisper',
        f'http://localhost:{DEFAULT_SERVER_PORT}',
        width=800,
        height=600
    )
    webview.start()
