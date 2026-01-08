#!/usr/bin/env python3
"""
Simple script to open Chrome with scraper profile
This allows you to install VPN extension before running scraper
"""

import os
import subprocess
import sys

SCRAPER_PROFILE = os.path.join(os.path.dirname(__file__), ".scraper-chrome-profile")
os.makedirs(SCRAPER_PROFILE, exist_ok=True)

print("=" * 70)
print("Opening Chrome for VPN Extension Setup")
print("=" * 70)
print()
print("This will open Chrome with the scraper's profile.")
print("You can then install your VPN extension.")
print()

# Find Chrome executable
chrome_paths = [
    "google-chrome",
    "chromium-browser",
    "chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium"
]

chrome_cmd = None
for path in chrome_paths:
    try:
        result = subprocess.run(["which", path.split("/")[-1]], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            chrome_cmd = result.stdout.strip()
            break
    except:
        continue

if not chrome_cmd:
    # Try direct execution
    for path in chrome_paths:
        try:
            subprocess.run([path, "--version"], 
                         capture_output=True, timeout=2)
            chrome_cmd = path
            break
        except:
            continue

if not chrome_cmd:
    print("❌ Chrome/Chromium not found!")
    print("Please install Chrome first:")
    print("  sudo apt install google-chrome-stable")
    print("  or")
    print("  sudo apt install chromium-browser")
    sys.exit(1)

print(f"Using Chrome: {chrome_cmd}")
print(f"Profile: {SCRAPER_PROFILE}")
print()

# Open Chrome
try:
    subprocess.Popen([
        chrome_cmd,
        f"--user-data-dir={SCRAPER_PROFILE}",
        "--new-window",
        "https://chrome.google.com/webstore"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("✅ Chrome should now be open!")
    print()
    print("📝 INSTRUCTIONS:")
    print("  1. In the Chrome window that opened:")
    print("     - Chrome Web Store should be open")
    print("  2. Search for 'VPN' and install a free one:")
    print("     - Windscribe Free (recommended)")
    print("     - TunnelBear Free")
    print("     - Any free VPN extension")
    print("  3. Click extension icon → Connect VPN")
    print("  4. Verify: Visit https://api.ipify.org")
    print("  5. Close Chrome when done")
    print()
    print("  6. Then run: ./run.sh")
    print("     The scraper will use your VPN extension automatically!")
    print()
    
except Exception as e:
    print(f"❌ Error opening Chrome: {e}")
    print()
    print("Try manually:")
    print(f"  {chrome_cmd} --user-data-dir='{SCRAPER_PROFILE}' https://chrome.google.com/webstore")
    sys.exit(1)


