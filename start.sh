#!/bin/bash
# Start the scraper in continuous mode (after first-time setup)

cd "$(dirname "$0")"

echo "=========================================="
echo "Starting Foreclosure Scraper"
echo "=========================================="
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

echo "The scraper will:"
echo "  ✅ Run continuously until you stop it (Ctrl+C)"
echo "  ✅ Automatically scrape every 5 minutes"
echo "  ✅ Save new leads to Excel files"
echo ""
echo "Access the web interface at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the scraper"
echo "=========================================="
echo ""

# Use venv if it exists
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    exec venv/bin/python app.py
else
    exec python3 app.py
fi

