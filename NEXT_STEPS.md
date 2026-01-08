# Next Steps - Complete Setup Guide

## ✅ Current Status

Your scraper is ready! The app is configured and working. Now you need to:

1. **Start the app**
2. **Install VPN extension in Chrome**
3. **Test scraping**

---

## Step 1: Start the Application

```bash
./run.sh
```

This will:
- Automatically kill any process on port 5000
- Start the Flask server
- Make it available at: **http://localhost:5000**

**Keep this terminal open!**

---

## Step 2: Install VPN Extension

When you run the app, Chrome will open (this is the scraper's Chrome, separate from your regular Chrome).

### In that Chrome window:

1. **Go to Chrome Web Store:**
   ```
   https://chrome.google.com/webstore
   ```

2. **Search for "VPN"** and install a free one:
   - **Windscribe Free** (recommended - 10GB/month)
   - **TunnelBear Free** (500MB/month)
   - **Any free VPN extension**

3. **Connect the VPN:**
   - Click the extension icon in Chrome toolbar
   - Click "Connect" or "Turn On"
   - Wait for connection (icon should show "Connected")

4. **Verify VPN is working:**
   - Visit: https://api.ipify.org
   - Should show a different IP address (not your real IP)

5. **Close Chrome** (the extension is saved, don't worry!)

---

## Step 3: Test the Scraper

1. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

2. **Click "Scrape Towns" button**

3. **Wait for results** - it should:
   - Connect to the website via VPN
   - Extract all town names
   - Display them on the page

4. **If successful:**
   - Click "Extract Leads" button
   - This will scrape foreclosure data from all towns
   - Results will be saved to Excel file

---

## 🆘 Troubleshooting

### "Connection error" or "No towns found"
- **VPN not connected!** Make sure:
  - VPN extension is installed
  - VPN is connected (check extension icon)
  - Try reconnecting VPN
  - Test manually: Visit the target website in Chrome

### "Port 5000 already in use"
- Run: `./kill_port.sh`
- Or: `./run.sh` (automatically kills port)

### Chrome doesn't open
- Make sure Chrome browser is installed
- Check: `google-chrome --version`

### Extension not working
- Make sure extension is **enabled** in Chrome
- Check extension icon shows "Connected"
- Try a different VPN extension

---

## 📋 Quick Reference

```bash
# Start app
./run.sh

# Kill port 5000 manually
./kill_port.sh

# Run simple scraper (alternative)
./run_simple.sh

# Setup VPN extension helper
./setup_vpn_extension.sh
```

---

## ✅ Success Checklist

- [ ] App is running (http://localhost:5000)
- [ ] VPN extension installed in scraper's Chrome
- [ ] VPN is connected (extension icon shows "Connected")
- [ ] Can access http://localhost:5000 in browser
- [ ] "Scrape Towns" button works
- [ ] Towns are displayed
- [ ] "Extract Leads" button works
- [ ] Excel file is generated

---

## 🎯 What Happens Next

Once everything is working:

1. **Click "Scrape Towns"** → Gets list of all towns
2. **Click "Extract Leads"** → Scrapes foreclosure data from all towns
3. **Download Excel** → Get all leads in Excel format
4. **Done!** → Data is saved in project folder

The scraper will:
- Use your VPN extension automatically
- Scrape all towns
- Save results to Excel
- Show progress in real-time

---

## 💡 Tips

- **Keep VPN connected** while scraping
- **Don't close Chrome** while scraping is in progress
- **Be patient** - scraping many towns takes time
- **Check Excel file** in project folder after scraping

---

## 🚀 Ready to Start?

Run this command:
```bash
./run.sh
```

Then follow Step 2 and Step 3 above!


