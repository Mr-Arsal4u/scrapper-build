#!/bin/bash
# Quick script to create .env file with VPN proxy

echo "VPN Proxy Setup"
echo "=============="
echo ""
echo "Enter your VPN proxy details:"
echo ""
read -p "Proxy URL (e.g., http://proxy.example.com:8080): " PROXY_URL
read -p "Proxy Username (optional, press Enter to skip): " PROXY_USER
read -p "Proxy Password (optional, press Enter to skip): " PROXY_PASS

cat > .env << ENVFILE
# VPN Proxy Configuration
VPN_PROXY=${PROXY_URL}
ENVFILE

if [ ! -z "$PROXY_USER" ]; then
    echo "VPN_PROXY_USER=${PROXY_USER}" >> .env
fi

if [ ! -z "$PROXY_PASS" ]; then
    echo "VPN_PROXY_PASS=${PROXY_PASS}" >> .env
fi

echo ""
echo "✓ .env file created successfully!"
echo ""
cat .env
