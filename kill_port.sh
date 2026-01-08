#!/bin/bash
# Kill process using port 5000

PORT=5000

echo "Checking for process on port $PORT..."

# Find process using port 5000
PID=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}')

if [ -z "$PID" ]; then
    # Try alternative method
    PID=$(netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 | head -1)
fi

if [ -z "$PID" ]; then
    # Try ss command
    PID=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
fi

if [ ! -z "$PID" ]; then
    echo "Found process $PID using port $PORT"
    echo "Killing process..."
    kill -9 $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null
    sleep 1
    echo "✓ Port $PORT is now free"
else
    echo "No process found on port $PORT"
fi


