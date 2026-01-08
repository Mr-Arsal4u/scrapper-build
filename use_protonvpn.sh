#!/bin/bash
# Quick script to connect ProtonVPN and run scraper

cd "$(dirname "$0")"

echo "=========================================="
echo "ProtonVPN + Scraper"
echo "=========================================="
echo ""

# Check if ProtonVPN is installed
if ! command -v protonvpn &> /dev/null; then
    echo "❌ ProtonVPN CLI not found!"
    echo ""
    echo "Run setup first:"
    echo "  ./setup_protonvpn.sh"
    echo ""
    exit 1
fi

# Check if already connected
if protonvpn status 2>/dev/null | grep -q "Connected"; then
    echo "✓ Already connected to ProtonVPN"
    protonvpn status | head -5
else
    echo "Connecting to ProtonVPN..."
    protonvpn connect -f
    
    # Wait for connection
    sleep 3
    
    if ! protonvpn status 2>/dev/null | grep -q "Connected"; then
        echo "❌ Failed to connect. Try manually:"
        echo "  protonvpn connect -f"
        exit 1
    fi
    
    echo "✓ Connected to ProtonVPN"
fi

echo ""
echo "Your current IP:"
curl -s https://api.ipify.org
echo ""
echo ""

# Use system Python (no venv needed)
# if [ -d "venv" ]; then
#     source venv/bin/activate
# fi

# Ask what to run
echo "What would you like to run?"
echo "  1) Simple scraper (python simple_scraper.py)"
echo "  2) Web app (python app.py)"
echo "  3) Just keep VPN connected"
echo ""
read -p "Choose (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Starting simple scraper..."
        python3 simple_scraper.py
        ;;
    2)
        echo ""
        echo "Starting web app..."
        echo "Open http://localhost:5000 in your browser"
        python3 app.py
        ;;
    3)
        echo ""
        echo "VPN is connected. You can run scraper manually:"
        echo "  python3 simple_scraper.py"
        echo ""
        echo "Press Ctrl+C to disconnect VPN"
        while true; do
            sleep 60
            if ! protonvpn status 2>/dev/null | grep -q "Connected"; then
                echo "⚠️  VPN disconnected!"
                break
            fi
        done
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

