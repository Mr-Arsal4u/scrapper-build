#!/bin/bash
# Check if Flask server is running

echo "Checking Flask server status..."
echo ""

# Check if port 5000 is in use
if command -v lsof &> /dev/null; then
    PID=$(lsof -ti:5000 2>/dev/null)
elif command -v netstat &> /dev/null; then
    PID=$(netstat -tlnp 2>/dev/null | grep ":5000 " | awk '{print $7}' | cut -d'/' -f1 | head -1)
elif command -v ss &> /dev/null; then
    PID=$(ss -tlnp 2>/dev/null | grep ":5000 " | grep -oP 'pid=\K[0-9]+' | head -1)
fi

if [ ! -z "$PID" ]; then
    echo "✅ Flask server is running (PID: $PID)"
    echo ""
    echo "Server should be accessible at:"
    echo "  http://localhost:5000"
    echo "  http://127.0.0.1:5000"
    echo ""
    
    # Test if server responds
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Server is responding correctly"
    else
        echo "⚠️  Server is running but not responding"
    fi
else
    echo "❌ Flask server is NOT running"
    echo ""
    echo "Start it with:"
    echo "  ./run.sh"
    echo ""
fi


