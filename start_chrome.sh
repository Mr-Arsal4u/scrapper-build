#!/bin/bash
# Helper script to start Chrome with remote debugging enabled

echo "Closing any existing Chrome instances..."
pkill -f "google-chrome" 2>/dev/null
sleep 2

# Create temporary profile directory if it doesn't exist
TEMP_PROFILE="/tmp/chrome-debug-profile"
mkdir -p "$TEMP_PROFILE"

echo "Starting Chrome with remote debugging on port 9222..."
echo "Using temporary profile: $TEMP_PROFILE"
google-chrome --remote-debugging-port=9222 --user-data-dir="$TEMP_PROFILE" > /tmp/chrome_debug.log 2>&1 &

echo "Chrome is starting..."
echo "Waiting 5 seconds for Chrome to initialize..."
sleep 5

# Check if port is listening
if netstat -tlnp 2>/dev/null | grep -q 9222 || ss -tlnp 2>/dev/null | grep -q 9222; then
    echo "✓ Chrome remote debugging is active on port 9222"
else
    echo "✗ Warning: Port 9222 may not be listening yet"
    echo "Check /tmp/chrome_debug.log for errors"
fi

echo ""
echo "IMPORTANT:"
echo "1. Chrome should now be open"
echo "2. MANUALLY install/connect your VPN extension in this Chrome window"
echo "3. Keep Chrome open"
echo "4. Then run: source venv/bin/activate && python app.py"
echo ""
echo "Chrome is running in the background. You can close this terminal."

