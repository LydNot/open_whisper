#!/bin/bash
# Install Open Whisper as a background service

set -e

echo "🎤 Installing Open Whisper background service..."

# Create logs directory
mkdir -p logs

# Copy plist to LaunchAgents
PLIST_NAME="com.openwhisper.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

cp "$PLIST_NAME" "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
echo "✓ Copied $PLIST_NAME to $LAUNCH_AGENTS_DIR"

# Unload if already loaded (ignore errors)
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true

# Load the service
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
echo "✓ Loaded service"

# Start the service
launchctl start com.openwhisper
echo "✓ Started service"

echo ""
echo "🎉 Open Whisper is now running in the background!"
echo ""
echo "The app will:"
echo "  • Start automatically when you log in"
echo "  • Restart automatically if it crashes"
echo "  • Run continuously in the background"
echo ""
echo "Useful commands:"
echo "  Check status:  launchctl list | grep openwhisper"
echo "  Stop service:  launchctl stop com.openwhisper"
echo "  Restart:       launchctl kickstart -k gui/\$(id -u)/com.openwhisper"
echo "  View logs:     tail -f logs/stdout.log logs/stderr.log"
echo "  Uninstall:     ./uninstall_service.sh"
echo ""
echo "Look for the 🎤 icon in your menu bar!"





