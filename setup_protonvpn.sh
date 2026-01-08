#!/bin/bash
# Setup script for ProtonVPN with scraper

cd "$(dirname "$0")"

echo "=========================================="
echo "ProtonVPN Setup for Scraper"
echo "=========================================="
echo ""

# Check if ProtonVPN CLI is installed
if ! command -v protonvpn &> /dev/null; then
    echo "ProtonVPN CLI is not installed."
    echo ""
    echo "Installing ProtonVPN CLI..."
    echo ""
    
    # Check if we can install
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 is required. Please install it first."
        exit 1
    fi
    
    # Install ProtonVPN CLI
    echo "Installing ProtonVPN CLI..."
    pip3 install protonvpn-cli --user 2>/dev/null || {
        echo "Trying alternative installation method..."
        git clone https://github.com/ProtonVPN/linux-cli.git /tmp/protonvpn-cli 2>/dev/null
        if [ -d "/tmp/protonvpn-cli" ]; then
            cd /tmp/protonvpn-cli
            sudo ./protonvpn install 2>/dev/null || {
                echo "❌ Could not install ProtonVPN CLI automatically."
                echo ""
                echo "Please install manually:"
                echo "  1. Visit: https://protonvpn.com/support/linux-vpn-setup/"
                echo "  2. Or use: sudo apt install protonvpn-cli"
                exit 1
            }
        fi
    }
    
    echo "✓ ProtonVPN CLI installed"
    echo ""
fi

# Check if logged in
if ! protonvpn status &> /dev/null || [ "$(protonvpn status 2>/dev/null | grep -c 'No active')" -gt 0 ]; then
    echo "You need to login to ProtonVPN first."
    echo ""
    echo "If you don't have an account, sign up for free at:"
    echo "  https://protonvpn.com/signup"
    echo ""
    read -p "Press Enter to login to ProtonVPN (or Ctrl+C to sign up first)..."
    
    protonvpn login
fi

echo ""
echo "Connecting to ProtonVPN (free server)..."
echo ""

# Connect to fastest free server
protonvpn connect -f

# Wait a moment for connection
sleep 3

# Check connection status
if protonvpn status | grep -q "Connected"; then
    echo ""
    echo "=========================================="
    echo "✓ ProtonVPN Connected Successfully!"
    echo "=========================================="
    echo ""
    
    # Show connection info
    protonvpn status
    
    echo ""
    echo "Your IP address:"
    curl -s https://api.ipify.org
    echo ""
    echo ""
    
    # Update .env to not use proxy (use system VPN)
    if [ -f ".env" ]; then
        # Comment out VPN_PROXY if it exists
        sed -i 's/^VPN_PROXY=/#VPN_PROXY=/' .env 2>/dev/null || true
    fi
    
    echo "✓ Configured scraper to use system VPN"
    echo ""
    echo "You can now run the scraper:"
    echo "  python simple_scraper.py"
    echo ""
    echo "Or the web app:"
    echo "  python app.py"
    echo ""
else
    echo ""
    echo "❌ Failed to connect to ProtonVPN"
    echo ""
    echo "Try manually:"
    echo "  protonvpn connect -f"
    echo ""
    exit 1
fi


