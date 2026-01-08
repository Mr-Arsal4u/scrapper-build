# VPN Extension Setup for Chrome Scraper

## ✅ Easy Method: Use Chrome VPN Extension

Instead of configuring proxy, you can install a VPN extension in Chrome and the scraper will use it automatically!

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Run the Scraper Once
```bash
python app.py
```

This will open Chrome with the scraper's profile.

### Step 2: Install VPN Extension

When Chrome opens (scraper Chrome, not your regular Chrome):

1. **Go to Chrome Web Store**: https://chrome.google.com/webstore
2. **Search for VPN extension** (recommended):
   - **ProtonVPN Free** (if available)
   - **Windscribe Free**
   - **TunnelBear Free**
   - **Hotspot Shield Free**
   - Any free VPN extension

3. **Click "Add to Chrome"**
4. **Connect the VPN** in the extension
5. **Close Chrome**

### Step 3: Run Scraper Again
```bash
python app.py
```

The scraper will remember your VPN extension and use it automatically!

---

## 📝 Step-by-Step with Screenshots

### 1. First Run
```bash
cd /home/ro/scrapper-data
source venv/bin/activate
python app.py
```

Chrome will open (this is the scraper's Chrome, separate from yours).

### 2. Install VPN Extension

**Option A: ProtonVPN (Recommended)**
- Go to: https://chrome.google.com/webstore/search/protonvpn
- Click "Add to Chrome"
- Sign up for free account if needed
- Click extension icon → Connect

**Option B: Windscribe Free**
- Go to: https://chrome.google.com/webstore/search/windscribe
- Click "Add to Chrome"
- Sign up (10GB free/month)
- Click extension icon → Connect

**Option C: Any Free VPN Extension**
- Search "VPN" in Chrome Web Store
- Install any free one
- Connect it

### 3. Verify VPN is Connected

- Check extension icon (should show "Connected")
- Visit: https://api.ipify.org (should show different IP)
- Close Chrome

### 4. Run Scraper

```bash
python app.py
```

Now click "Scrape Towns" - it will use your VPN extension!

---

## 🔧 How It Works

1. **Scraper uses separate Chrome profile** (`.scraper-chrome-profile`)
2. **VPN extension is installed in that profile**
3. **Extension persists** - you only install once
4. **Scraper automatically uses VPN** when extension is connected

---

## ✅ Advantages

- ✅ **No proxy configuration needed**
- ✅ **Visual confirmation** (see extension icon)
- ✅ **Easy to manage** (click to connect/disconnect)
- ✅ **Works with any VPN extension**
- ✅ **Free options available**

---

## 🆘 Troubleshooting

### Extension Not Working?
1. Make sure extension is **connected** (icon shows "Connected")
2. Check extension is **enabled** in Chrome
3. Try a different VPN extension
4. Restart Chrome and reconnect VPN

### Scraper Still Can't Access Site?
1. Verify VPN is connected (check extension icon)
2. Test manually: Open Chrome, go to the target website
3. If it works manually, scraper should work too
4. Make sure you're using the scraper's Chrome (not your regular Chrome)

### Extension Disappears?
- Extensions are saved in `.scraper-chrome-profile` folder
- If you delete that folder, you'll need to reinstall extension
- Don't delete `.scraper-chrome-profile` folder!

---

## 💡 Pro Tips

1. **Use ProtonVPN or Windscribe** - Most reliable free options
2. **Keep extension connected** - Connect before running scraper
3. **Check extension status** - Make sure it shows "Connected"
4. **One-time setup** - Install once, use forever

---

## 🎯 Recommended VPN Extensions

### 1. Windscribe Free
- **10GB/month free**
- **Reliable**
- **Easy to use**
- Link: https://windscribe.com

### 2. ProtonVPN (if extension available)
- **Unlimited free**
- **Trusted**
- Link: https://protonvpn.com

### 3. TunnelBear Free
- **500MB/month free**
- **Simple interface**
- Link: https://www.tunnelbear.com

---

## 📋 Complete Workflow

```bash
# 1. Run scraper (opens Chrome)
python app.py

# 2. In the Chrome that opens:
#    - Go to Chrome Web Store
#    - Install VPN extension
#    - Connect VPN
#    - Close Chrome

# 3. Run scraper again
python app.py

# 4. Click "Scrape Towns" - VPN will be used automatically!
```

---

## ✅ Summary

**No proxy needed!** Just:
1. Install VPN extension in scraper's Chrome
2. Connect it
3. Run scraper - it uses VPN automatically!

The extension is saved, so you only need to install once.


