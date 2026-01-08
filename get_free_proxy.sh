#!/bin/bash
# Automatic free proxy finder and tester

cd "$(dirname "$0")"

echo "=========================================="
echo "Free Proxy Finder & Tester"
echo "=========================================="
echo ""
echo "This script will:"
echo "  1. Fetch free proxies from multiple sources"
echo "  2. Test each proxy"
echo "  3. Find the fastest working one"
echo "  4. Update your .env file"
echo ""
read -p "Press Enter to continue..."

# Create temp directory
TMP_DIR="/tmp/proxy_finder_$$"
mkdir -p "$TMP_DIR"

echo ""
echo "Step 1: Fetching free proxies..."
echo "-----------------------------------"

# Fetch from ProxyScrape API
echo "  Fetching from ProxyScrape..."
curl -s "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all" > "$TMP_DIR/proxyscrape.txt" 2>/dev/null

# Fetch from FreeProxyList
echo "  Fetching from FreeProxyList..."
curl -s "https://www.proxyscan.io/api/proxy?format=txt&limit=50" > "$TMP_DIR/freeproxylist.txt" 2>/dev/null

# Combine all proxies
cat "$TMP_DIR/proxyscrape.txt" "$TMP_DIR/freeproxylist.txt" | grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+" | sort -u > "$TMP_DIR/all_proxies.txt"

PROXY_COUNT=$(wc -l < "$TMP_DIR/all_proxies.txt" | tr -d ' ')
echo "  ✓ Found $PROXY_COUNT proxies"
echo ""

if [ "$PROXY_COUNT" -eq 0 ]; then
    echo "❌ No proxies found. Trying alternative method..."
    
    # Alternative: Use a known free proxy service
    echo "  Trying alternative sources..."
    curl -s "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt" > "$TMP_DIR/github_proxies.txt" 2>/dev/null
    cat "$TMP_DIR/github_proxies.txt" | grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+" | head -50 > "$TMP_DIR/all_proxies.txt"
    PROXY_COUNT=$(wc -l < "$TMP_DIR/all_proxies.txt" | tr -d ' ')
    
    if [ "$PROXY_COUNT" -eq 0 ]; then
        echo "❌ Could not fetch proxies. Check your internet connection."
        rm -rf "$TMP_DIR"
        exit 1
    fi
fi

echo "Step 2: Testing proxies (this may take a while)..."
echo "-----------------------------------"
echo "Testing up to 20 proxies to find a working one..."
echo ""

WORKING_PROXY=""
TEST_COUNT=0
MAX_TESTS=20

while IFS= read -r proxy && [ $TEST_COUNT -lt $MAX_TESTS ]; do
    TEST_COUNT=$((TEST_COUNT + 1))
    IP=$(echo "$proxy" | cut -d: -f1)
    PORT=$(echo "$proxy" | cut -d: -f2)
    
    printf "  [%2d/%2d] Testing %s:%s... " "$TEST_COUNT" "$MAX_TESTS" "$IP" "$PORT"
    
    # Test proxy with timeout
    RESULT=$(timeout 5 curl -s -x "http://$proxy" --max-time 5 "https://api.ipify.org" 2>/dev/null)
    
    if [ ! -z "$RESULT" ] && [[ "$RESULT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "✓ WORKING! (IP: $RESULT)"
        WORKING_PROXY="http://$proxy"
        break
    else
        echo "✗ Failed"
    fi
done < "$TMP_DIR/all_proxies.txt"

# Cleanup
rm -rf "$TMP_DIR"

echo ""
if [ -z "$WORKING_PROXY" ]; then
    echo "=========================================="
    echo "❌ No working proxy found"
    echo "=========================================="
    echo ""
    echo "Free proxies are unreliable. Try:"
    echo "  1. Run this script again (new proxies)"
    echo "  2. Use Windscribe free tier (more reliable)"
    echo "  3. Use ProtonVPN free (system VPN)"
    echo "  4. Get a paid proxy ($5-10/month)"
    echo ""
    exit 1
fi

echo "=========================================="
echo "✓ Found Working Proxy!"
echo "=========================================="
echo "Proxy: $WORKING_PROXY"
echo ""

# Update .env file
if [ -f ".env" ]; then
    # Backup existing .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null
    
    # Update VPN_PROXY
    if grep -q "^VPN_PROXY=" .env; then
        sed -i "s|^VPN_PROXY=.*|VPN_PROXY=$WORKING_PROXY|" .env
    else
        echo "VPN_PROXY=$WORKING_PROXY" >> .env
    fi
else
    # Create new .env
    echo "VPN_PROXY=$WORKING_PROXY" > .env
fi

echo "✓ Updated .env file with working proxy"
echo ""
echo "You can now run the scraper:"
echo "  ./run_with_vpn.sh"
echo ""
echo "⚠️  Note: Free proxies die frequently."
echo "   Run this script again if proxy stops working."
echo ""


