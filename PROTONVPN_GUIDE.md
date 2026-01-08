# ProtonVPN Free Tier - Complete Guide

## ✅ Yes, ProtonVPN Free is FREE FOR LIFETIME!

### What You Get (Free Forever):
- ✅ **Unlimited bandwidth** (no data caps!)
- ✅ **3 server locations** (Netherlands, Japan, USA)
- ✅ **No ads**
- ✅ **No logs policy**
- ✅ **Works forever** - truly free lifetime

### What You DON'T Get (Free Tier):
- ❌ **No dedicated proxy servers** (but VPN works as proxy)
- ❌ **Limited to 1 device** (paid: 10 devices)
- ❌ **Slower speeds** (paid: faster)
- ❌ **Only 3 countries** (paid: 70+ countries)

---

## 🚀 How to Use ProtonVPN Free with Scraper

### Method 1: System VPN (Recommended)

1. **Sign up for free**: https://protonvpn.com
2. **Download ProtonVPN**: 
   - Linux: https://protonvpn.com/support/linux-vpn-setup/
   - Or use OpenVPN config files
3. **Connect to ProtonVPN** (any free server)
4. **Run scraper WITHOUT proxy** - it will use system VPN automatically

**In your `.env` file:**
```
# Leave VPN_PROXY empty - system VPN will be used
# VPN_PROXY=
```

Then run:
```bash
python simple_scraper.py
```

---

### Method 2: OpenVPN Config (More Control)

1. **Get OpenVPN configs**:
   - Log into ProtonVPN account
   - Go to Downloads → OpenVPN configuration files
   - Download free server configs (Netherlands, Japan, USA)

2. **Connect using OpenVPN**:
   ```bash
   sudo apt install openvpn
   sudo openvpn --config /path/to/protonvpn-config.ovpn
   ```

3. **Run scraper** - it will use the VPN connection

---

### Method 3: Use ProtonVPN CLI (Linux)

1. **Install ProtonVPN CLI**:
   ```bash
   # Ubuntu/Debian
   sudo apt install protonvpn-cli
   
   # Or from source
   git clone https://github.com/ProtonVPN/linux-cli
   cd linux-cli
   sudo ./protonvpn install
   ```

2. **Login and connect**:
   ```bash
   protonvpn login
   protonvpn connect -f  # Connect to fastest free server
   ```

3. **Run scraper**:
   ```bash
   python simple_scraper.py
   ```

---

## 📝 Step-by-Step Setup

### Quick Setup (5 minutes):

1. **Sign up** (free, no credit card):
   ```
   https://protonvpn.com/signup
   ```

2. **Download ProtonVPN**:
   - Linux: Use OpenVPN or CLI
   - Windows/Mac: Download app from website

3. **Connect to free server**:
   - Choose: Netherlands, Japan, or USA
   - Click Connect

4. **Verify connection**:
   ```bash
   curl https://api.ipify.org
   # Should show different IP (not your real IP)
   ```

5. **Run scraper** (no proxy needed):
   ```bash
   python simple_scraper.py
   ```

---

## ⚙️ Configuration for Scraper

### Option A: System VPN (Easiest)
- Connect ProtonVPN
- Leave `.env` empty or don't set `VPN_PROXY`
- Scraper uses system VPN automatically

### Option B: SOCKS5 Proxy (If Available)
ProtonVPN free tier doesn't provide SOCKS5 proxy, but you can:
- Use the VPN connection itself
- Or set up a local SOCKS5 proxy through the VPN

---

## 🔍 How to Check if It's Working

```bash
# Check your IP (should be different)
curl https://api.ipify.org

# Check VPN status
ip addr show | grep tun0  # Linux

# Test scraper
python simple_scraper.py
```

---

## 💡 Pro Tips

1. **Free servers can be slow** - Be patient
2. **Switch servers** if one is too slow
3. **Use during off-peak hours** for better speed
4. **For production**: Consider paid tier ($5/month) for faster speeds

---

## 🆚 Comparison: Free vs Paid

| Feature | Free | Paid ($5-10/month) |
|---------|------|-------------------|
| Bandwidth | ✅ Unlimited | ✅ Unlimited |
| Servers | 3 countries | 70+ countries |
| Speed | Slower | Faster |
| Devices | 1 | 10 |
| Proxy | ❌ No | ✅ Yes (SOCKS5) |
| Lifetime | ✅ Forever | ✅ Forever |

---

## ✅ Summary

**Yes, ProtonVPN Free is FREE FOR LIFETIME!**

- ✅ Unlimited bandwidth
- ✅ No expiration
- ✅ Works forever
- ✅ No credit card needed

**For the scraper:**
- Connect ProtonVPN
- Run scraper (no proxy config needed)
- System VPN will be used automatically

---

## 🚀 Quick Start Command

```bash
# 1. Sign up: https://protonvpn.com/signup
# 2. Install and connect ProtonVPN
# 3. Run scraper:
python simple_scraper.py
```

That's it! No proxy configuration needed when using system VPN.


