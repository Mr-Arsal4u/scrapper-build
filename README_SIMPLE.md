# Simple HTTP Scraper - No Browser Automation

This is a **simpler, faster, and more reliable** alternative to the browser-based scraper.

## ✨ Advantages

- ✅ **No browser automation** - Uses simple HTTP requests
- ✅ **Much faster** - No need to wait for browser to load
- ✅ **More reliable** - Less prone to crashes
- ✅ **Easier to use** - Just run and it works
- ✅ **Works with VPN proxy** - Configure once, use forever

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_simple.txt
```

### 2. Configure VPN Proxy (Required)

Create a `.env` file:

```bash
VPN_PROXY=http://your-vpn-proxy-host:port
# Optional if proxy needs authentication:
VPN_PROXY_USER=username
VPN_PROXY_PASS=password
```

Or set environment variable:

```bash
export VPN_PROXY="http://proxy-host:port"
```

### 3. Run the Scraper

**Option A: Using the script**
```bash
./run_simple_scraper.sh
```

**Option B: Direct Python**
```bash
python simple_scraper.py
```

That's it! The scraper will:
1. Fetch all towns
2. Scrape leads from each town
3. Save to Excel and JSON files in `scraped_data/` folder

## 📋 Output

The scraper creates:
- `scraped_data/foreclosure_leads_YYYYMMDD_HHMMSS.xlsx` - Excel file
- `scraped_data/foreclosure_leads_YYYYMMDD_HHMMSS.json` - JSON file

## 🔧 VPN Proxy Setup

### If you have a VPN proxy server:

1. Get your VPN proxy details (host, port)
2. Create `.env` file:
   ```
   VPN_PROXY=http://proxy.example.com:8080
   ```
3. Run the scraper

### If you have SOCKS5 proxy:

```
VPN_PROXY=socks5://socks-proxy.example.com:1080
```

### If proxy requires authentication:

```
VPN_PROXY=http://proxy.example.com:8080
VPN_PROXY_USER=myusername
VPN_PROXY_PASS=mypassword
```

## 🆚 Comparison with Browser Scraper

| Feature | Simple Scraper | Browser Scraper |
|---------|---------------|-----------------|
| Speed | ⚡ Very Fast | 🐌 Slower |
| Reliability | ✅ Very Stable | ⚠️ Can crash |
| Setup | ✅ Simple | ❌ Complex |
| VPN | ✅ Proxy only | ✅ Proxy/Extension/System |
| Resource Usage | ✅ Low | ❌ High (Chrome) |

## 🐛 Troubleshooting

### "403 Forbidden" or "Connection refused"

- **VPN proxy is required!** This website blocks direct connections
- Make sure `.env` file has correct `VPN_PROXY` setting
- Test your proxy: `curl -x http://your-proxy:port https://google.com`

### "No towns found"

- Check VPN proxy is working
- Verify you can access the website manually through VPN
- Check proxy credentials if authentication is required

### "Module not found"

- Install dependencies: `pip install -r requirements_simple.txt`

## 💡 Tips

- The scraper is respectful - adds small delays between requests
- All data is saved with timestamps
- Check `scraped_data/` folder for output files
- JSON file contains raw data for further processing

## 📝 Example Usage

```bash
# 1. Set up VPN proxy
echo "VPN_PROXY=http://my-vpn-proxy.com:8080" > .env

# 2. Run scraper
python simple_scraper.py

# 3. Check results
ls -lh scraped_data/
```

## 🔐 Security

- Never commit `.env` file to version control
- Keep VPN credentials secure
- The `.env` file is already in `.gitignore`


