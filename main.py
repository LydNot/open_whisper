"""Open Whisper menu bar application using rumps."""

import threading
import uvicorn
import time
import rumps
import webbrowser
import os
import sys
from typing import Optional
from backend.app import app as fastapi_app, service
from backend.constants import DEFAULT_SERVER_PORT

def start_server() -> None:
    """Start the FastAPI server in a background thread."""
    uvicorn.run(fastapi_app, host="localhost", port=DEFAULT_SERVER_PORT, log_level="error")

class OpenWhisperApp(rumps.App):
    """macOS menu bar application for Open Whisper."""
    
    def __init__(self) -> None:
        """Initialize the menu bar application."""
        super(OpenWhisperApp, self).__init__("🎤", quit_button=None)

        self.server_thread: Optional[threading.Thread] = None
        self.window_opened: bool = False
        self.is_recording: bool = False

        # Menu items
        self.menu = [
            rumps.MenuItem("Open Window", callback=self.open_window),
            rumps.separator,
            rumps.MenuItem("Toggle Recording (⌘R or ⌘⇧R)", callback=None),
            rumps.MenuItem("Paste Transcripts (⌘⇧V)", callback=self.paste_transcripts),
            rumps.separator,
            rumps.MenuItem("Quit Open Whisper", callback=self.quit_app)
        ]
    
    def start_backend(self) -> None:
        """Start FastAPI server in background thread."""
        self.server_thread = threading.Thread(target=start_server, daemon=True)
        self.server_thread.start()
        time.sleep(1)  # Wait for server to start

    def open_window(self, _: rumps.MenuItem) -> None:
        """Open the interface in default browser."""
        webbrowser.open(f'http://localhost:{DEFAULT_SERVER_PORT}')
        self.window_opened = True

    def paste_transcripts(self, _: rumps.MenuItem) -> None:
        """Manually trigger paste (same as Cmd+Shift+V)."""
        if service.transcripts:
            import pyperclip
            import pyautogui
            text = '\n'.join(service.transcripts)
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('command', 'v')
        else:
            rumps.notification(
                title="Open Whisper",
                subtitle="No transcripts yet",
                message="Start speaking to create transcripts"
            )

    def quit_app(self, _: rumps.MenuItem) -> None:
        """Quit the application."""
        rumps.quit_application()

def check_single_instance() -> None:
    """Ensure only one instance of Open Whisper is running."""
    pid_file = os.path.expanduser('~/.open_whisper.pid')
    
    # Check if PID file exists
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                print(f"Open Whisper is already running (PID: {old_pid})")
                print("Opening window...")
                webbrowser.open(f'http://localhost:{DEFAULT_SERVER_PORT}')
                sys.exit(0)
            except OSError:
                # Process is not running, remove stale PID file
                os.remove(pid_file)
        except (ValueError, FileNotFoundError):
            pass
    
    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Register cleanup on exit
    import atexit
    atexit.register(lambda: os.path.exists(pid_file) and os.remove(pid_file))

if __name__ == '__main__':
    check_single_instance()
    app = OpenWhisperApp()
    app.start_backend()
    app.run()
