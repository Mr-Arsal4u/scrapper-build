# First-Time Startup Guide

## 🚀 Complete Workflow

This guide explains how to start the project for the first time (to connect VPN extension) and then run it continuously.

---

## 📋 Overview

**The project workflow:**
1. **First Time**: Setup VPN extension → Then runs continuously
2. **After Setup**: Just start the project → Runs continuously until stopped

**The scraper will:**
- ✅ Run continuously (lifetime) until you manually stop it
- ✅ Automatically scrape every 5 minutes
- ✅ Save new leads to Excel files automatically
- ✅ Use VPN extension automatically

---

## 🎯 First-Time Setup (One-Time Only)

### Step 1: Run First-Time Setup Script

```bash
./first_time_setup.sh
```

This script will:
1. Open Chrome for VPN extension installation
2. Guide you through VPN setup
3. Then start the scraper to run continuously

### Step 2: Install VPN Extension

When Chrome opens:

1. **Go to Chrome Web Store** (should be open automatically)
2. **Search for "VPN"** and install a free one:
   - **Windscribe Free** (recommended - 10GB/month)
   - **TunnelBear Free** (500MB/month)
   - **ProtonVPN** (if available)
   - Any free VPN extension

3. **Connect the VPN:**
   - Click the extension icon in Chrome toolbar
   - Click "Connect" or "Turn On"
   - Wait for connection (icon should show "Connected")

4. **Verify VPN is working:**
   - Visit: https://api.ipify.org
   - Should show a different IP address

5. **Close Chrome** (the extension is saved automatically!)

6. **Press Enter** in the terminal to continue

### Step 3: Scraper Starts Automatically

After VPN setup, the scraper will:
- ✅ Start running continuously
- ✅ Automatically scrape every 5 minutes
- ✅ Use your VPN extension automatically
- ✅ Save new leads to Excel files

**Access the web interface:** http://localhost:5000

**To stop:** Press `Ctrl+C` in the terminal

---

## 🔄 Running After First-Time Setup

After the first-time setup is complete, you can simply run:

```bash
./start.sh
```

Or:

```bash
./run.sh
```

The scraper will:
- ✅ Run continuously until you stop it
- ✅ Automatically scrape every 5 minutes
- ✅ Use your saved VPN extension
- ✅ Save new leads to Excel files

**To stop:** Press `Ctrl+C` in the terminal

---

## 📊 How It Works

### Continuous Operation

The scraper uses a **background scheduler** that:
- Runs every **5 minutes** automatically
- Scrapes all towns for foreclosure leads
- Compares with previous results
- Saves only **new leads** to Excel files
- Runs **continuously** until you stop it

### VPN Extension

- The VPN extension is saved in `.scraper-chrome-profile` folder
- You only need to install it **once**
- The scraper uses it automatically on every run
- No need to reconnect manually

### Excel Files

The scraper saves two types of files:
- `new_leads_YYYYMMDD_HHMMSS.xlsx` - Only new leads (when count increases)
- `all_leads_YYYYMMDD_HHMMSS.xlsx` - All current leads

---

## 🛑 Stopping the Scraper

To stop the scraper:
1. Go to the terminal where it's running
2. Press `Ctrl+C`
3. Wait for it to shut down gracefully

The scheduler will stop and the Flask server will close.

---

## 🔧 Troubleshooting

### VPN Extension Not Working?

1. Make sure extension is **connected** (check extension icon)
2. Try reconnecting the VPN
3. Run `./first_time_setup.sh` again to reinstall

### Scraper Not Accessing Website?

1. Verify VPN is connected (check extension icon)
2. Test manually: Open Chrome, go to the target website
3. If it works manually, scraper should work too

### Want to Reset VPN Setup?

Delete the setup flag and run first-time setup again:
```bash
rm .vpn_extension_setup_complete
./first_time_setup.sh
```

---

## 📝 Summary

**First Time:**
```bash
./first_time_setup.sh
# → Install VPN extension → Press Enter → Runs continuously
```

**After Setup:**
```bash
./start.sh
# → Runs continuously until you stop it (Ctrl+C)
```

**The scraper runs continuously (lifetime) until you manually stop it!**

---

## ✅ Quick Reference

| Action | Command |
|--------|---------|
| First-time setup | `./first_time_setup.sh` |
| Start scraper | `./start.sh` or `./run.sh` |
| Stop scraper | `Ctrl+C` in terminal |
| Web interface | http://localhost:5000 |
| Reset VPN setup | `rm .vpn_extension_setup_complete && ./first_time_setup.sh` |

---

## 💡 Tips

1. **Keep the terminal open** - The scraper runs in that terminal
2. **Check Excel files** - New leads are saved automatically
3. **VPN stays connected** - Extension remembers connection
4. **Runs 24/7** - Can run continuously until you stop it
5. **No manual intervention** - Fully automated after setup

---

## 🎉 You're All Set!

Once you run `./first_time_setup.sh` and complete VPN setup, the scraper will run continuously and automatically scrape every 5 minutes. Just let it run!

