# Quick Reference Card

## 🎯 First Time Setup (One-Time Only)

```bash
./first_time_setup.sh
```

**What happens:**
1. Opens Chrome → Install VPN extension → Connect VPN
2. Press Enter → Scraper starts running continuously
3. Runs forever until you stop it (Ctrl+C)

---

## 🔄 Running After Setup

```bash
./start.sh
```

**What happens:**
- Scraper starts immediately
- Runs continuously until you stop it (Ctrl+C)
- Automatically scrapes every 5 minutes
- Saves new leads to Excel files

---

## 🛑 Stopping the Scraper

Press `Ctrl+C` in the terminal where it's running

---

## 📊 Access Web Interface

http://localhost:5000

---

## ✅ Summary

| When | Command | What It Does |
|------|---------|--------------|
| **First time** | `./first_time_setup.sh` | Setup VPN → Runs continuously |
| **After setup** | `./start.sh` | Runs continuously until stopped |
| **Stop** | `Ctrl+C` | Stops the scraper |

---

## 💡 Key Points

- ✅ **Runs continuously** (lifetime) until you stop it
- ✅ **Automatic scraping** every 5 minutes
- ✅ **VPN extension** saved after first setup
- ✅ **No manual intervention** needed after setup
- ✅ **Excel files** saved automatically

---

**That's it! Simple and automated!** 🎉

