#!/bin/bash
# Simple run script - automatically uses venv if it exists

cd "$(dirname "$0")"

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

# Use venv if it exists (seamless - no manual activation needed)
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    exec venv/bin/python app.py
else
    # Fallback to system python3
    exec python3 app.py
fi
