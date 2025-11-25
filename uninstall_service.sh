#!/bin/bash
# Uninstall Open Whisper background service

set -e

echo "🛑 Uninstalling Open Whisper background service..."

PLIST_NAME="com.openwhisper.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

if [ -f "$PLIST_PATH" ]; then
    # Stop and unload the service
    launchctl stop com.openwhisper 2>/dev/null || true
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    
    # Remove the plist
    rm "$PLIST_PATH"
    echo "✓ Removed service"
else
    echo "⚠ Service not found at $PLIST_PATH"
fi

echo ""
echo "✓ Open Whisper background service uninstalled"
echo "You can still run it manually with: ./start_app.sh"




