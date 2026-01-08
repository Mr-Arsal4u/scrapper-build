#!/bin/bash
# Run simple scraper - automatically uses venv if it exists

cd "$(dirname "$0")"

# Use venv if it exists
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    exec venv/bin/python simple_scraper.py
else
    # Fallback to system python3
    exec python3 simple_scraper.py
fi


