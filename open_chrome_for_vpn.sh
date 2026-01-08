#!/bin/bash
# Open Chrome with scraper profile so you can install VPN extension

cd "$(dirname "$0")"

SCRAPER_PROFILE="$PWD/.scraper-chrome-profile"

echo "=========================================="
echo "Opening Chrome for VPN Extension Setup"
echo "=========================================="
echo ""
echo "This will open Chrome with the scraper's profile."
echo "You can then install your VPN extension."
echo ""

# Create profile directory if it doesn't exist
mkdir -p "$SCRAPER_PROFILE"

# Check if Chrome is installed
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "❌ Chrome/Chromium not found!"
    echo "Please install Chrome first."
    exit 1
fi

# Determine Chrome command
if command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"
elif command -v chromium &> /dev/null; then
    CHROME_CMD="chromium"
fi

echo "Opening Chrome with scraper profile..."
echo "Profile: $SCRAPER_PROFILE"
echo ""

# Open Chrome with the scraper profile
$CHROME_CMD \
    --user-data-dir="$SCRAPER_PROFILE" \
    --new-window \
    https://chrome.google.com/webstore \
    > /dev/null 2>&1 &

sleep 2

echo "✅ Chrome should now be open!"
echo ""
echo "📝 INSTRUCTIONS:"
echo "  1. In the Chrome window that opened:"
echo "     - Go to Chrome Web Store (already open)"
echo "  2. Search for 'VPN' and install a free one:"
echo "     - Windscribe Free (recommended - 10GB/month)"
echo "     - TunnelBear Free (500MB/month)"
echo "     - Any free VPN extension"
echo "  3. Click the extension icon and connect VPN"
echo "  4. Verify: Visit https://api.ipify.org (should show different IP)"
echo "  5. Close Chrome when done"
echo ""
echo "  6. Then run: ./run.sh"
echo "     The scraper will use your VPN extension automatically!"
echo ""
echo "=========================================="


