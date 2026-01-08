#!/bin/bash
# Simple scraper runner script

cd "$(dirname "$0")"

# Use system Python (no venv needed)
# if [ -d "venv" ]; then
#     source venv/bin/activate
# fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements_simple.txt

# Run the simple scraper
echo "Starting scraper..."
python simple_scraper.py

