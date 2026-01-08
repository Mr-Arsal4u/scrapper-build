# Setup Page Guide

## 🎯 Overview

The scraper now has a **user-friendly setup page** that guides users through VPN extension setup **without requiring terminal knowledge**.

## 🚀 How It Works

### First-Time Users

1. **Start the app:**
   ```bash
   python app.py
   # or
   ./run.sh
   ```

2. **Open browser:** http://localhost:5000

3. **Automatic redirect:** If VPN setup is not complete, you'll be redirected to `/setup` page

4. **Setup page shows:**
   - Step-by-step instructions
   - "Setup VPN Extension" button
   - "Ready to Scrape" button (appears after clicking setup button)

### Setup Flow

1. **Click "Setup VPN Extension" Button**
   - Opens Chrome with scraper profile
   - Chrome Web Store opens automatically
   - "Ready to Scrape" button appears

2. **Install VPN Extension** (in Chrome window)
   - Search for "VPN" in Chrome Web Store
   - Install a free VPN extension (Windscribe, TunnelBear, etc.)
   - Connect the VPN
   - Verify it's working (visit https://api.ipify.org)
   - Close Chrome

3. **Click "Ready to Scrape" Button**
   - Marks setup as complete
   - Redirects to main scraper page
   - Scraper is already running (started when app.py ran)

4. **Start Scraping!**
   - Click "Scrape Towns" button
   - Scraper runs continuously
   - Automatically scrapes every 5 minutes

## ✅ Features

- ✅ **No terminal knowledge required** - Everything is done via web interface
- ✅ **Step-by-step instructions** - Clear guidance for users
- ✅ **Automatic redirect** - Setup page appears automatically if needed
- ✅ **One-time setup** - After setup, scraper runs continuously
- ✅ **Visual feedback** - Status messages show what's happening

## 🔧 Technical Details

### Routes Added

- `/setup` - Setup page
- `/api/setup-status` - Check if setup is complete
- `/api/open-chrome-for-vpn` - Open Chrome for VPN setup
- `/api/mark-setup-complete` - Mark setup as complete

### Files Created

- `templates/setup.html` - Setup page template
- `.vpn_extension_setup_complete` - Flag file (created when setup is complete)

### Logic Flow

1. User visits `/` → Checks if VPN setup is complete
2. If not complete → Redirects to `/setup`
3. User clicks "Setup VPN Extension" → Opens Chrome
4. User clicks "Ready to Scrape" → Creates flag file → Redirects to `/`
5. User can now scrape normally

## 📝 Notes

- The scraper **already runs** when `app.py` starts (scheduler starts automatically)
- The setup page just configures VPN extension
- After setup, users can use the scraper normally
- Setup is **one-time only** - flag file persists setup completion

## 🎉 Benefits

- **User-friendly** - No terminal commands needed
- **Guided setup** - Clear step-by-step instructions
- **Visual interface** - Buttons and status messages
- **Automatic** - Setup page appears automatically when needed

---

**The scraper runs continuously once started - no need to restart after setup!**

