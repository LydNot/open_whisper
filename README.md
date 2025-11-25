# Open Whisper 🎤

**Real-time speech-to-text desktop application powered by OpenAI Whisper.**

100% local, private, and free forever. No cloud dependencies, no subscriptions.

## ✨ Features

- 🎙️ **Real-time transcription** with Voice Activity Detection (VAD)
- ⌨️ **Global keyboard shortcuts** (work anywhere, even when app is hidden)
- 📋 **Auto-paste to editor** - transcripts automatically appear where you're typing
- 📝 **Auto-save transcripts** - separate JSONL files for each transcription
- 📊 **Queue monitoring** with detailed metrics and processing stats
- 📈 **Live audio visualizer** with configurable threshold indicator
- 🎯 **File drag-and-drop** - transcribe existing audio files (MP3, WAV, M4A, etc.)
- ⚙️ **Fully configurable** - model, language, thresholds, and behavior

## Quick Start

```bash
# Install dependencies
uv sync

# Start the desktop app
./start_desktop.sh
```

The app opens in a native-looking PyWebView window with:
- 🖥️ Self-contained desktop window
- 🎯 All features in one place
- 🔄 Real-time transcription interface
- ⚙️ Built-in settings panel

## Global Keyboard Shortcuts

Work anywhere on your Mac, even when the app is in the background:

| Shortcut | Action |
|----------|--------|
| `Cmd+R` | **Toggle recording** on/off<br>Auto-copies transcript to clipboard when stopping |
| `Cmd+Shift+R` | **Toggle recording** (alternative hotkey) |
| `Cmd+Shift+V` | **Paste transcripts** at cursor location |

**Setup Required:** See [ACCESSIBILITY.md](ACCESSIBILITY.md) for permission setup (2-minute one-time setup).

## How to Use

1. **Start the app** - Desktop window opens automatically
2. **Grant microphone permission** when prompted
3. **Setup accessibility permissions** - See [ACCESSIBILITY.md](ACCESSIBILITY.md) for 2-minute setup
4. **Start recording:**
   - Click the microphone button in the app, OR
   - Press `Cmd+R` anywhere (works globally!)
5. **Speak naturally** - transcription appears after brief pauses
6. **Stop recording:**
   - Press `Cmd+R` again (auto-copies to clipboard!)
   - OR click microphone button
7. **Auto-paste:** Transcripts automatically paste into your active editor
8. **Manual paste:** Press `Cmd+Shift+V` anytime

## Usage Tips

- **Background recording:** Minimize the window and use `Cmd+R` to record from anywhere
- **Auto-paste mode:** Enable in Settings to automatically paste transcriptions
- **Drag & drop files:** Drop audio files directly into the window to transcribe them
- **Queue monitoring:** Watch the queue sidebar for processing status

## Configuration

Edit `config.json` or use Settings panel in the app:

- **Model**: `tiny`, `base`, `small`, `medium`, `large-v2`, `turbo`
- **Language**: `en`, `es`, `fr`, etc.
- **Volume Threshold**: Adjust microphone sensitivity
- **Silence Duration**: How long to wait before processing speech

## Troubleshooting

### "This process is not trusted!" error

You need to grant Accessibility permissions. See [ACCESSIBILITY.md](ACCESSIBILITY.md) for detailed setup.

**Quick fix:**
1. System Settings → Privacy & Security → Accessibility
2. Add **Terminal** (or iTerm)
3. Add **Python** (from your `.venv` folder)
4. Restart the app

### Hotkeys don't work

Make sure:
- ✅ Accessibility permissions granted (both Terminal AND Python)
- ✅ App is running (check for Open Whisper window or process)
- ✅ Mac has been restarted after granting permissions

### No transcripts appearing

- Check microphone is selected in Settings
- Adjust volume threshold (Settings panel)
- Ensure you're speaking loud enough
- Try a faster model (`base` instead of `turbo`)

## Technical Details

- **Backend**: FastAPI + Python
- **Frontend**: HTML/CSS/JavaScript  
- **Desktop**: PyWebView for native-looking window
- **Transcription**: whisper-ctranslate2 (optimized Whisper)
- **Audio**: sounddevice + numpy
- **Hotkeys**: pynput (global keyboard shortcuts)

## 📁 Project Structure

```
├── start_desktop.sh      # Launch script
├── main_desktop.py       # Desktop app entry point
├── config.json           # Your settings (auto-generated)
├── ACCESSIBILITY.md      # Accessibility permissions setup guide
├── CHANGELOG.md          # Version history and improvements
├── backend/
│   ├── app.py           # FastAPI server with API endpoints
│   ├── service.py       # Core transcription service
│   ├── config.py        # Configuration management
│   ├── constants.py     # Application constants
│   └── static/          # Web interface (HTML/CSS/JS)
└── transcripts/         # Saved transcripts (auto-generated JSONL files)
```

## 🏗️ Code Quality

- ✅ Full type hints throughout the codebase
- ✅ Comprehensive docstrings for all functions
- ✅ Centralized constants (no magic numbers)
- ✅ Clean separation of concerns
- ✅ Well-documented API endpoints
- ✅ Zero linter errors

## License

MIT

---

**Made with ❤️ using [Claude Code](https://claude.com/claude-code)**
