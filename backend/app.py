"""FastAPI application for Open Whisper transcription service."""

from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import json
import pyautogui
import pyperclip
import time
import os
import tempfile
import numpy as np
from datetime import datetime
from .service import TranscriptionService
from .config import load_config, update_config
from .constants import DEFAULT_SERVER_PORT, CLIPBOARD_DELAY

app = FastAPI(title="Open Whisper", description="Real-time speech transcription service")

class PasteRequest(BaseModel):
    """Request model for pasting text."""
    text: str

class SaveRequest(BaseModel):
    """Request model for saving transcripts."""
    transcripts: List[Dict[str, str]]

class ConfigUpdate(BaseModel):
    """Request model for updating configuration."""
    key: str
    value: str | int | float | bool

@app.post("/paste")
async def paste_to_cursor(request: PasteRequest) -> Dict[str, str]:
    """
    Paste text to the active cursor location.
    
    Args:
        request: PasteRequest containing the text to paste
        
    Returns:
        Status message
    """
    pyperclip.copy(request.text)
    time.sleep(CLIPBOARD_DELAY)  # Ensure clipboard is ready
    pyautogui.hotkey('command', 'v')  # macOS paste command
    return {"status": "pasted"}

@app.post("/toggle_listening")
async def toggle_listening() -> Dict[str, bool]:
    """
    Toggle the listening state of the transcription service.
    
    Returns:
        Current listening state
    """
    service.listening = not service.listening
    service.manual_recording = service.listening  # Enable manual mode for web UI too
    
    if service.listening:
        # Clear buffer when starting manual recording
        service.buffer = np.zeros((0, 1))
    else:
        # Process the entire recording when stopping
        if len(service.buffer) > 0:
            service._save_to_process()
    
    return {"listening": service.listening}

@app.post("/save_transcript")
async def save_transcript(request: SaveRequest) -> Dict[str, str]:
    """
    Save transcripts to a JSONL file.
    
    Args:
        request: SaveRequest containing list of transcripts
        
    Returns:
        Path to the saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"transcript-{timestamp}.jsonl"
    
    # Create transcripts directory if it doesn't exist
    save_dir = os.path.join(os.getcwd(), "transcripts")
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        for t in request.transcripts:
            f.write(json.dumps(t) + "\n")
            
    return {"path": filepath}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("backend/static/index.html")

service = TranscriptionService()

@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the transcription service on startup."""
    service.start()

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up the transcription service on shutdown."""
    service.stop()

@app.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns:
        Configuration dictionary
    """
    return load_config()

@app.post("/config")
async def set_config(update: ConfigUpdate) -> Dict[str, str]:
    """
    Update configuration setting.
    
    Args:
        update: ConfigUpdate containing key and value
        
    Returns:
        Status message
    """
    update_config(update.key, update.value)
    # Restart service to apply changes
    service.stop()
    service.start()
    return {"status": "updated"}

@app.get("/queue_status")
async def get_queue_status() -> Dict[str, Any]:
    """
    Get current transcription queue status.
    
    Returns:
        Queue status including size, items, and statistics
    """
    return service.get_queue_status()

@app.post("/transcribe_file")
async def transcribe_file(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Transcribe an uploaded audio file.
    
    Args:
        file: Audio file to transcribe
        
    Returns:
        Transcribed text and filename
        
    Raises:
        Exception: If transcription fails
    """
    """Transcribe an uploaded audio file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Use the transcription model to transcribe the file
        if not service.transcribe_model:
            from whisper_ctranslate2.transcribe import Transcribe, TranscriptionOptions
            
            # Auto-detect optimal thread count if not specified
            threads = service.config.get("threads", 0)
            if threads == 0:
                import os
                threads = os.cpu_count() or 4  # Fallback to 4 if detection fails
            
            compute_type = service.config.get("compute_type", "int8")
            
            service.transcribe_model = Transcribe(
                model_path=service.config.get("model", "turbo"),
                device="auto",
                device_index=0,
                compute_type=compute_type,
                threads=threads,
                cache_directory=None,
                local_files_only=False,
                batched=False
            )

        from whisper_ctranslate2.transcribe import TranscriptionOptions
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
            temperature=0.0,
            hotwords=None,
            print_colors=False,
            hallucination_silence_threshold=None,
            vad_threshold=None,
            multilingual=False,
            vad_filter=service.config.get("vad_filter", True),
            vad_min_speech_duration_ms=service.config.get("vad_min_speech_duration_ms", 1500),
            vad_max_speech_duration_s=service.config.get("vad_max_speech_duration_s", 30),
            vad_min_silence_duration_ms=service.config.get("vad_min_silence_duration_ms", 500),
        )

        # Transcribe the file
        result = service.transcribe_model.inference(
            audio=tmp_path,
            task="transcribe",
            language=service.config.get("language", "en"),
            verbose=False,
            live=False,
            options=options,
        )

        # Clean up temp file
        os.unlink(tmp_path)

        return {"text": result['text'].strip(), "filename": file.filename}

    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise Exception(f"Error transcribing file: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time updates.
    
    Sends transcription results, volume levels, and queue status to clients.
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    try:
        while True:
            # Priority 1: Check high-priority queue (text, status, queue updates)
            if not service.queue.empty():
                data = service.queue.get()
                await websocket.send_json(data)
            # Priority 2: Check volume queue only if main queue is empty
            elif not service.volume_queue.empty():
                data = service.volume_queue.get()
                await websocket.send_json(data)
            else:
                await asyncio.sleep(0.01)  # Reduced sleep time for better responsiveness
    except WebSocketDisconnect:
        pass
