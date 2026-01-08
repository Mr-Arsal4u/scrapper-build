#!/bin/bash
# Script to help find proxy settings

echo "=========================================="
echo "Proxy Detection Helper"
echo "=========================================="
echo ""

echo "1. Checking environment variables..."
if [ ! -z "$http_proxy" ] || [ ! -z "$HTTP_PROXY" ]; then
    echo "   ✓ Found HTTP_PROXY: ${http_proxy:-$HTTP_PROXY}"
else
    echo "   ✗ No HTTP_PROXY found"
fi

if [ ! -z "$https_proxy" ] || [ ! -z "$HTTPS_PROXY" ]; then
    echo "   ✓ Found HTTPS_PROXY: ${https_proxy:-$HTTPS_PROXY}"
else
    echo "   ✗ No HTTPS_PROXY found"
fi

echo ""
echo "2. Checking system proxy settings..."
if command -v gsettings &> /dev/null; then
    HTTP_PROXY_SYS=$(gsettings get org.gnome.system.proxy.http host 2>/dev/null)
    if [ ! -z "$HTTP_PROXY_SYS" ] && [ "$HTTP_PROXY_SYS" != "''" ]; then
        PORT=$(gsettings get org.gnome.system.proxy.http port 2>/dev/null)
        echo "   ✓ System HTTP Proxy: ${HTTP_PROXY_SYS}:${PORT}"
    fi
fi

echo ""
echo "3. Checking VPN processes..."
if pgrep -x "openvpn" > /dev/null; then
    echo "   ✓ OpenVPN is running"
    echo "   Check OpenVPN config for proxy settings"
fi

if pgrep -x "nordvpn" > /dev/null; then
    echo "   ✓ NordVPN is running"
    echo "   Check: nordvpn settings"
fi

echo ""
echo "4. Testing current connection..."
MY_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null)
if [ ! -z "$MY_IP" ]; then
    echo "   ✓ Your current IP: $MY_IP"
    echo "   Location: $(curl -s --max-time 5 "https://ipapi.co/$MY_IP/json/" | grep -o '"city":"[^"]*"' | head -1)"
else
    echo "   ✗ Could not detect IP (might need VPN/proxy)"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "If you found a proxy above, add it to .env:"
echo "  VPN_PROXY=http://proxy-host:port"
echo ""
echo "If not, check HOW_TO_GET_PROXY.md for options"
echo ""
