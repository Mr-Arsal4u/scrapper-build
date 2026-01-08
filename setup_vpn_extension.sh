#!/bin/bash
# Helper script to setup VPN extension in Chrome

cd "$(dirname "$0")"

echo "=========================================="
echo "VPN Extension Setup Helper"
echo "=========================================="
echo ""
echo "This script will help you install a VPN extension"
echo "in the scraper's Chrome browser."
echo ""
echo "Steps:"
echo "  1. Run the scraper (opens Chrome)"
echo "  2. Install VPN extension in that Chrome"
echo "  3. Connect VPN"
echo "  4. Done! Scraper will use VPN automatically"
echo ""
read -p "Press Enter to start scraper and open Chrome..."

# Automatically use venv if it exists
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo ""
echo "Starting scraper..."
echo "Chrome will open - this is the scraper's Chrome (separate from yours)"
echo ""
echo "📝 INSTRUCTIONS:"
echo "  1. In the Chrome that opens, go to:"
echo "     https://chrome.google.com/webstore"
echo ""
echo "  2. Search for 'VPN' and install a free one:"
echo "     - Windscribe Free (recommended)"
echo "     - ProtonVPN (if available)"
echo "     - TunnelBear Free"
echo "     - Any free VPN extension"
echo ""
echo "  3. Click the extension icon and connect VPN"
echo ""
echo "  4. Close Chrome when done"
echo ""
echo "  5. Run scraper again - VPN will be used automatically!"
echo ""
echo "=========================================="
echo ""

# Run app.py which will open Chrome
$PYTHON_CMD app.py

