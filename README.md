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

## Two Versions Available

### 📍 Menu Bar Version (Default)
Lives in your macOS menu bar - always accessible!

```bash
./start_app.sh
```

- Microphone icon (🎤) in menu bar (top right)
- Opens interface in your default browser
- Stays out of the way - no Dock icon
- Perfect for background use

### 🖥️ Desktop Window Version
Traditional desktop app with native-looking window.

```bash
./start_desktop.sh
```

- PyWebView desktop window
- Appears in Dock
- Self-contained window
- Feels like a native app

**Both versions have identical features!** Pick whichever you prefer.

## Global Keyboard Shortcuts

Work anywhere on your Mac, even when the app is hidden:

| Shortcut | Action |
|----------|--------|
| `Cmd+R` | **Toggle recording** on/off<br>Auto-copies transcript to clipboard when stopping |
| `F9` | **Toggle recording** (alternative) |
| `Cmd+Shift+V` | **Paste transcripts** at cursor location |

**Setup Required:** See [ACCESSIBILITY.md](ACCESSIBILITY.md) for permission setup (2-minute one-time setup).

## Quick Start

### Installation

```bash
# Install dependencies
uv sync

# Start menu bar version
./start_app.sh

# OR start desktop window version
./start_desktop.sh
```

### First Use

1. **Start the app** (menu bar icon 🎤 appears, or window opens)
2. **Grant microphone permission** when prompted
3. **Setup accessibility** (for global hotkeys) - see [ACCESSIBILITY.md](ACCESSIBILITY.md)
4. **Start recording:**
   - Click 🎤 menu bar icon → "Open Window" → Click microphone button
   - OR press `Cmd+R` anywhere (works globally!)
5. **Speak naturally** - transcription appears after brief pauses
6. **Stop recording:**
   - Press `Cmd+R` again (auto-copies to clipboard!)
   - OR click microphone button in app
7. **Paste anywhere:** Press `Cmd+Shift+V`

## Usage Workflow

### Background Mode (Recommended)

Perfect for continuous use without opening the window:

```bash
./start_app.sh  # Starts in menu bar
# Window doesn't open - just runs in background

# Press Cmd+R → Start recording
# Speak your text
# Press Cmd+R → Stop (auto-copied!)
# Press Cmd+Shift+V → Paste anywhere
```

### Window Mode

For monitoring transcripts in real-time:

```bash
./start_app.sh  # Menu bar version
# Click 🎤 → "Open Window"

# OR

./start_desktop.sh  # Desktop window opens automatically
```

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
- ✅ App is running (check menu bar for 🎤)
- ✅ Mac has been restarted after granting permissions

### No transcripts appearing

- Check microphone is selected in Settings
- Adjust volume threshold (Settings panel)
- Ensure you're speaking loud enough
- Try a faster model (`base` instead of `turbo`)

## Technical Details

- **Backend**: FastAPI + Python
- **Frontend**: HTML/CSS/JavaScript
- **Transcription**: whisper-ctranslate2 (optimized Whisper)
- **Audio**: sounddevice + numpy
- **Desktop**: PyWebView (desktop version) or default browser (menu bar version)
- **Menu Bar**: rumps (macOS)
- **Hotkeys**: pynput

See [plan.md](plan.md) for complete architecture.

## 📁 Project Structure

```
├── start_app.sh          # Start menu bar version
├── start_desktop.sh      # Start desktop window version (recommended)
├── main.py               # Menu bar app entry point
├── main_desktop.py       # Desktop window entry point
├── config.json           # Your settings (auto-generated)
├── ACCESSIBILITY.md      # Accessibility permissions guide
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
