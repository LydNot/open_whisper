"""Constants used across the Open Whisper application."""

# Audio processing constants
BLOCK_SIZE_MS = 30  # milliseconds per audio block
SAMPLE_RATE = 16000  # Hz - Default sample rate for Whisper
VOCAL_FREQ_MIN = 50  # Hz - Minimum human vocal frequency
VOCAL_FREQ_MAX = 1000  # Hz - Maximum frequency for voice detection

# Queue management
MAX_QUEUE_SIZE = 10  # Maximum items in queue before dropping old items
QUEUE_WARNING_THRESHOLD = 5  # Show warning when queue exceeds this
QUEUE_HISTORY_SIZE = 50  # Number of processing events to keep in history
MAX_QUEUE_ITEMS_MEMORY = 100  # Maximum queue items to keep in memory
KEEP_COMPLETED_ITEMS = 50  # Number of completed items to retain

# WebSocket queue sizes
VOLUME_QUEUE_MAXSIZE = 5  # Maximum volume updates to queue (drop if full)

# Volume visualization scaling
VOLUME_SCALE_FACTOR = 500  # Multiplier for volume visualization

# Server configuration
DEFAULT_SERVER_PORT = 8000

# Paste operation timing
CLIPBOARD_DELAY = 0.1  # seconds to wait after copying to clipboard



