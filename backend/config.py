"""Configuration management for Open Whisper."""

import json
import os
from typing import Dict, Any

CONFIG_FILE = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "model": "turbo",
    "language": "en",
    "live_volume_threshold": 0.02,
    "vad_filter": True,
    "vad_min_speech_duration_ms": 1500,
    "vad_min_silence_duration_ms": 900,
    "vad_max_speech_duration_s": 30,
    "live_transcribe": True,
    "silence_duration_ms": 1000,
    "max_chunk_duration_s": 10,  # Maximum duration before forcing transcription
    "threads": 0,  # 0 = auto-detect optimal thread count based on CPU
    "compute_type": "int8",  # int8 for speed, float16/float32 for higher accuracy
    "auto_paste": True  # Automatically paste transcribed text into active editor
}

def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or create default if not exists.
    
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def update_config(key: str, value: Any) -> None:
    """
    Update a single configuration value.
    
    Args:
        key: Configuration key to update
        value: New value for the configuration key
    """
    config = load_config()
    config[key] = value
    save_config(config)
