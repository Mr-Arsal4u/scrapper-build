# Quick Start Guide - Simple Scraper

## Step 1: Configure VPN Proxy

You need to create a `.env` file with your VPN proxy details.

### Option A: Use the interactive script
```bash
./create_env.sh
```

### Option B: Create .env manually
```bash
nano .env
```

Add this content (replace with YOUR actual VPN proxy):
```
VPN_PROXY=http://your-vpn-proxy-host:port
```

Examples:
- `VPN_PROXY=http://127.0.0.1:8080`
- `VPN_PROXY=socks5://127.0.0.1:1080`
- `VPN_PROXY=http://vpn-proxy.example.com:3128`

If your proxy needs authentication:
```
VPN_PROXY=http://proxy-host:port
VPN_PROXY_USER=your_username
VPN_PROXY_PASS=your_password
```

## Step 2: Run the Scraper

```bash
python simple_scraper.py
```

Or use the setup script:
```bash
./setup_and_run.sh
```

## Step 3: Check Results

Results are saved in `scraped_data/` folder:
- Excel file: `foreclosure_leads_YYYYMMDD_HHMMSS.xlsx`
- JSON file: `foreclosure_leads_YYYYMMDD_HHMMSS.json`

## Troubleshooting

### "Connection timed out" or "403 Forbidden"
- **You need VPN!** The website blocks direct connections
- Make sure `.env` file has correct `VPN_PROXY` setting
- Test your proxy: `curl -x http://your-proxy:port https://google.com`

### "No towns found"
- Check VPN proxy is working
- Verify you can access the website manually through VPN


