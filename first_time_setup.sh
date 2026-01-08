#!/bin/bash
# First-time setup script: Connects VPN extension, then runs project continuously

cd "$(dirname "$0")"

SCRAPER_PROFILE=".scraper-chrome-profile"
VPN_SETUP_FLAG=".vpn_extension_setup_complete"

echo "=========================================="
echo "Foreclosure Scraper - First Time Setup"
echo "=========================================="
echo ""

# Check if VPN extension is already set up
if [ -f "$VPN_SETUP_FLAG" ]; then
    echo "✅ VPN extension already set up!"
    echo "Starting scraper in continuous mode..."
    echo ""
    echo "The scraper will:"
    echo "  - Run continuously until you stop it (Ctrl+C)"
    echo "  - Automatically scrape every 5 minutes"
    echo "  - Save new leads to Excel files"
    echo ""
    echo "Access the web interface at: http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop the scraper"
    echo "=========================================="
    echo ""
    
    # Run the app (it will run continuously)
    if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
        exec venv/bin/python app.py
    else
        exec python3 app.py
    fi
else
    echo "🔧 First-time setup detected!"
    echo ""
    echo "This script will:"
    echo "  1. Open Chrome for VPN extension installation"
    echo "  2. Guide you through VPN setup"
    echo "  3. Then start the scraper to run continuously"
    echo ""
    read -p "Press Enter to continue..."
    echo ""
    
    # Kill any process on port 5000
    if command -v lsof &> /dev/null || command -v fuser &> /dev/null || command -v netstat &> /dev/null || command -v ss &> /dev/null; then
        PORT=5000
        PID=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}' || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 | head -1 || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
        
        if [ ! -z "$PID" ]; then
            echo "⚠️  Port 5000 is in use (PID: $PID)"
            echo "Killing existing process..."
            kill -9 $PID 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # Step 1: Open Chrome for VPN extension setup
    echo "=========================================="
    echo "Step 1: VPN Extension Setup"
    echo "=========================================="
    echo ""
    echo "Opening Chrome with scraper profile..."
    echo ""
    
    # Use the existing open_chrome_simple.py script
    if [ -f "open_chrome_simple.py" ]; then
        if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
            venv/bin/python open_chrome_simple.py
        else
            python3 open_chrome_simple.py
        fi
    else
        echo "❌ open_chrome_simple.py not found!"
        echo "Please run: python3 open_chrome_simple.py manually"
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    echo "📝 INSTRUCTIONS:"
    echo "=========================================="
    echo ""
    echo "In the Chrome window that opened:"
    echo ""
    echo "  1. Go to Chrome Web Store (should be open)"
    echo ""
    echo "  2. Search for 'VPN' and install a free one:"
    echo "     - Windscribe Free (recommended - 10GB/month)"
    echo "     - TunnelBear Free (500MB/month)"
    echo "     - ProtonVPN (if available)"
    echo "     - Any free VPN extension"
    echo ""
    echo "  3. Click the extension icon in Chrome toolbar"
    echo "     → Click 'Connect' or 'Turn On'"
    echo "     → Wait for connection (icon should show 'Connected')"
    echo ""
    echo "  4. Verify VPN is working:"
    echo "     → Visit: https://api.ipify.org"
    echo "     → Should show a different IP address"
    echo ""
    echo "  5. Close Chrome when done"
    echo ""
    echo "=========================================="
    echo ""
    read -p "Press Enter after you've installed and connected the VPN extension..."
    echo ""
    
    # Mark VPN setup as complete
    touch "$VPN_SETUP_FLAG"
    echo "✅ VPN extension setup complete!"
    echo ""
    
    # Step 2: Start the scraper continuously
    echo "=========================================="
    echo "Step 2: Starting Scraper (Continuous Mode)"
    echo "=========================================="
    echo ""
    echo "The scraper will now:"
    echo "  ✅ Run continuously until you stop it (Ctrl+C)"
    echo "  ✅ Automatically scrape every 5 minutes"
    echo "  ✅ Save new leads to Excel files"
    echo "  ✅ Use your VPN extension automatically"
    echo ""
    echo "Access the web interface at: http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop the scraper"
    echo "=========================================="
    echo ""
    
    # Run the app (it will run continuously)
    if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
        exec venv/bin/python app.py
    else
        exec python3 app.py
    fi
fi

