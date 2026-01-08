#!/bin/bash
# Simple runner script with VPN check

cd "$(dirname "$0")"

# Use system Python (no venv needed)
# source venv/bin/activate 2>/dev/null || true

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "=========================================="
    echo "❌ .env file not found!"
    echo "=========================================="
    echo ""
    echo "You need to configure VPN proxy first."
    echo ""
    echo "Quick setup:"
    echo "  1. Run: ./create_env.sh"
    echo "  2. Or create .env manually with:"
    echo "     VPN_PROXY=http://your-vpn-proxy:port"
    echo ""
    exit 1
fi

# Load .env
export $(grep -v '^#' .env | xargs)

# Check if VPN_PROXY is set
if [ -z "$VPN_PROXY" ] || [ "$VPN_PROXY" = "http://proxy.example.com:8080" ]; then
    echo "=========================================="
    echo "⚠️  VPN Proxy not configured!"
    echo "=========================================="
    echo ""
    echo "Current VPN_PROXY: ${VPN_PROXY:-'not set'}"
    echo ""
    echo "Please edit .env file and set your actual VPN proxy:"
    echo "  VPN_PROXY=http://your-vpn-proxy:port"
    echo ""
    exit 1
fi

echo "=========================================="
echo "Starting Simple Scraper"
echo "=========================================="
echo "VPN Proxy: $VPN_PROXY"
echo ""

python3 simple_scraper.py
