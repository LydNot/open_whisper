#!/bin/bash
# Check Open Whisper service status

echo "📊 Open Whisper Service Status"
echo "================================"
echo ""

# Check if service is loaded
if launchctl list | grep -q "com.openwhisper"; then
    echo "✓ Service is loaded"
    
    # Get PID
    PID=$(launchctl list | grep com.openwhisper | awk '{print $1}')
    if [ "$PID" != "-" ]; then
        echo "✓ Service is running (PID: $PID)"
    else
        echo "⚠ Service is loaded but not running"
    fi
else
    echo "✗ Service is not loaded"
    echo "  Run ./install_service.sh to install"
fi

echo ""

# Check if process is running
if ps aux | grep -v grep | grep -q "main.py"; then
    echo "✓ Open Whisper process is active"
    ps aux | grep -v grep | grep "main.py" | awk '{print "  PID: " $2 ", CPU: " $3 "%, Memory: " $4 "%"}'
else
    echo "✗ Open Whisper process is not running"
fi

echo ""
echo "Recent logs (last 10 lines):"
echo "----------------------------"
if [ -f logs/stdout.log ]; then
    tail -n 10 logs/stdout.log
else
    echo "(no logs yet)"
fi

echo ""
echo "Useful commands:"
echo "  View logs:     tail -f logs/stdout.log logs/stderr.log"
echo "  Restart:       launchctl kickstart -k gui/\$(id -u)/com.openwhisper"
echo "  Stop:          launchctl stop com.openwhisper"
echo "  Uninstall:     ./uninstall_service.sh"


