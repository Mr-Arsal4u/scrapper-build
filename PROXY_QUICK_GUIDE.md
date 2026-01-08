# Quick Guide: Getting a Proxy URL

## 🎯 Fastest Options

### Option 1: Use Free Proxy (Quick Test)
1. Go to: https://www.proxy-list.download/
2. Copy a proxy (format: `IP:PORT`)
3. Add to `.env`: `VPN_PROXY=http://IP:PORT`

### Option 2: Use Your VPN's Proxy
1. Log into your VPN account dashboard
2. Find "Proxy Servers" section
3. Copy proxy address (e.g., `proxy.vpn.com:8080`)
4. Add to `.env`: `VPN_PROXY=http://proxy.vpn.com:8080`

### Option 3: Free VPN with Proxy
- **ProtonVPN Free**: https://protonvpn.com (has proxy option)
- **Windscribe Free**: https://windscribe.com (10GB/month free)

---

## 📝 Step-by-Step: Setting Up Proxy

### Step 1: Get Proxy URL
Choose one:
- Free proxy from proxy-list.download
- Your VPN provider's proxy
- Paid proxy service

### Step 2: Create .env File
```bash
nano .env
```

### Step 3: Add Proxy
```
VPN_PROXY=http://your-proxy-ip:port
```

Example:
```
VPN_PROXY=http://185.199.229.156:7492
```

### Step 4: Test
```bash
./run_with_vpn.sh
```

---

## 🔍 How to Find Proxy in Common VPNs

### NordVPN
- Dashboard → Tools → Proxy
- Format: `us-nordvpn.com:1080`

### ExpressVPN
- Dashboard → Setup → Proxy
- Format: `us-proxy.expressvpn.com:3128`

### Surfshark
- Dashboard → Manual Setup → Proxy
- Format: `proxy.surfshark.com:1080`

---

## ⚠️ Important Notes

1. **Free proxies are unreliable** - Use for testing only
2. **Paid proxies are better** - For production use
3. **Some proxies need authentication** - Add `VPN_PROXY_USER` and `VPN_PROXY_PASS`
4. **Test your proxy first**:
   ```bash
   curl -x http://your-proxy:port https://api.ipify.org
   ```

---

## 🆘 Still Need Help?

Run the proxy checker:
```bash
./check_proxy.sh
```

Or check detailed guide:
```bash
cat HOW_TO_GET_PROXY.md
```


