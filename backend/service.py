"""Transcription service for real-time speech-to-text processing."""

import threading
import queue
import time
import numpy as np
import sounddevice as sd
import sys
import site
import os
from datetime import datetime
from collections import deque
from typing import Dict, List, Any, Optional, Tuple
from pynput import keyboard
import pyperclip
import pyautogui

# Workaround for broken whisper-ctranslate2 package structure
# It installs into site-packages/src/whisper_ctranslate2 instead of site-packages/whisper_ctranslate2
for site_package in site.getsitepackages():
    src_path = os.path.join(site_package, "src")
    if os.path.exists(os.path.join(src_path, "whisper_ctranslate2")):
        sys.path.append(src_path)
        break

from whisper_ctranslate2.transcribe import Transcribe, TranscriptionOptions
from .config import load_config
from .constants import (
    BLOCK_SIZE_MS,
    SAMPLE_RATE,
    VOCAL_FREQ_MIN,
    VOCAL_FREQ_MAX,
    MAX_QUEUE_SIZE,
    VOLUME_QUEUE_MAXSIZE,
    QUEUE_HISTORY_SIZE,
    MAX_QUEUE_ITEMS_MEMORY,
    KEEP_COMPLETED_ITEMS,
    CLIPBOARD_DELAY
)

class TranscriptionService:
    """Service for managing real-time speech transcription with voice activity detection."""
    
    def __init__(self) -> None:
        """Initialize the transcription service with default configuration."""
        self.config: Dict[str, Any] = load_config()
        self.running: bool = False
        self.listening: bool = False  # Default to not recording
        self.manual_recording: bool = False  # Track if manually recording (F9 mode)
        
        # Communication queues
        self.queue: queue.Queue = queue.Queue()  # WebSocket queue (high priority: text, status)
        self.volume_queue: queue.Queue = queue.Queue(maxsize=VOLUME_QUEUE_MAXSIZE)  # Low priority: volume updates
        self.audio_queue: queue.Queue = queue.Queue()  # Audio buffer queue
        
        # Threading
        self.thread: Optional[threading.Thread] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.hotkey_listener: Optional[keyboard.Listener] = None
        
        # Transcription model
        self.transcribe_model: Optional[Transcribe] = None

        # Voice detection state
        self.waiting: int = 0
        self.prevblock: np.ndarray = np.zeros((0, 1))
        self.buffer: np.ndarray = np.zeros((0, 1))
        self.speaking: bool = False
        self.blocks_speaking: int = 0

        # Queue metadata tracking
        self.queue_item_counter: int = 0
        self.queue_items: Dict[int, Dict[str, Any]] = {}
        self.processing_stats: Dict[str, Any] = {
            'total_processed': 0,
            'total_processing_time': 0.0,
            'items_dropped': 0
        }
        self.processing_history: deque = deque(maxlen=QUEUE_HISTORY_SIZE)

        # Transcripts for hotkey paste
        self.transcripts: List[str] = []
        
    def start(self) -> None:
        """Start the transcription service with all threads and listeners."""
        if self.running:
            return
        self.running = True
        self.config = load_config()  # Reload config on start

        # Start audio capture thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        # Start transcription worker thread
        self.worker_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.worker_thread.start()

        # Start global hotkey listener
        self._start_hotkey_listener()
        
    def stop(self) -> None:
        """Stop the transcription service and clean up all resources."""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.worker_thread:
            self.worker_thread.join()
        if self.hotkey_listener:
            self.hotkey_listener.stop()

    def _start_hotkey_listener(self):
        """Start global hotkey listener for Cmd+Shift+V, Cmd+R, and F9"""
        def on_paste():
            """Paste transcripts when hotkey is pressed"""
            if self.transcripts:
                text = '\n'.join(self.transcripts)
                pyperclip.copy(text)
                time.sleep(0.1)
                # Cmd+V on macOS
                pyautogui.hotkey('command', 'v')

        def on_toggle_recording():
            """Toggle recording when hotkey is pressed"""
            self.listening = not self.listening
            self.manual_recording = self.listening  # Track manual recording mode
            
            status = "Recording started" if self.listening else "Recording stopped"
            print(f"[Hotkey] {status} (Manual mode)")
            
            # Show macOS notification
            import subprocess
            if self.listening:
                # Clear buffer when starting manual recording
                self.buffer = np.zeros((0, 1))
                subprocess.run([
                    'osascript', '-e',
                    'display notification "Press Cmd+R or F9 to stop" with title "🎤 Recording Started" sound name "Tink"'
                ])
            else:
                # Process the entire recording when stopping
                if len(self.buffer) > 0:
                    self._save_to_process()
                
                subtitle = f"Processing recording..." if len(self.buffer) > 0 else "No audio recorded"
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{subtitle}" with title "⏹️ Recording Stopped" sound name "Tink"'
                ])

        # Create hotkeys
        paste_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<cmd>+<shift>+v'),
            on_paste
        )

        record_hotkey_cmdr = keyboard.HotKey(
            keyboard.HotKey.parse('<cmd>+r'),
            on_toggle_recording
        )

        record_hotkey_f9 = keyboard.HotKey(
            keyboard.HotKey.parse('<f9>'),
            on_toggle_recording
        )

        def for_canonical(paste_fn, record_cmdr_fn, record_f9_fn):
            def handler(key):
                paste_fn(key)
                record_cmdr_fn(key)
                record_f9_fn(key)
            return handler

        hotkey_listener = keyboard.Listener(
            on_press=for_canonical(paste_hotkey.press, record_hotkey_cmdr.press, record_hotkey_f9.press),
            on_release=for_canonical(paste_hotkey.release, record_hotkey_cmdr.release, record_hotkey_f9.release)
        )

        hotkey_listener.start()
        self.hotkey_listener = hotkey_listener
        print("Global hotkeys registered:")
        print("  Cmd+Shift+V - Paste transcripts")
        print("  Cmd+R - Toggle recording (auto-copies on stop)")
        print("  F9 - Toggle recording (auto-copies on stop)")
            
    def _is_there_voice(self, indata: np.ndarray, frames: int, sample_rate: int) -> bool:
        """
        Detect if voice is present in audio data using frequency and volume analysis.
        
        Args:
            indata: Audio data array
            frames: Number of frames in the audio data
            sample_rate: Audio sample rate in Hz
            
        Returns:
            True if voice is detected, False otherwise
        """
        freq = (
            np.argmax(np.abs(np.fft.rfft(indata[:, 0])))
            * sample_rate
            / frames
        )
        volume = np.sqrt(np.mean(indata**2))
        return (volume > self.config.get("live_volume_threshold", 0.02) and 
                VOCAL_FREQ_MIN <= freq <= VOCAL_FREQ_MAX)

    def _save_to_process(self) -> None:
        """Save current audio buffer to processing queue and reset state."""
        buffer_copy = self.buffer.copy()
        item_id = self.queue_item_counter
        self.queue_item_counter += 1

        # Track queue item metadata
        self.queue_items[item_id] = {
            'id': item_id,
            'timestamp': datetime.now().isoformat(),
            'buffer_size': len(buffer_copy),
            'duration_seconds': len(buffer_copy) / SAMPLE_RATE,
            'status': 'queued'
        }

        self.audio_queue.put((item_id, buffer_copy))
        self.buffer = np.zeros((0, 1))
        self.speaking = False

        # Notify queue size increase and send detailed queue info
        self._send_queue_update()

    def _callback(self, indata: np.ndarray, frames: int, _time: Any, status: Any) -> None:
        """
        Audio callback for processing incoming audio data.
        
        Args:
            indata: Audio data array
            frames: Number of frames
            _time: Time information (unused)
            status: Status information (unused)
        """
        if not self.listening:
            return

        if not any(indata):
            return

        volume = np.sqrt(np.mean(indata**2))

        # Send volume update to low-priority queue (drop if full to avoid backlog)
        try:
            self.volume_queue.put_nowait({"volume": float(volume)})
        except queue.Full:
            pass  # Drop volume update if queue is full

        # Manual recording mode: accumulate all audio without VAD chunking
        if self.manual_recording:
            self.buffer = np.concatenate((self.buffer, indata))
            self.prevblock = indata  # Keep track of previous block
            return  # Don't process until user manually stops

        # Automatic VAD mode (original behavior)
        voice = self._is_there_voice(indata, frames, SAMPLE_RATE)

        if not voice and not self.speaking:
            return

        if voice:
            if self.waiting < 1:
                self.buffer = self.prevblock.copy()

            self.buffer = np.concatenate((self.buffer, indata))
            
            # Calculate EndBlocks dynamically based on config
            silence_ms = self.config.get("silence_duration_ms", 1000)
            self.waiting = int(silence_ms / BLOCK_SIZE_MS)

            if not self.speaking:
                # Calculate FlushBlocks dynamically from config
                max_chunk_s = self.config.get("max_chunk_duration_s", 10)
                self.blocks_speaking = int((max_chunk_s * 1000) / BLOCK_SIZE_MS)

            self.speaking = True
        else:
            self.waiting -= 1
            if self.waiting < 1:
                self._save_to_process()
                return
            else:
                self.buffer = np.concatenate((self.buffer, indata))

        self.blocks_speaking -= 1
        if self.blocks_speaking < 1:
            self._save_to_process()

    def _auto_paste(self, text: str) -> None:
        """
        Automatically paste transcribed text to active editor.
        
        Args:
            text: The text to paste
        """
        try:
            # Copy to clipboard
            pyperclip.copy(text)
            time.sleep(CLIPBOARD_DELAY)  # Brief delay to ensure clipboard is ready
            # Paste using Cmd+V on macOS
            pyautogui.hotkey('command', 'v')
            print(f"[Auto-paste] Pasted: {text[:50]}{'...' if len(text) > 50 else ''}")
        except Exception as e:
            print(f"[Auto-paste] Error: {e}")

    def _send_queue_update(self) -> None:
        """Send detailed queue status update via WebSocket."""
        queued_items = [item for item in self.queue_items.values() if item['status'] == 'queued']
        processing_items = [item for item in self.queue_items.values() if item['status'] == 'processing']

        avg_processing_time = 0
        if self.processing_stats['total_processed'] > 0:
            avg_processing_time = self.processing_stats['total_processing_time'] / self.processing_stats['total_processed']

        self.queue.put({
            'queue_size': len(queued_items),
            'queue_details': {
                'queued_items': queued_items,
                'processing_items': processing_items,
                'stats': {
                    'total_processed': self.processing_stats['total_processed'],
                    'avg_processing_time': round(avg_processing_time, 2),
                    'items_dropped': self.processing_stats['items_dropped']
                },
                'processing_history': list(self.processing_history)
            }
        })

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status for API endpoint.
        
        Returns:
            Dictionary containing queue size, items, and statistics
        """
        queued_items = [item for item in self.queue_items.values() if item['status'] == 'queued']
        processing_items = [item for item in self.queue_items.values() if item['status'] == 'processing']

        avg_processing_time = 0
        if self.processing_stats['total_processed'] > 0:
            avg_processing_time = self.processing_stats['total_processing_time'] / self.processing_stats['total_processed']

        return {
            'queue_size': len(queued_items),
            'queued_items': queued_items,
            'processing_items': processing_items,
            'stats': {
                'total_processed': self.processing_stats['total_processed'],
                'avg_processing_time': round(avg_processing_time, 2),
                'items_dropped': self.processing_stats['items_dropped']
            },
            'processing_history': list(self.processing_history)
        }

    def _transcription_worker(self) -> None:
        """Worker thread for processing audio transcription queue."""
        while self.running:
            item_id = None
            try:
                # Check queue size to prevent infinite backlog
                qsize = self.audio_queue.qsize()
                if qsize > 5:
                    print(f"Warning: Transcription queue backlog: {qsize} items")

                if qsize > MAX_QUEUE_SIZE:
                    print("Error: Queue too large, dropping old items to catch up")
                    # Drop items until we have 5 left to avoid clearing everything
                    items_to_drop = qsize - QUEUE_WARNING_THRESHOLD
                    for _ in range(items_to_drop):
                        try:
                            dropped_item_id, _ = self.audio_queue.get_nowait()
                            if dropped_item_id in self.queue_items:
                                self.queue_items[dropped_item_id]['status'] = 'dropped'
                                self.processing_stats['items_dropped'] += 1
                        except queue.Empty:
                            break
                    self._send_queue_update()

                # Wait for audio buffer with timeout to check self.running
                item_id, _buffer = self.audio_queue.get(timeout=1)

                # Update item status to processing
                if item_id in self.queue_items:
                    self.queue_items[item_id]['status'] = 'processing'
                    self.queue_items[item_id]['processing_start'] = datetime.now().isoformat()

                # Notify frontend of status and send queue update
                self.queue.put({"status": "Transcribing..."})
                self._send_queue_update()

            except queue.Empty:
                continue
            
            if not self.transcribe_model:
                # Initialize model
                # Auto-detect optimal thread count if not specified
                threads = self.config.get("threads", 0)
                if threads == 0:
                    threads = os.cpu_count() or 4  # Fallback to 4 if detection fails
                
                compute_type = self.config.get("compute_type", "int8")
                
                print(f"Initializing Whisper model: {self.config.get('model', 'turbo')}")
                print(f"  Threads: {threads}")
                print(f"  Compute type: {compute_type}")
                
                self.transcribe_model = Transcribe(
                    model_path=self.config.get("model", "turbo"),
                    device="auto",
                    device_index=0,
                    compute_type=compute_type,
                    threads=threads,
                    cache_directory=None,
                    local_files_only=False,
                    batched=False
                )

            options = TranscriptionOptions(
                beam_size=5,
                best_of=5,
                patience=1,
                length_penalty=1,
                repetition_penalty=1,
                no_repeat_ngram_size=0,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4,
                condition_on_previous_text=True,
                prompt_reset_on_temperature=0.5,
                initial_prompt=None,
                prefix=None,
                suppress_blank=True,
                suppress_tokens=[-1],
                word_timestamps=False,
                prepend_punctuations="\"'“¿([{-",
                append_punctuations="\"'.。,，!！?？:：”)]}、",
                temperature=0.0,
                hotwords=None,
                print_colors=False,
                hallucination_silence_threshold=None,
                vad_threshold=None,
                multilingual=False,
                vad_filter=self.config.get("vad_filter", True),
                vad_min_speech_duration_ms=self.config.get("vad_min_speech_duration_ms", 1500),
                vad_max_speech_duration_s=self.config.get("vad_max_speech_duration_s", 30),
                vad_min_silence_duration_ms=self.config.get("vad_min_silence_duration_ms", 500),
            )

            # Track processing time
            processing_start_time = time.time()

            try:
                result = self.transcribe_model.inference(
                    audio=_buffer.flatten().astype("float32"),
                    task="transcribe",
                    language=self.config.get("language", "en"),
                    verbose=False,
                    live=False, # Changed to False to force immediate transcription
                    options=options,
                )

                processing_time = time.time() - processing_start_time

                # Update processing stats
                if item_id is not None and item_id in self.queue_items:
                    self.queue_items[item_id]['status'] = 'completed'
                    self.queue_items[item_id]['processing_time'] = round(processing_time, 2)
                    self.queue_items[item_id]['processing_end'] = datetime.now().isoformat()

                    # Add to processing history
                    self.processing_history.append({
                        'id': item_id,
                        'timestamp': self.queue_items[item_id]['timestamp'],
                        'processing_time': round(processing_time, 2),
                        'text_length': len(result['text'].strip()) if result['text'].strip() else 0
                    })

                    # Update stats
                    self.processing_stats['total_processed'] += 1
                    self.processing_stats['total_processing_time'] += processing_time

                    # Clean up old completed items
                    if len(self.queue_items) > MAX_QUEUE_ITEMS_MEMORY:
                        completed_ids = [k for k, v in self.queue_items.items() if v['status'] == 'completed']
                        completed_ids.sort()
                        for old_id in completed_ids[:-KEEP_COMPLETED_ITEMS]:
                            del self.queue_items[old_id]

                if result['text'].strip():
                    text = result['text'].strip()
                    self.queue.put({"text": text})
                    # Add to transcripts for hotkey paste
                    self.transcripts.append(text)
                    
                    # Auto-paste if enabled
                    if self.config.get("auto_paste", True):
                        self._auto_paste(text)

                # Send queue update after completion
                self._send_queue_update()

            except Exception as e:
                print(f"Error during transcription: {e}")
                if item_id is not None and item_id in self.queue_items:
                    self.queue_items[item_id]['status'] = 'error'
                    self.queue_items[item_id]['error'] = str(e)
                    self._send_queue_update()

    def _run_loop(self) -> None:
        """Main audio capture loop that runs in a separate thread."""
        block_size = int(SAMPLE_RATE * BLOCK_SIZE_MS / 1000)
        
        with sd.InputStream(
            channels=1,
            callback=self._callback,
            blocksize=block_size,
            samplerate=SAMPLE_RATE,
        ):
            while self.running:
                time.sleep(0.1)
