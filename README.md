# Foreclosure Scraper - User-Friendly One-Click Solution

A web scraping tool to extract foreclosure leads from the Connecticut Judicial website and save them to an Excel file.

## 🚀 Quick Start (Recommended - First Time Setup)

**For first-time setup with VPN extension:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run first-time setup (handles VPN extension setup automatically):**
   ```bash
   ./first_time_setup.sh
   ```
   
   This will:
   - Open Chrome for VPN extension installation
   - Guide you through VPN setup
   - Then start the scraper to run continuously

3. **After setup, the scraper runs continuously:**
   - Automatically scrapes every 5 minutes
   - Saves new leads to Excel files
   - Runs until you stop it (Ctrl+C)
   - Access web interface: http://localhost:5000

**For subsequent runs (after first-time setup):**
```bash
./start.sh
```

> 📖 **See [FIRST_TIME_STARTUP.md](FIRST_TIME_STARTUP.md) for detailed first-time setup guide**

---

## 🚀 Alternative Quick Start (Manual)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python app.py
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

4. **Click "Scrape Towns" button** - That's it! 🎉

## 🔒 VPN Setup (Choose One Method)

The website requires VPN access. Choose the method that works best for you:

### Method A: VPN Proxy (Recommended for Clients)

If you have a VPN proxy server:

1. Create a `.env` file in the project directory:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your VPN proxy:
   ```
   VPN_PROXY=http://your-vpn-proxy:port
   ```

3. If your proxy requires authentication:
   ```
   VPN_PROXY_USER=username
   VPN_PROXY_PASS=password
   ```

4. Restart the app and scrape!

### Method B: VPN Extension in Scraper Chrome

1. Run the app and click "Scrape Towns"
2. Chrome will open (this is the scraper's Chrome, separate from your Chrome)
3. Install your VPN extension in this Chrome window
4. Connect your VPN
5. Close Chrome
6. Click "Scrape Towns" again - it will remember your VPN extension

### Method C: System VPN

1. Connect VPN at the system level (before running the app)
2. Run the app and scrape - it will use system VPN automatically

## ✨ Features

- ✅ **One-click scraping** - Just click the button and it works
- ✅ **Continuous operation** - Runs automatically every 5 minutes until stopped
- ✅ **First-time setup** - Automated VPN extension setup
- ✅ **Doesn't interfere** with your existing Chrome sessions
- ✅ **Separate Chrome profile** - Uses its own Chrome instance
- ✅ **No need to close tabs** - Works independently
- ✅ **Automatic ChromeDriver** - Downloads compatible version automatically
- ✅ **Excel export** - Saves all leads to Excel file automatically
- ✅ **Real-time progress** - See scraping progress in the web interface

## 📊 Data Structure

The Excel file contains:
- Town
- Row #
- Sale Date
- Docket Number
- Sale Type
- Address
- Docket URL
- View Full Notice URL

## 🛠️ Troubleshooting

### "ChromeDriver error"
- Make sure Chrome browser is installed
- The app will automatically download ChromeDriver
- Check your internet connection

### "Connection error" or "No town names found"
- Verify VPN is configured correctly
- If using proxy, check `.env` file settings
- If using extension, make sure it's installed in scraper Chrome
- Try accessing the website manually to verify VPN works

### "ChromeDriver compatibility error"
- The app will automatically download compatible ChromeDriver
- Make sure Chrome browser is up to date
- Try scraping again

## 📁 Project Structure

```
scrapper-data/
├── app.py              # Flask web application
├── scraper.py          # Core scraping logic (optional)
├── requirements.txt    # Python dependencies
├── .env.example        # Example VPN configuration
├── .env                # Your VPN configuration (create this)
├── templates/
│   └── index.html     # Web interface
└── README.md          # This file
```

## 💡 Tips

- The scraper uses its own Chrome profile (`.scraper-chrome-profile` folder)
- You can delete this folder to reset the scraper Chrome (will need to reinstall VPN extension)
- All leads are saved to Excel files with timestamps
- Old lead files are automatically cleaned up after 1 hour

## 🔐 Security Note

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Keep your VPN credentials secure
