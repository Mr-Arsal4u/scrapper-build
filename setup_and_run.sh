#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================="
echo "Simple Scraper Setup & Run"
echo "=========================================="

# Use system Python (no venv needed)
# if [ -d "venv" ]; then
#     source venv/bin/activate
#     echo "✓ Virtual environment activated"
# else
#     echo "⚠️  Virtual environment not found"
# fi
echo "✓ Using system Python"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q requests beautifulsoup4 pandas openpyxl python-dotenv lxml
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
# VPN Proxy Configuration
# Replace with your actual VPN proxy details
VPN_PROXY=http://proxy.example.com:8080

# If your proxy requires authentication:
# VPN_PROXY_USER=your_username
# VPN_PROXY_PASS=your_password

# Common examples:
# VPN_PROXY=http://127.0.0.1:8080
# VPN_PROXY=socks5://127.0.0.1:1080
ENVEOF
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your VPN proxy details!"
    echo "   Example: VPN_PROXY=http://your-vpn-proxy:port"
    echo ""
    read -p "Press Enter to continue (or Ctrl+C to edit .env first)..."
fi

# Load .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ Loaded .env configuration"
fi

# Run the scraper
echo ""
echo "=========================================="
echo "Starting Scraper..."
echo "=========================================="
python3 simple_scraper.py
