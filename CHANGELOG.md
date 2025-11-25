# Changelog

## [2024-11-25] - Codebase Cleanup & Quality Improvements

### 🗑️ Files Removed
- **transcribe.sh** - Old CLI wrapper script (functionality now in desktop app)
- **plan.md** - Development planning document (no longer needed)
- **post.md** - Blog post draft (moved out of codebase)
- **Info.plist.template** - Unused template file

### ✨ New Features Added
- **Auto-paste to active editor** - Transcriptions automatically paste where you're typing
- **Configurable auto-paste** - Toggle on/off via settings UI
- **Constants module** (`backend/constants.py`) - Centralized configuration values

### 🔧 Code Quality Improvements

#### Type Hints & Documentation
- ✅ Added comprehensive type hints to all functions and methods
- ✅ Added docstrings throughout the codebase
- ✅ Documented all API endpoints with proper type signatures
- ✅ Added module-level documentation strings

#### Refactoring
- ✅ Extracted magic numbers into named constants
- ✅ Created `backend/constants.py` for centralized configuration
- ✅ Improved code organization and readability
- ✅ Cleaned up redundant comments
- ✅ Made threading daemon threads explicit

#### Files Improved
- `backend/service.py` - Full type hints, docstrings, and constants
- `backend/app.py` - API endpoint documentation and type hints
- `backend/config.py` - Type hints and documentation
- `main.py` - Type hints for menu bar app
- `main_desktop.py` - Type hints for desktop app

### 📝 Documentation
- ✅ Created `.gitignore` file (Python, macOS, IDE, project-specific)
- ✅ Updated README with code quality badges
- ✅ Improved project structure documentation

### 🎯 Quality Metrics
- **Zero linter errors**
- **100% type-hinted functions**
- **Comprehensive docstrings**
- **No magic numbers**
- **Clean separation of concerns**

## Previous Versions

### Initial Release
- Real-time speech-to-text with Whisper
- Global keyboard shortcuts
- Queue monitoring
- File transcription support
- Web-based UI

