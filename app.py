"""
Flask web application for scraping foreclosure data from Connecticut Judicial website

USER-FRIENDLY ONE-CLICK SOLUTION:
=================================
1. RUN THE APP:
   - Install dependencies: pip install -r requirements.txt
   - Run: python app.py
   - Open browser: http://localhost:5000
   - Click "Scrape Towns" button - that's it!

2. VPN SETUP (Choose one method):
   
   METHOD A - VPN Proxy (Recommended for clients):
   - Set environment variables:
     export VPN_PROXY="http://your-vpn-proxy:port"
     export VPN_PROXY_USER="username"  # Optional
     export VPN_PROXY_PASS="password"  # Optional
   - Or create a .env file with these variables
   
   METHOD B - VPN Extension in Scraper Chrome:
   - The scraper uses its own Chrome profile
   - First time: Chrome will open, install your VPN extension
   - Connect VPN in that Chrome window
   - Close Chrome, try scraping again - it will remember the extension
   
   METHOD C - System VPN:
   - Connect VPN at system level
   - The scraper will use system VPN automatically

FEATURES:
- Doesn't interfere with your existing Chrome sessions
- Uses separate Chrome profile for scraping
- Fully automated - just click and scrape
- No need to close other tabs or Chrome windows
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, send_file
import traceback as tb_module
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException
from bs4 import BeautifulSoup
import os
import time
import socket
import json
import uuid
from datetime import datetime, timedelta
import pandas as pd
import threading
import tempfile
import logging
from urllib.parse import urljoin
# import traceback (already imported as tb_module above)

# Define a function to get formatted traceback safely
def get_safe_traceback():
    try:
        return tb_module.format_exc()
    except:
        return "Could not generate traceback"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log")
    ]
)
logger = logging.getLogger(__name__)

DEBUG_LOG_PATH = "debug-5f1f4f.log"
DEBUG_SESSION_ID = "5f1f4f"
DEBUG_LOG_FALLBACK_PATH = os.path.join(os.path.dirname(__file__), "debug-5f1f4f.log")

def debug_log(run_id, hypothesis_id, location, message, data=None):
    """Write NDJSON debug logs for runtime hypothesis validation."""
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000)
    }
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        try:
            with open(DEBUG_LOG_FALLBACK_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception as log_error:
            logger.error(f"Debug log write failed at {location}: {log_error}")

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Import Google Sheets handler
try:
    from google_sheets_handler import GoogleSheetsHandler
    print("✅ Google Sheets handler loaded successfully")
except ImportError as e:
    GoogleSheetsHandler = None
    print(f"⚠️  Warning: Google Sheets handler not available. Error: {e}")
    print("   Install dependencies: pip install gspread google-auth")
except Exception as e:
    GoogleSheetsHandler = None
    print(f"⚠️  Warning: Google Sheets handler failed to load. Error: {e}")
    tb_module.print_exc()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for sessions

# Global progress tracking for real-time updates
scraping_progress = {
    'current': 0,
    'total': 0,
    'current_town': '',
    'leads_found': 0,
    'status': 'idle'
}

# Directory to store temporary lead files
LEADS_STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'temp_leads')
os.makedirs(LEADS_STORAGE_DIR, exist_ok=True)

# File to store last lead count for comparison
LAST_LEAD_COUNT_FILE = os.path.join(LEADS_STORAGE_DIR, 'last_lead_count.json')
LAST_EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'last_auto_export.xlsx')

# File to mark VPN extension setup as complete
VPN_SETUP_FLAG = os.path.join(os.path.dirname(__file__), '.vpn_extension_setup_complete')

# File to track scheduler run count for cleanup
SCHEDULER_COUNT_FILE = os.path.join(LEADS_STORAGE_DIR, '.scheduler_run_count.json')

# Cleanup old files (older than 1 hour)
def cleanup_old_lead_files():
    """Remove lead files older than 1 hour"""
    try:
        current_time = datetime.now()
        for filename in os.listdir(LEADS_STORAGE_DIR):
            filepath = os.path.join(LEADS_STORAGE_DIR, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if current_time - file_time > timedelta(hours=1):
                    os.remove(filepath)
    except Exception as e:
        print(f"Error cleaning up old files: {e}")


def cleanup_old_files_by_count():
    """
    After every 10 scheduler runs, delete the oldest 5 JSON files and 5 Excel files
    to prevent disk space from growing too much
    """
    try:
        # Get JSON files from temp_leads directory (excluding last_lead_count.json and .scheduler_run_count.json)
        json_files = []
        if os.path.exists(LEADS_STORAGE_DIR):
            for filename in os.listdir(LEADS_STORAGE_DIR):
                if filename.endswith('.json') and filename not in ['last_lead_count.json', '.scheduler_run_count.json']:
                    filepath = os.path.join(LEADS_STORAGE_DIR, filename)
                    if os.path.isfile(filepath):
                        json_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time (oldest first)
        json_files.sort(key=lambda x: x[1])
        
        # Delete oldest 5 JSON files
        deleted_json = 0
        for filepath, _ in json_files[:5]:
            try:
                os.remove(filepath)
                deleted_json += 1
                print(f"[CLEANUP] Deleted old JSON file: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"[CLEANUP] Error deleting JSON file {filepath}: {e}")
        
        # Get Excel files from project root
        excel_files = []
        project_dir = os.path.dirname(__file__)
        for filename in os.listdir(project_dir):
            if filename.startswith(('foreclosure_leads_', 'all_leads_', 'new_leads_')) and filename.endswith('.xlsx'):
                filepath = os.path.join(project_dir, filename)
                if os.path.isfile(filepath):
                    excel_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time (oldest first)
        excel_files.sort(key=lambda x: x[1])
        
        # Delete oldest 5 Excel files
        deleted_excel = 0
        for filepath, _ in excel_files[:5]:
            try:
                os.remove(filepath)
                deleted_excel += 1
                print(f"[CLEANUP] Deleted old Excel file: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"[CLEANUP] Error deleting Excel file {filepath}: {e}")
        
        if deleted_json > 0 or deleted_excel > 0:
            print(f"[CLEANUP] ✅ Cleanup completed: Deleted {deleted_json} JSON files and {deleted_excel} Excel files")
        else:
            print(f"[CLEANUP] No files to delete (less than 5 files of each type)")
            
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")
        import traceback
        traceback.print_exc()


def get_and_increment_scheduler_count():
    """Get current scheduler run count and increment it. Returns the count after increment."""
    try:
        count = 0
        if os.path.exists(SCHEDULER_COUNT_FILE):
            try:
                with open(SCHEDULER_COUNT_FILE, 'r') as f:
                    data = json.load(f)
                    count = data.get('count', 0)
            except:
                count = 0
        
        # Increment count
        count += 1
        
        # Save updated count
        with open(SCHEDULER_COUNT_FILE, 'w') as f:
            json.dump({
                'count': count,
                'last_run': datetime.now().isoformat()
            }, f, indent=2)
        
        return count
    except Exception as e:
        print(f"[SCHEDULER] Error managing scheduler count: {e}")
        return 1  # Return 1 if error, so cleanup happens on next run

# Run cleanup on startup
cleanup_old_lead_files()

# ============================================================================
# CONFIGURATION: Chrome settings
# ============================================================================
# Separate Chrome profile for scraping (doesn't interfere with user's Chrome)
SCRAPER_CHROME_PROFILE = os.path.join(os.path.dirname(__file__), ".scraper-chrome-profile")
os.makedirs(SCRAPER_CHROME_PROFILE, exist_ok=True)

# VPN/Proxy Configuration (optional - set if you have VPN proxy)
# Leave empty to use system VPN or Chrome extension
VPN_PROXY = os.getenv("VPN_PROXY", "")  # Format: "http://proxy-host:port" or "socks5://proxy-host:port"
VPN_PROXY_USER = os.getenv("VPN_PROXY_USER", "")
VPN_PROXY_PASS = os.getenv("VPN_PROXY_PASS", "")

# ============================================================================
# TARGET URL
# ============================================================================
TARGET_URL = "https://sso.eservices.jud.ct.gov/foreclosures/Public/PendPostbyTownList.aspx"
BASE_URL = "https://sso.eservices.jud.ct.gov/foreclosures/Public"


# Removed check_chrome_debugging_port - no longer using remote debugging


def is_driver_session_valid(driver):
    """Check if the driver session is still valid"""
    try:
        _ = driver.current_window_handle
        _ = driver.window_handles
        return True
    except:
        return False


def ensure_chrome_window(driver, timeout=25):
    """
    Chrome sometimes starts with no usable window when flags/profile conflict.
    Wait for at least one handle and focus it to avoid 'no such window' on first navigation.
    """
    try:
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) >= 1)
        driver.switch_to.window(driver.window_handles[0])
    except TimeoutException as e:
        raise Exception(
            "Chrome started without any browser window. "
            "Close any other Chrome using the scraper profile "
            f"({SCRAPER_CHROME_PROFILE}) and try again."
        ) from e


def collect_town_targets(driver):
    """
    Build town name + detail URL list from the main list page.
    Uses BeautifulSoup first, then Selenium (case-insensitive hrefs, real resolved URLs).
    """
    seen = set()
    targets = []

    def add_target(name, url):
        if not name or not url:
            return
        url = url.strip()
        if url in seen:
            return
        seen.add(url)
        targets.append({"name": name, "url": url})

    soup = BeautifulSoup(driver.page_source, "html.parser")
    panel = soup.find("div", id="ctl00_cphBody_Panel1")
    if panel:
        for link in panel.find_all("a", href=True):
            href = (link.get("href") or "").strip()
            hl = href.lower()
            if "pendpostbytowndetails" not in hl or "town=" not in hl:
                continue
            name = link.get_text(strip=True)
            full = urljoin(TARGET_URL, href)
            add_target(name, full)

    if not targets:
        try:
            anchors = driver.find_elements(
                By.CSS_SELECTOR,
                "#ctl00_cphBody_Panel1 a[href*='PendPostbyTownDetails'], "
                "#ctl00_cphBody_Panel1 a[href*='pendpostbytowndetails']",
            )
            for el in anchors:
                href = (el.get_attribute("href") or "").strip()
                if not href:
                    continue
                hl = href.lower()
                if "town=" not in hl:
                    continue
                name = (el.text or "").strip()
                add_target(name, href)
        except Exception as e:
            logger.warning("Selenium town link fallback failed: %s", e)

    return targets


def scrape_town_leads_from_page(driver, town_name, extraction_time):
    """
    Scrape leads from the currently loaded town detail page (simplified - only 4 fields)
    Returns list of lead dictionaries with: Sale Date, Docket Number, Type of Sale & Property Address, Extraction Time
    """
    leads = []
    
    try:
        # Wait for the table to load with retry logic
        wait = WebDriverWait(driver, 15)
        table_found = False
        
        try:
            # Try to find the table
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_GridView1")))
            table_found = True
        except:
            # Table not found - might mean no leads for this town
            # Wait a bit for page to fully load, then check page source
            time.sleep(1)
            page_source = driver.page_source.lower()
            
            # Check if page loaded successfully (look for town name or common elements)
            if "town of" in page_source or town_name.lower() in page_source:
                # Page loaded but no table - likely no leads
                print(f"    No table found for {town_name} (likely no leads)")
                return leads
            else:
                # Page might not have loaded properly
                print(f"    Page may not have loaded for {town_name}")
                return leads
        
        # Minimal wait for content
        time.sleep(0.3)
        
        # Parse HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table
        table = soup.find('table', id='ctl00_cphBody_GridView1')
        
        if table and table_found:
            # Find all data rows (skip header row)
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        # Extract only the 4 required fields
                        
                        # 1. Sale Date (in a span with <br> tag, format: "01/17/2026<br>12:00PM")
                        sale_date = ""
                        if len(cells) > 1:
                            sale_date_elem = cells[1].find('span') or cells[1]
                            # Replace <br> with space and clean up
                            sale_date = sale_date_elem.get_text(separator=' ', strip=True)
                            sale_date = ' '.join(sale_date.split())  # Normalize whitespace
                        
                        # 2. Docket Number (in an <a> tag)
                        docket_number = ""
                        if len(cells) > 2:
                            docket_link = cells[2].find('a')
                            if docket_link:
                                docket_number = docket_link.get_text(strip=True)
                            else:
                                docket_number = cells[2].get_text(strip=True)
                        
                        # 3. Type of Sale & Property Address (combined field)
                        type_and_address = ""
                        if len(cells) > 3:
                            property_elem = cells[3].find('span') or cells[3]
                            property_text = property_elem.get_text(separator=' ', strip=True)
                            type_and_address = ' '.join(property_text.split())  # Normalize whitespace
                        
                        # 4. Extraction Time (already provided as parameter)
                        
                        # Only add if we have essential data
                        if docket_number and sale_date:
                            leads.append({
                                'Sale Date': sale_date,
                                'Docket Number': docket_number,
                                'Type of Sale & Property Address': type_and_address,
                                'Extraction Time': extraction_time
                            })
                    except Exception as e:
                        print(f"    Error parsing row: {e}")
                        continue
        else:
            # Table not found in HTML either - no leads for this town
            print(f"    No table found in HTML for {town_name} (no leads)")
        
        print(f"  Found {len(leads)} leads for {town_name}")
        return leads
        
    except Exception as e:
        print(f"  Error scraping {town_name}: {e}")
        return leads


def scrape_town_leads(driver, town_name, original_window):
    """
    Scrape leads from a town's detail page
    Returns list of lead dictionaries
    """
    leads = []
    scraping_tab = None
    
    # Validate session before starting
    if not is_driver_session_valid(driver):
        print(f"    Warning: Invalid session for {town_name}, skipping...")
        return leads
    
    try:
        # Construct the town detail URL
        town_url = f"{BASE_URL}/PendPostbyTownDetails.aspx?town={town_name}"
        print(f"  Scraping leads for {town_name}...")
        
        # Get current window count before opening new tab
        windows_before = set(driver.window_handles)
        
        # Open URL in background tab
        driver.execute_script(f"window.open('{town_url}', '_blank');")
        
        # Wait a moment for the tab to actually open
        time.sleep(0.5)
        
        # Get the new tab handle - find the new window
        windows_after = set(driver.window_handles)
        new_windows = windows_after - windows_before
        
        if new_windows:
            scraping_tab = new_windows.pop()
        else:
            # Fallback: use the last window handle
            all_windows = driver.window_handles
            if original_window and original_window in all_windows:
                # Find a window that's not the original
                for handle in all_windows:
                    if handle != original_window:
                        scraping_tab = handle
                        break
            if not scraping_tab:
                scraping_tab = all_windows[-1] if all_windows else None
        
        if not scraping_tab:
            print(f"    Warning: Could not find new tab for {town_name}")
            return leads
        
        # Verify the window is still valid before switching
        if scraping_tab not in driver.window_handles:
            print(f"    Warning: Tab closed before switching for {town_name}")
            return leads
        
        # Switch to the background tab
        try:
            # Validate session before switching
            if not is_driver_session_valid(driver):
                print(f"    Session invalid before switching for {town_name}")
                return leads
            driver.switch_to.window(scraping_tab)
        except Exception as e:
            error_msg = str(e).lower()
            if 'invalid session' in error_msg or 'session' in error_msg:
                print(f"    Session expired for {town_name}")
            else:
                print(f"    Error switching to tab for {town_name}: {e}")
            return leads
        
        # Wait for page to load - check for either the table or a message indicating no leads
        wait = WebDriverWait(driver, 15)
        table_found = False
        
        try:
            # Try to find the table
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_GridView1")))
            table_found = True
        except:
            # Table not found - might mean no leads for this town
            # Wait a bit for page to fully load, then check page source
            time.sleep(1)
            page_source = driver.page_source.lower()
            
            # Check if page loaded successfully (look for town name or common elements)
            if "town of" in page_source or town_name.lower() in page_source:
                # Page loaded but no table - likely no leads
                print(f"    No table found for {town_name} (likely no leads)")
                # Close tab and return empty leads
                try:
                    if scraping_tab in driver.window_handles:
                        driver.close()
                    if original_window and original_window in driver.window_handles:
                        driver.switch_to.window(original_window)
                except:
                    pass
                return leads
            else:
                # Page might not have loaded properly
                print(f"    Page may not have loaded for {town_name}")
                try:
                    if scraping_tab in driver.window_handles:
                        driver.close()
                    if original_window and original_window in driver.window_handles:
                        driver.switch_to.window(original_window)
                except:
                    pass
                return leads
        
        # Minimal wait for content
        time.sleep(0.3)
        
        # Parse HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table
        table = soup.find('table', id='ctl00_cphBody_GridView1')
        
        if table and table_found:
            # Find all data rows (skip header row)
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        # Extract data from each cell
                        row_num = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                        
                        # Sale Date (in a span with <br> tag, format: "01/17/2026<br>12:00PM")
                        sale_date = ""
                        if len(cells) > 1:
                            sale_date_elem = cells[1].find('span') or cells[1]
                            # Replace <br> with space and clean up
                            sale_date = sale_date_elem.get_text(separator=' ', strip=True)
                            sale_date = ' '.join(sale_date.split())  # Normalize whitespace
                        
                        # Docket Number (in an <a> tag)
                        docket_number = ""
                        docket_url = ""
                        if len(cells) > 2:
                            docket_link = cells[2].find('a')
                            if docket_link:
                                docket_number = docket_link.get_text(strip=True)
                                href = docket_link.get('href', '')
                                if href:
                                    if href.startswith('http'):
                                        docket_url = href
                                    else:
                                        docket_url = f"{BASE_URL}/{href.lstrip('/')}"
                            else:
                                docket_number = cells[2].get_text(strip=True)
                        
                        # Type of Sale & Property Address (in a span)
                        property_text = ""
                        address = ""
                        sale_type = ""
                        if len(cells) > 3:
                            property_elem = cells[3].find('span') or cells[3]
                            property_text = property_elem.get_text(separator=' ', strip=True)
                            property_text = ' '.join(property_text.split())  # Normalize whitespace
                            
                            # Extract address and sale type from property text
                            # Format: "PUBLIC AUCTION FORECLOSURE SALE: Residential <br> ADDRESS:  40 James Street..."
                            if "ADDRESS:" in property_text.upper():
                                parts = property_text.split("ADDRESS:", 1)
                                if len(parts) > 1:
                                    # Extract sale type (everything before ADDRESS:)
                                    sale_type_part = parts[0].replace("PUBLIC AUCTION FORECLOSURE SALE:", "").strip()
                                    sale_type = sale_type_part if sale_type_part else "PUBLIC AUCTION FORECLOSURE SALE"
                                    # Extract address (everything after ADDRESS:)
                                    address = parts[1].strip()
                                else:
                                    address = property_text
                                    sale_type = "PUBLIC AUCTION FORECLOSURE SALE"
                            else:
                                address = property_text
                                sale_type = "PUBLIC AUCTION FORECLOSURE SALE"
                        
                        # View Full Notice link
                        view_notice_url = ""
                        if len(cells) > 4:
                            view_link = cells[4].find('a')
                            if view_link:
                                href = view_link.get('href', '')
                                if href:
                                    if href.startswith('http'):
                                        view_notice_url = href
                                    else:
                                        view_notice_url = f"{BASE_URL}/{href.lstrip('/')}"
                        
                        # Only add if we have essential data
                        if docket_number and sale_date:
                            leads.append({
                                'town': town_name,
                                'row_number': row_num,
                                'sale_date': sale_date,
                                'docket_number': docket_number,
                                'docket_url': docket_url,
                                'sale_type': sale_type,
                                'address': address,
                                'view_notice_url': view_notice_url
                            })
                    except Exception as e:
                        print(f"    Error parsing row: {e}")
                        continue
        else:
            # Table not found in HTML either - no leads for this town
            print(f"    No table found in HTML for {town_name} (no leads)")
        
        print(f"  Found {len(leads)} leads for {town_name}")
        return leads
        
    except Exception as e:
        print(f"  Error scraping {town_name}: {e}")
        return leads


def get_chrome_version():
    """Get installed Chrome version"""
    logger.info("Detecting Chrome version...")
    try:
        import subprocess
        import re
        import platform
        
        system = platform.system()
        logger.info(f"Operating System: {system}")
        
        if system == "Windows":
            # Try multiple registry locations
            try:
                result = subprocess.run(
                    ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        version = match.group(1)
                        logger.info(f"Found Chrome version in registry (HKCU): {version}")
                        return version
            except Exception as e:
                logger.debug(f"HKCU registry check failed: {e}")
            
            try:
                result = subprocess.run(
                    ['reg', 'query', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome', '/v', 'version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        version = match.group(1)
                        logger.info(f"Found Chrome version in registry (HKLM): {version}")
                        return version
            except Exception as e:
                logger.debug(f"HKLM registry check failed: {e}")
            
            # Try reading from Chrome executable using wmic (more reliable on Windows)
            try:
                result = subprocess.run(
                    ['wmic', 'datafile', 'where', 'name="C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version='):
                            version = line.split('=')[1].strip()
                            if version:
                                logger.info(f"Found Chrome version via wmic: {version}")
                                return version
            except Exception as e:
                logger.debug(f"wmic check failed: {e}")
            
            # Fallback: Try reading from Chrome executable using PowerShell
            chrome_paths = [
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ]
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    try:
                        result = subprocess.run(
                            ['powershell', '-Command', f'(Get-Item "{chrome_path}").VersionInfo.FileVersion'],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip()
                            if version:
                                logger.info(f"Found Chrome version via PowerShell at {chrome_path}: {version}")
                                return version
                    except Exception as e:
                        logger.debug(f"PowerShell check at {chrome_path} failed: {e}")
        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        version = match.group(1)
                        logger.info(f"Found Chrome version (macOS): {version}")
                        return version
            except Exception as e:
                logger.debug(f"macOS version check failed: {e}")
        else:  # Linux
            try:
                result = subprocess.run(
                    ['google-chrome', '--version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        version = match.group(1)
                        logger.info(f"Found Chrome version (Linux): {version}")
                        return version
            except Exception as e:
                logger.debug(f"Linux google-chrome version check failed: {e}")
    except Exception as e:
        logger.error(f"Could not detect Chrome version: {e}")
    return None


def get_chromedriver_path():
    """Get ChromeDriver path, handling webdriver-manager bug and version compatibility"""
    logger.info("Starting get_chromedriver_path()...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        import os
        import shutil
        
        # Get Chrome version to ensure compatibility
        chrome_version = get_chrome_version()
        if chrome_version:
            logger.info(f"Detected Chrome version: {chrome_version}")
            # Extract major version (e.g., 143.0.7499.193 -> 143)
            major_version = chrome_version.split('.')[0]
            logger.info(f"Chrome major version: {major_version}")
        else:
            logger.warning("Could not detect Chrome version, will download latest compatible ChromeDriver")
        
        logger.info("Downloading/updating ChromeDriver to match Chrome version...")
        
        # Force download with version detection
        driver_manager = ChromeDriverManager()
        driver_path = driver_manager.install()
        logger.info(f"webdriver-manager installed driver to: {driver_path}")
        # #region agent log
        debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="app.py:get_chromedriver_path:post_install",
            message="ChromeDriver manager install result",
            data={"driver_path": driver_path, "exists": os.path.exists(driver_path)}
        )
        # #endregion
        
        # Check if it's actually the chromedriver executable
        if os.path.isfile(driver_path) and os.access(driver_path, os.X_OK):
            # Check if it's not a text file (webdriver-manager bug)
            try:
                with open(driver_path, 'rb') as f:
                    header = f.read(4)
                    # ELF binary (Linux) or MZ (Windows) or Mach-O (macOS)
                    if header.startswith(b'\x7fELF') or header.startswith(b'MZ') or header.startswith(b'\xcf\xfa'):
                        logger.info(f"Verified executable at: {driver_path}")
                        # #region agent log
                        debug_log(
                            run_id="pre-fix",
                            hypothesis_id="H1",
                            location="app.py:get_chromedriver_path:binary_header",
                            message="Driver path points to executable binary",
                            data={"driver_path": driver_path, "header_hex": header.hex()}
                        )
                        # #endregion
                        return driver_path
                    else:
                        logger.warning(f"File at {driver_path} is not a valid executable binary")
            except Exception as e:
                logger.error(f"Error reading binary header at {driver_path}: {e}")
        
        # If driver_path is wrong, find the actual chromedriver
        # webdriver-manager extracts to a subdirectory
        logger.info(f"Searching for chromedriver binary in {os.path.dirname(driver_path)}...")
        driver_dir = os.path.dirname(driver_path)
        for root, dirs, files in os.walk(driver_dir):
            for file in files:
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        logger.info(f"Found executable at: {full_path}")
                        # #region agent log
                        debug_log(
                            run_id="pre-fix",
                            hypothesis_id="H1",
                            location="app.py:get_chromedriver_path:walk_result",
                            message="Resolved executable by directory walk",
                            data={"resolved_path": full_path}
                        )
                        # #endregion
                        return full_path
        
        # Fallback: try to find in common locations
        logger.warning(f"Fallback: returning driver_path as is: {driver_path}")
        return driver_path
    except Exception as e:
        logger.error(f"Critical error in get_chromedriver_path: {e}")
        logger.error(tb_module.format_exc())
        return None


def create_chrome_driver():
    """
    Create a separate Chrome WebDriver instance for scraping.
    This doesn't interfere with user's existing Chrome sessions.
    
    VPN Support:
    - If VPN_PROXY is set, uses proxy
    - Otherwise, uses system VPN or allows VPN extension in scraper Chrome
    """
    logger.info("Initializing Chrome Options...")
    chrome_options = Options()
    
    # Use persistent scraper profile so VPN extension/session can be reused.
    # If an explicit proxy is configured, isolate with a temp profile.
    use_temp_profile = bool(VPN_PROXY)
    profile_dir = tempfile.mkdtemp() if use_temp_profile else SCRAPER_CHROME_PROFILE
    logger.info(f"Using Chrome profile directory: {profile_dir}")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    # #region agent log
    debug_log(
        run_id="pre-fix",
        hypothesis_id="H2",
        location="app.py:create_chrome_driver:temp_profile",
        message="Chrome profile directory selected",
        data={
            "profile_dir": profile_dir,
            "is_temp_profile": use_temp_profile,
            "exists": os.path.isdir(profile_dir)
        }
    )
    # #endregion
    
    # Kill any existing Chrome instances using this profile
    try:
        import subprocess
        # Find Chrome processes using this profile
        logger.info(f"Attempting to kill existing Chrome processes using profile: {SCRAPER_CHROME_PROFILE}")
        # subprocess.run(["pkill", "-f", SCRAPER_CHROME_PROFILE], 
        #               stderr=subprocess.DEVNULL, timeout=2)
        # time.sleep(0.5)  # Wait a moment for processes to die
    except Exception as e:
        logger.debug(f"Process cleanup (pkill) failed or not needed: {e}")
    
    # Additional options for stability and compatibility
    logger.info("Setting Chrome flags...")
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # Keep extensions enabled unless an explicit proxy mode is used.
    if use_temp_profile:
        chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    # Avoid --remote-debugging-pipe: it can break Selenium sessions on Windows (window closes / no such window).
    crash_dump_dir = tempfile.gettempdir()
    logger.info(f"Setting crash dumps directory to: {crash_dump_dir}")
    chrome_options.add_argument(f"--crash-dumps-dir={crash_dump_dir}")
    
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent to avoid detection
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    logger.info(f"Using User-Agent: {user_agent}")
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Set page load strategy to 'eager' for faster loading (don't wait for all resources)
    chrome_options.page_load_strategy = 'eager'
    
    # Add connection settings
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-background-networking")
    
    # VPN/Proxy support
    if VPN_PROXY:
        logger.info(f"Using VPN proxy: {VPN_PROXY}")
        chrome_options.add_argument(f"--proxy-server={VPN_PROXY}")
        if VPN_PROXY_USER and VPN_PROXY_PASS:
            # Note: Selenium doesn't support proxy auth directly, 
            # but we can use an extension or handle it differently
            logger.info("Proxy credentials provided (note: selenium may need extra handling for this)")
            pass
    else:
        # No proxy configured - will use VPN extension if installed in Chrome profile
        logger.info("No proxy configured - using system VPN or Chrome extension (if installed)")
    
    # Check if ChromeDriver binary exists
    chrome_binary = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    if not os.path.exists(chrome_binary):
        chrome_binary = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    
    if os.path.exists(chrome_binary):
        logger.info(f"Setting binary_location to: {chrome_binary}")
        chrome_options.binary_location = chrome_binary
    
    try:
        # Try to get ChromeDriver path with version detection
        logger.info("Attempting to get ChromeDriver path...")
        driver_path = get_chromedriver_path()
        
        if driver_path and os.path.exists(driver_path):
            logger.info(f"Using ChromeDriver at: {driver_path}")
            service = Service(driver_path)
            # Set service timeout
            service.service_args = ['--timeout=60']
            logger.info("Starting webdriver.Chrome with service and options...")
            # #region agent log
            debug_log(
                run_id="pre-fix",
                hypothesis_id="H2,H3,H4",
                location="app.py:create_chrome_driver:before_webdriver_start",
                message="Launching webdriver with chrome options",
                data={
                    "driver_path": driver_path,
                    "chrome_binary": chrome_options.binary_location,
                    "has_headless_flag": "--headless" in chrome_options.arguments,
                    "has_disable_gpu_flag": "--disable-gpu" in chrome_options.arguments,
                    "has_disable_extensions_flag": "--disable-extensions" in chrome_options.arguments,
                    "page_load_strategy": chrome_options.page_load_strategy,
                    "args_count": len(chrome_options.arguments)
                }
            )
            # #endregion
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback: let Selenium find ChromeDriver automatically
            logger.warning("No specific driver path found, falling back to auto-detection...")
            driver = webdriver.Chrome(options=chrome_options)
        
        # Set timeouts for the driver
        logger.info("Setting driver timeouts...")
        driver.set_page_load_timeout(60)  # 60 seconds for page load
        driver.implicitly_wait(5)

        ensure_chrome_window(driver)

        logger.info("Chrome driver created successfully")
        # #region agent log
        debug_log(
            run_id="pre-fix",
            hypothesis_id="H5",
            location="app.py:create_chrome_driver:success",
            message="Webdriver session created successfully",
            data={"current_url": getattr(driver, "current_url", ""), "window_count": len(driver.window_handles)}
        )
        # #endregion
        return driver
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to initialize Chrome driver. Error: {error_msg}")
        logger.error(tb_module.format_exc())
        # #region agent log
        debug_log(
            run_id="pre-fix",
            hypothesis_id="H2,H3,H4,H5",
            location="app.py:create_chrome_driver:exception",
            message="Webdriver launch failed",
            data={
                "error": error_msg,
                "chrome_binary": chrome_options.binary_location,
                "has_headless_flag": "--headless" in chrome_options.arguments,
                "has_disable_gpu_flag": "--disable-gpu" in chrome_options.arguments,
                "has_disable_extensions_flag": "--disable-extensions" in chrome_options.arguments,
                "temp_profile_arg": next((arg for arg in chrome_options.arguments if arg.startswith("--user-data-dir=")), "")
            }
        )
        # #endregion
        
        error_msg_lower = error_msg.lower()

        # Prioritize network/timeout errors before compatibility heuristics
        if (
            "timeout" in error_msg_lower
            or "connection" in error_msg_lower
            or "err_connection_timed_out" in error_msg_lower
            or "net::err_" in error_msg_lower
        ):
            logger.error("Connection/Timeout error during driver creation.")
            raise Exception(
                f"Connection timeout during driver initialization: {error_msg}\n\n"
                f"This usually means VPN is not connected or the proxy is unreachable.\n\n"
                f"SOLUTION:\n"
                f"1. Check VPN connection\n"
                f"2. If using proxy, verify VPN_PROXY in .env file\n"
                f"3. Test VPN by accessing the site manually\n\n"
                f"Technical details: {error_msg}"
            )
        elif (
            "no such window" in error_msg_lower
            or "target window already closed" in error_msg_lower
            or "web view not found" in error_msg_lower
        ):
            raise Exception(
                "Chrome closed or lost the automation window. "
                f"Close any other Chrome using the same profile ({SCRAPER_CHROME_PROFILE}), "
                "then try again.\n\n"
                f"Technical details: {error_msg}"
            )
        # Check for ChromeDriver compatibility issues
        elif (
            "session not created" in error_msg_lower
            or "only supports chrome version" in error_msg_lower
            or "chromedriver" in error_msg_lower
            or "executable needs to be in path" in error_msg_lower
            or "unable to discover open window" in error_msg_lower
        ):
            chrome_version = get_chrome_version()
            version_info = f"\nDetected Chrome version: {chrome_version}\n" if chrome_version else "\n"
            
            logger.error(f"Detected potential compatibility issue. Chrome version: {chrome_version}")
            
            raise Exception(
                f"ChromeDriver compatibility error detected. This usually means ChromeDriver version doesn't match Chrome version.\n\n"
                f"{version_info}"
                f"SOLUTION:\n"
                f"1. The app will automatically download compatible ChromeDriver\n"
                f"2. Make sure Chrome browser is installed and up to date\n"
                f"3. Try scraping again - it should work automatically\n\n"
                f"Technical details: {error_msg}"
            )
        else:
            logger.error(f"Generic failure to initialize Chrome driver: {error_msg}")
            raise Exception(f"Failed to initialize Chrome driver: {error_msg}")


def load_page_with_retry(driver, url, max_retries=3, timeout=60):
    """Load a page with retry logic for connection timeouts"""
    for attempt in range(max_retries):
        try:
            print(f"Loading {url} (attempt {attempt + 1}/{max_retries})...")
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            return True
        except Exception as e:
            error_msg = str(e)
            err_low = error_msg.lower()
            if "no such window" in err_low or "target window already closed" in err_low:
                raise Exception(
                    "Chrome closed the automation window mid-load. "
                    f"Close any manual Chrome using the scraper profile ({SCRAPER_CHROME_PROFILE}), "
                    "then try again.\n\n"
                    f"Original error: {error_msg}"
                )
            if "timeout" in err_low:
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            if 'timeout' in err_low or 'connection' in err_low:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                    print(f"Connection timeout, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(
                        f"Connection timeout after {max_retries} attempts.\n\n"
                        f"This usually means:\n"
                        f"1. VPN is not connected or not working\n"
                        f"2. Network connection is unstable\n"
                        f"3. The website is blocking the connection\n\n"
                        f"SOLUTION:\n"
                        f"1. Check VPN connection\n"
                        f"2. Verify you can access the site manually in browser\n"
                        f"3. If using proxy, check VPN_PROXY in .env file\n"
                        f"4. Try again after ensuring VPN is active\n\n"
                        f"Original error: {error_msg}"
                    )
            else:
                raise
    return False


@app.route('/')
def index():
    """Main page - redirects to setup if VPN not configured"""
    # Check if VPN setup is complete (skip if VPN_PROXY is set)
    if not VPN_PROXY and not os.path.exists(VPN_SETUP_FLAG):
        return redirect(url_for('setup'))
    
    # Get leads from file if available
    leads = []
    lead_count = 0
    lead_file_id = session.get('lead_file_id')
    
    # First try to get from session file
    if lead_file_id:
        lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
        if os.path.exists(lead_file_path):
            try:
                with open(lead_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    leads = data.get('leads', [])
                    lead_count = data.get('lead_count', 0)
                    print(f"[INDEX] Loaded {lead_count} leads from file {lead_file_id}")
            except Exception as e:
                print(f"[INDEX] Error reading lead file: {e}")
        else:
            print(f"[INDEX] Lead file not found: {lead_file_path}")
    
    # Also check the latest count from scheduler's last_lead_count.json
    # This ensures we show the most up-to-date count
    if os.path.exists(LAST_LEAD_COUNT_FILE):
        try:
            with open(LAST_LEAD_COUNT_FILE, 'r', encoding='utf-8') as f:
                scheduler_data = json.load(f)
                scheduler_count = scheduler_data.get('count', 0)
                scheduler_leads = scheduler_data.get('leads', [])
                
                # Use scheduler data if it's more recent or if we don't have session data
                if scheduler_count > lead_count or (lead_count == 0 and scheduler_count > 0):
                    leads = scheduler_leads
                    lead_count = scheduler_count
                    print(f"[INDEX] Using scheduler data: {lead_count} leads")
        except Exception as e:
            print(f"[INDEX] Error reading scheduler data: {e}")
    
    # If still no leads, try to find the latest lead file
    if lead_count == 0:
        try:
            lead_files = [f for f in os.listdir(LEADS_STORAGE_DIR) 
                         if f.endswith('.json') and f != 'last_lead_count.json']
            if lead_files:
                # Sort by modification time, get the latest
                lead_files.sort(key=lambda x: os.path.getmtime(
                    os.path.join(LEADS_STORAGE_DIR, x)), reverse=True)
                latest_file = lead_files[0]
                latest_file_path = os.path.join(LEADS_STORAGE_DIR, latest_file)
                with open(latest_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    leads = data.get('leads', [])
                    lead_count = data.get('lead_count', len(leads))
                    print(f"[INDEX] Loaded {lead_count} leads from latest file {latest_file}")
        except Exception as e:
            print(f"[INDEX] Error finding latest file: {e}")
    
    return render_template('index.html', leads=leads, lead_count=lead_count)


@app.route('/setup')
def setup():
    """Setup page for VPN extension configuration"""
    setup_complete = os.path.exists(VPN_SETUP_FLAG) or bool(VPN_PROXY)
    return render_template('setup.html', setup_complete=setup_complete)


@app.route('/api/setup-status')
def setup_status():
    """Check VPN setup status"""
    setup_complete = os.path.exists(VPN_SETUP_FLAG) or bool(VPN_PROXY)
    return jsonify({
        'setup_complete': setup_complete,
        'has_proxy': bool(VPN_PROXY)
    })


@app.route('/api/open-chrome-for-vpn', methods=['POST'])
def open_chrome_for_vpn():
    """Open Chrome with scraper profile for VPN extension installation"""
    try:
        import subprocess
        
        # Find Chrome executable
        chrome_paths = [
            "google-chrome",
            "chromium-browser",
            "chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
        
        chrome_cmd = None
        for path in chrome_paths:
            try:
                result = subprocess.run(["which", path.split("/")[-1]], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    chrome_cmd = result.stdout.strip()
                    break
            except:
                continue
        
        if not chrome_cmd:
            # Try direct execution
            for path in chrome_paths:
                try:
                    subprocess.run([path, "--version"], 
                                 capture_output=True, timeout=2)
                    chrome_cmd = path
                    break
                except:
                    continue
        
        if not chrome_cmd:
            return jsonify({
                'success': False,
                'error': 'Chrome/Chromium not found. Please install Chrome first.'
            }), 400
        
        # Open Chrome with scraper profile
        subprocess.Popen([
            chrome_cmd,
            f"--user-data-dir={SCRAPER_CHROME_PROFILE}",
            "--new-window",
            "https://chrome.google.com/webstore"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return jsonify({
            'success': True,
            'message': 'Chrome opened successfully! Please install VPN extension and connect it.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to open Chrome: {str(e)}'
        }), 500


@app.route('/api/mark-setup-complete', methods=['POST'])
def mark_setup_complete():
    """Mark VPN extension setup as complete"""
    try:
        # Create the setup flag file
        with open(VPN_SETUP_FLAG, 'w') as f:
            f.write(f"Setup completed at {datetime.now().isoformat()}\n")
        
        return jsonify({
            'success': True,
            'message': 'Setup marked as complete! Redirecting to scraper...'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to mark setup complete: {str(e)}'
        }), 500


@app.route('/api/leads-status')
def leads_status():
    """Check if leads are available"""
    lead_file_id = session.get('lead_file_id')
    if lead_file_id:
        lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
        if os.path.exists(lead_file_path):
            try:
                with open(lead_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return jsonify({
                        'available': True,
                        'lead_count': data.get('lead_count', 0)
                    })
            except:
                pass
    return jsonify({'available': False})


@app.route('/download-excel')
def download_excel():
    """Download the Excel file with leads"""
    # First try to get filename from session
    excel_filename = session.get('excel_filename')
    if excel_filename:
        excel_file_path = os.path.join(os.path.dirname(__file__), excel_filename)
        if os.path.exists(excel_file_path):
            return send_file(
                excel_file_path,
                as_attachment=True,
                download_name=excel_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    
    # If not in session, try to get leads from lead_file_id and create Excel
    lead_file_id = session.get('lead_file_id')
    if lead_file_id:
        lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
        if os.path.exists(lead_file_path):
            try:
                with open(lead_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    leads = data.get('leads', [])
                    
                    if leads and len(leads) > 0:
                        # Create Excel file from leads
                        excel_filename = f"foreclosure_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        excel_file_path = os.path.join(os.path.dirname(__file__), excel_filename)
                        
                        # Create DataFrame from leads - include ALL data
                        df = pd.DataFrame(leads)
                        
                        print(f"📊 Creating Excel from {len(leads)} leads")
                        print(f"   DataFrame shape: {df.shape}")
                        print(f"   Columns: {list(df.columns)}")
                        
                        # Reorder columns for better readability (preferred order)
                        # But include ALL columns from the data
                        # Simplified structure: only 4 fields
                        column_order = ['Sale Date', 'Docket Number', 'Type of Sale & Property Address', 'Extraction Time']
                        
                        # Get all columns from data
                        all_columns = list(df.columns)
                        
                        # Reorder: preferred columns first, then any remaining columns
                        ordered_columns = []
                        for col in column_order:
                            if col in all_columns:
                                ordered_columns.append(col)
                        
                        # Add any remaining columns that weren't in the preferred order
                        for col in all_columns:
                            if col not in ordered_columns:
                                ordered_columns.append(col)
                        
                        # Reorder DataFrame columns
                        if ordered_columns:
                            df = df[ordered_columns]
                        
                        # Save to Excel (only if DataFrame has data)
                        if len(df) > 0:
                            df.to_excel(excel_file_path, index=False, engine='openpyxl')
                            print(f"✅ Created Excel file: {excel_file_path}")
                            print(f"   Saved {len(df)} rows with {len(df.columns)} columns")
                            print(f"   Columns in Excel: {list(df.columns)}")
                        else:
                            print(f"⚠️  Warning: DataFrame is empty, cannot create Excel file")
                            return jsonify({'error': 'No leads data available to create Excel file.'}), 404
                        
                        # Store in session for future downloads
                        session['excel_filename'] = excel_filename
                        
                        return send_file(
                            excel_file_path,
                            as_attachment=True,
                            download_name=excel_filename,
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
            except Exception as e:
                print(f"Error creating Excel from leads: {e}")
                tb_module.print_exc()
    
    # If still no file, try to find the latest Excel file in the directory
    try:
        excel_files = [f for f in os.listdir(os.path.dirname(__file__)) 
                      if f.startswith(('foreclosure_leads_', 'all_leads_', 'new_leads_')) and f.endswith('.xlsx')]
        if excel_files:
            # Sort by modification time, get the latest
            excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(os.path.dirname(__file__), x)), reverse=True)
            latest_file = excel_files[0]
            excel_file_path = os.path.join(os.path.dirname(__file__), latest_file)
            
            return send_file(
                excel_file_path,
                as_attachment=True,
                download_name=latest_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    except Exception as e:
        print(f"Error finding latest Excel file: {e}")
    
    return jsonify({'error': 'Excel file not found. Please scrape leads first.'}), 404


@app.route('/update-sheet', methods=['POST'])
def update_sheet():
    """Update Google Sheet with extracted leads in Excel format"""
    try:
        # Get leads from session
        lead_file_id = session.get('lead_file_id')
        lead_file_path = None
        
        if lead_file_id:
            lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
            if not os.path.exists(lead_file_path):
                lead_file_path = None  # Try fallback
        
        # Fallback: find the latest lead file
        if not lead_file_path or not os.path.exists(lead_file_path):
            try:
                if os.path.exists(LEADS_STORAGE_DIR):
                    lead_files = [f for f in os.listdir(LEADS_STORAGE_DIR) 
                                 if f.endswith('.json') and not f.startswith('.')]
                    if lead_files:
                        # Sort by modification time, get the latest
                        lead_files.sort(key=lambda x: os.path.getmtime(
                            os.path.join(LEADS_STORAGE_DIR, x)), reverse=True)
                        latest_file = lead_files[0]
                        lead_file_path = os.path.join(LEADS_STORAGE_DIR, latest_file)
                        print(f"Using latest lead file: {latest_file}")
            except Exception as e:
                print(f"Error finding latest lead file: {e}")
        
        leads = []
        
        # Try to load from JSON file
        if lead_file_path and os.path.exists(lead_file_path):
            try:
                with open(lead_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    leads = data.get('leads', [])
                    print(f"Loaded {len(leads)} leads from JSON file")
            except Exception as e:
                print(f"Error loading JSON file: {e}")
        
        # Fallback: Read from Excel file if JSON not found
        if not leads or len(leads) == 0:
            print("No leads from JSON, trying to read from Excel file...")
            try:
                # Try to get Excel filename from session
                excel_filename = session.get('excel_filename')
                excel_file_path = None
                project_dir = os.path.dirname(__file__)
                
                print(f"Session excel_filename: {excel_filename}")
                print(f"Project directory: {project_dir}")
                
                if excel_filename:
                    excel_file_path = os.path.join(project_dir, excel_filename)
                    print(f"Trying Excel file from session: {excel_file_path}")
                    if not os.path.exists(excel_file_path):
                        print(f"Excel file from session not found: {excel_file_path}")
                        excel_file_path = None
                    else:
                        print(f"Found Excel file from session: {excel_file_path}")
                
                # If not in session, find latest Excel file
                if not excel_file_path:
                    print("Searching for latest Excel file in project directory...")
                    try:
                        # Check project directory
                        all_files = os.listdir(project_dir)
                        print(f"Files in project directory: {len(all_files)} files")
                        excel_files = [f for f in all_files 
                                      if f.startswith(('foreclosure_leads_', 'all_leads_', 'new_leads_')) and f.endswith('.xlsx')]
                        print(f"Found {len(excel_files)} Excel files matching pattern in project dir")
                        
                        # Also check current working directory as fallback
                        if not excel_files:
                            cwd = os.getcwd()
                            print(f"Checking current working directory: {cwd}")
                            if cwd != project_dir:
                                try:
                                    cwd_files = os.listdir(cwd)
                                    excel_files = [f for f in cwd_files 
                                                  if f.startswith(('foreclosure_leads_', 'all_leads_', 'new_leads_')) and f.endswith('.xlsx')]
                                    print(f"Found {len(excel_files)} Excel files in CWD")
                                    if excel_files:
                                        project_dir = cwd
                                except:
                                    pass
                        
                        if excel_files:
                            excel_files.sort(key=lambda x: os.path.getmtime(
                                os.path.join(project_dir, x)), reverse=True)
                            excel_file_path = os.path.join(project_dir, excel_files[0])
                            print(f"Using latest Excel file: {excel_files[0]} (path: {excel_file_path})")
                        else:
                            print("No Excel files found matching pattern")
                    except Exception as list_error:
                        print(f"Error listing directory: {list_error}")
                        tb_module.print_exc()
                
                if excel_file_path and os.path.exists(excel_file_path):
                    print(f"Reading Excel file: {excel_file_path}")
                    # Read leads from Excel file
                    df = pd.read_excel(excel_file_path, engine='openpyxl')
                    print(f"Excel file read successfully. Shape: {df.shape}")
                    print(f"Columns: {list(df.columns)}")
                    
                    # Drop any completely empty rows
                    df = df.dropna(how='all')
                    print(f"After dropping empty rows: {df.shape}")
                    
                    # Convert DataFrame to list of dicts, replacing NaN with empty strings
                    leads = df.fillna('').to_dict('records')
                    print(f"Converted to {len(leads)} lead records")
                    
                    # Filter out completely empty records
                    leads = [lead for lead in leads if any(str(v).strip() for v in lead.values() if v != '')]
                    print(f"After filtering empty records: {len(leads)} leads")
                    
                    # Ensure column names match expected format
                    if leads and len(leads) > 0:
                        # Check if column names need mapping
                        first_lead = leads[0]
                        print(f"First lead keys: {list(first_lead.keys())}")
                        print(f"First lead sample: {dict(list(first_lead.items())[:2])}")
                else:
                    print(f"Excel file not found or doesn't exist: {excel_file_path}")
            except Exception as e:
                print(f"Error reading Excel file: {e}")
                tb_module.print_exc()
        
        print(f"Final leads count: {len(leads) if leads else 0}")
        if not leads or len(leads) == 0:
            # Last resort: Try to read from Excel file using same logic as download-excel
            print("Last resort: Trying to read Excel file using download-excel logic...")
            try:
                excel_filename = session.get('excel_filename')
                project_dir = os.path.dirname(__file__)
                
                if excel_filename:
                    excel_file_path = os.path.join(project_dir, excel_filename)
                    if os.path.exists(excel_file_path):
                        df = pd.read_excel(excel_file_path, engine='openpyxl')
                        df = df.dropna(how='all')
                        leads = df.fillna('').to_dict('records')
                        leads = [lead for lead in leads if any(str(v).strip() for v in lead.values() if v != '')]
                        print(f"Loaded {len(leads)} leads from session Excel file")
                
                # If still no leads, find latest Excel file
                if (not leads or len(leads) == 0):
                    excel_files = [f for f in os.listdir(project_dir) 
                                  if f.startswith(('foreclosure_leads_', 'all_leads_', 'new_leads_')) and f.endswith('.xlsx')]
                    if excel_files:
                        excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(project_dir, x)), reverse=True)
                        latest_file = excel_files[0]
                        excel_file_path = os.path.join(project_dir, latest_file)
                        df = pd.read_excel(excel_file_path, engine='openpyxl')
                        df = df.dropna(how='all')
                        leads = df.fillna('').to_dict('records')
                        leads = [lead for lead in leads if any(str(v).strip() for v in lead.values() if v != '')]
                        print(f"Loaded {len(leads)} leads from latest Excel file: {latest_file}")
            except Exception as final_error:
                print(f"Final attempt to read Excel failed: {final_error}")
                tb_module.print_exc()
        
        if not leads or len(leads) == 0:
            error_msg = 'No leads found. Please scrape leads first. (Checked JSON files and Excel files)'
            print(f"ERROR: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Check Google Sheets configuration
        if not GoogleSheetsHandler:
            return jsonify({'success': False, 'error': 'Google Sheets handler not available. Install gspread and google-auth.'}), 500
        
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        if not spreadsheet_id:
            return jsonify({'success': False, 'error': 'GOOGLE_SHEETS_ID not set in environment variables.'}), 400
        
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        if not os.path.exists(credentials_path) and not credentials_json:
            return jsonify({'success': False, 'error': f'Credentials file not found at {credentials_path} and GOOGLE_CREDENTIALS_JSON not set.'}), 400
        
        # Initialize Google Sheets handler
        handler = GoogleSheetsHandler(
            credentials_path=credentials_path if os.path.exists(credentials_path) else None,
            spreadsheet_id=spreadsheet_id,
            credentials_json=credentials_json
        )
        
        # Authenticate and get spreadsheet
        handler.authenticate()
        handler.get_or_create_spreadsheet()
        
        # Append leads in Excel format
        total_added = handler.append_leads_excel_format(leads)
        spreadsheet_url = handler.get_spreadsheet_url()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated Google Sheet with {total_added} leads.',
            'total_added': total_added,
            'spreadsheet_url': spreadsheet_url
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error updating Google Sheet: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/check-new-leads')
def check_new_leads():
    """Check if there are new leads and return current count"""
    current_count = 0
    current_leads = []
    timestamp = None
    
    # Get current count from scheduler file
    if os.path.exists(LAST_LEAD_COUNT_FILE):
        try:
            with open(LAST_LEAD_COUNT_FILE, 'r') as f:
                data = json.load(f)
                current_count = data.get('count', 0)
                current_leads = data.get('leads', [])
                timestamp = data.get('timestamp')
        except Exception as e:
            print(f"Error reading last lead count: {e}")
    
    return jsonify({
        'current_count': current_count,
        'leads': current_leads,
        'timestamp': timestamp
    })


@app.route('/api/health')
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'endpoints': {
            'scrape_data': '/scrape-data (POST)',
            'download_excel': '/download-excel (GET)',
            'health': '/api/health (GET)'
        }
    })


@app.route('/api/progress')
def get_progress():
    """Get current scraping progress for real-time updates"""
    return jsonify(scraping_progress)


@app.route('/scrape-data', methods=['POST'])
def scrape_data():
    """
    Simplified scraper: Gets all foreclosure data directly without town list step
    Extracts only 4 fields: Sale Date, Docket Number, Type of Sale & Property Address, Extraction Time
    """
    driver = None
    try:
        # Get extraction time (same for all records in this run)
        extraction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create Chrome driver
        driver = create_chrome_driver()
        
        # First, get all town names from the main page
        print(f"Loading main page: {TARGET_URL}")
        load_page_with_retry(driver, TARGET_URL, max_retries=3, timeout=60)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 30)  # Increased timeout
        try:
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_Panel1")))
        except TimeoutException:
            return jsonify({
                'success': False,
                'error': 'Town list did not load in time. Check VPN, then try again.'
            }), 400
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        panel = soup.find('div', id='ctl00_cphBody_Panel1')
        
        if not panel:
            return jsonify({
                'success': False,
                'error': 'Could not find the towns panel. The page structure may have changed or VPN is not connected.'
            }), 400

        town_targets = collect_town_targets(driver)
        
        if not town_targets:
            return jsonify({
                'success': False,
                'error': 'No town names found. Please verify VPN is connected and the page loaded correctly.'
            }), 400
        
        print(f"Found {len(town_targets)} towns. Starting to scrape foreclosure data...")
        
        # Initialize progress tracking
        scraping_progress['current'] = 0
        scraping_progress['total'] = len(town_targets)
        scraping_progress['current_town'] = ''
        scraping_progress['leads_found'] = 0
        scraping_progress['status'] = 'scraping'
        
        # Scrape leads from each town's detail page
        all_leads = []
        print(f"\nScraping foreclosure data from {len(town_targets)} towns...")
        
        # Process all towns by navigating to each URL directly
        for i, town_target in enumerate(town_targets, 1):
            town_name = town_target["name"]
            town_url = town_target["url"]
            # Update progress
            scraping_progress['current'] = i
            scraping_progress['current_town'] = town_name
            scraping_progress['leads_found'] = len(all_leads)
            
            print(f"[{i}/{len(town_targets)}] Processing {town_name}...")
            
            try:
                # Navigate to the town's detail page
                print(f"  Navigating to {town_name}...")
                try:
                    load_page_with_retry(driver, town_url, max_retries=2, timeout=45)
                except Exception as nav_error:
                    print(f"  Navigation error for {town_name}: {nav_error}")
                    # Try to continue with next town
                    continue
                
                # Scrape leads from the current page (with extraction time)
                town_leads = scrape_town_leads_from_page(driver, town_name, extraction_time)
                all_leads.extend(town_leads)
                
                # Update progress with new leads count
                scraping_progress['leads_found'] = len(all_leads)
                
                # Small delay between towns to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Failed to scrape {town_name}: {e}")
                continue
        
        print(f"\nTotal leads scraped: {len(all_leads)}")
        
        # Mark as complete
        scraping_progress['status'] = 'complete'
        scraping_progress['leads_found'] = len(all_leads)
        
        # Google Sheets integration
        new_leads = []
        duplicate_count = 0
        added_count = 0
        spreadsheet_url = None
        sheets_error = None
        
        try:
            if GoogleSheetsHandler:
                credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
                spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
                
                if not spreadsheet_id:
                    print("⚠️  GOOGLE_SHEETS_ID not set in environment variables. Skipping Google Sheets integration.")
                    sheets_error = "GOOGLE_SHEETS_ID environment variable not set"
                elif not os.path.exists(credentials_path) and not os.getenv('GOOGLE_CREDENTIALS_JSON'):
                    print(f"⚠️  Credentials file not found at {credentials_path} and GOOGLE_CREDENTIALS_JSON not set. Skipping Google Sheets integration.")
                    sheets_error = f"Credentials file not found at {credentials_path}"
                else:
                    print("\n🔗 Integrating with Google Sheets...")
                    print(f"   Using spreadsheet ID: {spreadsheet_id}")
                    
                    sheets_handler = GoogleSheetsHandler(
                        credentials_path=credentials_path,
                        spreadsheet_id=spreadsheet_id
                    )
                    
                    # Authenticate and get/create spreadsheet
                    sheets_handler.authenticate()
                    sheets_handler.get_or_create_spreadsheet()
                    
                    # Convert simplified lead format to Google Sheets format
                    formatted_leads = []
                    for lead in all_leads:
                        formatted_lead = {
                            'row_number': '',
                            'town': '',  # We don't have town in simplified version
                            'sale_date': lead.get('Sale Date', ''),
                            'docket_number': lead.get('Docket Number', ''),
                            'address': lead.get('Type of Sale & Property Address', ''),
                            'sale_type': '',  # Combined with address in simplified version
                            'docket_url': '',
                            'view_notice_url': '',
                            'extraction_time': lead.get('Extraction Time', '')
                        }
                        formatted_leads.append(formatted_lead)
                    
                    # Filter duplicates
                    print("🔍 Checking for duplicates...")
                    new_leads, duplicate_count = sheets_handler.filter_duplicates(formatted_leads)
                    print(f"  Found {len(new_leads)} new leads, {duplicate_count} duplicates")
                    
                    # Append new leads to Google Sheets
                    if new_leads:
                        print(f"📝 Appending {len(new_leads)} new leads to Google Sheets...")
                        added_count = sheets_handler.append_leads(new_leads)
                        print(f"✅ Successfully added {added_count} new records")
                    else:
                        print("ℹ️  No new leads to add (all duplicates)")
                    
                    # Get spreadsheet URL
                    spreadsheet_url = sheets_handler.get_spreadsheet_url()
                    print(f"✅ Google Sheets integration complete: {spreadsheet_url}")
            else:
                print("⚠️  Google Sheets handler not available. Skipping Google Sheets integration.")
                sheets_error = "Google Sheets handler not available. Install gspread and google-auth."
                new_leads = all_leads  # Use all leads as new if sheets not available
        except Exception as e:
            sheets_error = str(e)
            error_msg = f"Google Sheets integration failed: {str(e)}"
            print(f"❌ {error_msg}")
            tb_module.print_exc()
            
            # Log error to file
            try:
                log_dir = os.path.join(os.path.dirname(__file__), 'logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'google_sheets_errors.log')
                with open(log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().isoformat()
                    f.write(f"\n[{timestamp}] {error_msg}\n")
                    f.write(f"{tb_module.format_exc()}\n")
            except:
                pass
            
            # Continue without sheets - use all leads as new
            new_leads = all_leads
        
        # Save directly to Excel file with only the 4 required fields
        excel_filename = None
        excel_file_path = None
        
        if all_leads:
            try:
                excel_filename = f"foreclosure_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                excel_file_path = os.path.join(os.path.dirname(__file__), excel_filename)
                
                # Create DataFrame from leads (already has only 4 fields)
                df = pd.DataFrame(all_leads)
                
                # Ensure columns are in the correct order
                column_order = ['Sale Date', 'Docket Number', 'Type of Sale & Property Address', 'Extraction Time']
                # Only include columns that exist
                ordered_columns = [col for col in column_order if col in df.columns]
                
                if ordered_columns:
                    df = df[ordered_columns]
                
                # Save to Excel
                if len(df) > 0:
                    df.to_excel(excel_file_path, index=False, engine='openpyxl')
                    print(f"📊 Saved Excel file: {excel_filename}")
                    print(f"   Columns: {list(df.columns)}")
                    print(f"   Rows: {len(df)}")
                else:
                    print(f"⚠️  Warning: DataFrame is empty, cannot create Excel file")
                    excel_file_path = None
                    excel_filename = None
            except Exception as e:
                print(f"⚠️  Warning: Error saving Excel file: {e}")
                tb_module.print_exc()
                excel_file_path = None
                excel_filename = None
        
        # Store filename in session for download
        if excel_filename:
            session['excel_filename'] = excel_filename
        
        # Save leads to JSON file for update-sheet functionality
        if all_leads:
            try:
                lead_file_id = str(uuid.uuid4())
                lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
                
                lead_data = {
                    'leads': all_leads,
                    'lead_count': len(all_leads),
                    'scraped_at': datetime.now().isoformat(),
                    'excel_filename': excel_filename
                }
                
                with open(lead_file_path, 'w', encoding='utf-8') as f:
                    json.dump(lead_data, f, indent=2)
                
                session['lead_file_id'] = lead_file_id
                print(f"💾 Saved {len(all_leads)} leads to {lead_file_id}.json")
            except Exception as e:
                print(f"⚠️  Warning: Error saving leads to JSON file: {e}")
                tb_module.print_exc()
        
        # Return response
        return jsonify({
            'success': True,
            'total_scraped': len(all_leads),
            'lead_count': len(all_leads),
            'new_added': added_count,
            'duplicates_skipped': duplicate_count,
            'spreadsheet_url': spreadsheet_url,
            'excel_file': excel_filename if excel_file_path else None,
            'sheets_error': sheets_error,
            'message': f'Successfully scraped {len(all_leads)} foreclosure records. Added {added_count} new records to Google Sheets.'
        })
        
    except Exception as e:
        # logger.error(f"Critical error in scrape_data: {e}")
        # logger.error(get_safe_traceback())
        
        error_message = str(e)
        
        # Provide helpful error messages
        error_message_lower = error_message.lower()
        if (
            'timeout' in error_message_lower
            or 'connection' in error_message_lower
            or 'refused' in error_message_lower
            or 'net::err_' in error_message_lower
        ):
            error_message = f"Connection error: {error_message}\n\n" \
                          f"VPN Setup Required:\n" \
                          f"1. If using VPN proxy, create .env file with: VPN_PROXY=http://proxy:port\n" \
                          f"2. If using VPN extension, install it in scraper Chrome (first run)\n" \
                          f"3. If using system VPN, ensure it's connected\n" \
                          f"4. Verify you can access the website manually"
        elif (
            'no such window' in error_message_lower
            or 'target window already closed' in error_message_lower
            or 'web view not found' in error_message_lower
        ):
            error_message = (
                "Chrome closed or lost the automation window. "
                f"Close any other Chrome using the scraper profile "
                f"({SCRAPER_CHROME_PROFILE}), then try again.\n\n"
                f"Details: {error_message}"
            )
        elif (
            'session not created' in error_message_lower
            or 'only supports chrome version' in error_message_lower
            or 'chromedriver' in error_message_lower
            or 'unable to discover open window' in error_message_lower
            or '#0 0x' in error_message
        ):
            error_message = f"ChromeDriver compatibility error detected. This usually means ChromeDriver version doesn't match Chrome version.\n\n" \
                          f"SOLUTION:\n" \
                          f"1. The app will automatically download compatible ChromeDriver\n" \
                          f"2. Make sure Chrome browser is installed and up to date\n" \
                          f"3. Try scraping again - it should work automatically\n\n" \
                          f"Technical details: {error_message}"
        else:
            error_message = f"Error during scraping: {error_message}\n\n" \
                          f"If this is a VPN issue, ensure VPN is configured (see VPN Setup in README)"
        
        return jsonify({
            'success': False,
            'error': error_message
        }), 500
        
    finally:
        # Close the driver to free resources (we create a new one each time)
        if driver:
            try:
                logger.info("Closing Chrome driver...")
                driver.quit()
            except Exception as e:
                logger.warning(f"Error while quitting driver: {e}")
                pass


@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """
    Scrape town names from the target URL
    Returns JSON with list of town names
    """
    driver = None
    try:
        # Create Chrome driver with existing profile
        driver = create_chrome_driver()
        
        # Save the current window/tab (if any) to return to it later
        original_window = None
        try:
            original_window = driver.current_window_handle
        except:
            # No existing window, we'll create a temporary one
            pass
        
        # Navigate directly to the URL (simpler approach)
        print(f"Loading URL: {TARGET_URL}")
        load_page_with_retry(driver, TARGET_URL, max_retries=3, timeout=60)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 30)  # Increased timeout
        try:
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_Panel1")))
        except TimeoutException:
            return jsonify({
                'success': False,
                'error': 'Town list did not load in time. Check VPN, then try again.'
            }), 400
        
        # Find the panel div containing towns
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        panel = soup.find('div', id='ctl00_cphBody_Panel1')
        
        # Get scraping tab handle before closing
        scraping_tab_handle = driver.current_window_handle
        
        if not panel:
            # Close tab immediately on error
            try:
                driver.close()
                if original_window and original_window in driver.window_handles:
                    driver.switch_to.window(original_window)
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'Could not find the towns panel. The page structure may have changed or VPN is not connected.'
            }), 400
        
        town_targets = collect_town_targets(driver)
        town_names = [t["name"] for t in town_targets if t.get("name")]
        
        if not town_names:
            return jsonify({
                'success': False,
                'error': 'No town names found. Please verify VPN is connected and the page loaded correctly.\n\n' +
                         'VPN Setup:\n' +
                         '1. If using VPN proxy, set VPN_PROXY in .env file\n' +
                         '2. If using VPN extension, install it in the scraper Chrome (first run)\n' +
                         '3. If using system VPN, ensure it\'s connected'
            }), 400
        
        # Add towns to Google Sheets
        sheets_error = None
        spreadsheet_url = None
        added_count = 0
        
        try:
            if GoogleSheetsHandler:
                credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
                spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
                
                if not spreadsheet_id:
                    print("⚠️  GOOGLE_SHEETS_ID not set in environment variables. Skipping Google Sheets integration.")
                    sheets_error = "GOOGLE_SHEETS_ID environment variable not set"
                elif not os.path.exists(credentials_path) and not os.getenv('GOOGLE_CREDENTIALS_JSON'):
                    print(f"⚠️  Credentials file not found at {credentials_path} and GOOGLE_CREDENTIALS_JSON not set. Skipping Google Sheets integration.")
                    sheets_error = f"Credentials file not found at {credentials_path}"
                else:
                    print("\n🔗 Adding towns to Google Sheets...")
                    print(f"   Using spreadsheet ID: {spreadsheet_id}")
                    print(f"   Using credentials: {credentials_path}")
                    
                    sheets_handler = GoogleSheetsHandler(
                        credentials_path=credentials_path,
                        spreadsheet_id=spreadsheet_id
                    )
                    
                    # Authenticate and get/create spreadsheet
                    print("   Authenticating...")
                    sheets_handler.authenticate()
                    print("   Getting/creating spreadsheet...")
                    sheets_handler.get_or_create_spreadsheet()
                    
                    # Append towns to Google Sheets
                    print(f"📝 Adding {len(town_names)} towns to Google Sheets...")
                    added_count = sheets_handler.append_towns(town_names)
                    print(f"✅ Successfully added {added_count} towns to Google Sheets")
                    
                    # Get spreadsheet URL
                    spreadsheet_url = sheets_handler.get_spreadsheet_url()
                    print(f"✅ Google Sheets integration complete: {spreadsheet_url}")
            else:
                print("⚠️  Google Sheets handler not available. Skipping Google Sheets integration.")
                sheets_error = "Google Sheets handler not available. Install gspread and google-auth."
        except Exception as e:
            sheets_error = str(e)
            print(f"❌ Error adding towns to Google Sheets: {sheets_error}")
            tb_module.print_exc()
            error_msg = f"Google Sheets integration failed: {str(e)}"
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            try:
                log_file = os.path.join(log_dir, 'google_sheets_errors.log')
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n[{datetime.now().isoformat()}] {error_msg}\n")
                    f.write(f"{tb_module.format_exc()}\n")
            except:
                pass
        
        # Return success response
        return jsonify({
            'success': True,
            'town_count': len(town_names),
            'added_to_sheets': added_count,
            'spreadsheet_url': spreadsheet_url,
            'sheets_error': sheets_error
        })
        
    except Exception as e:
        # logger.error(f"Critical error in scrape route: {e}")
        # logger.error(get_safe_traceback())
        
        error_message = str(e)
        
        # Provide helpful error messages
        error_message_lower = error_message.lower()
        if (
            'timeout' in error_message_lower
            or 'connection' in error_message_lower
            or 'refused' in error_message_lower
            or 'net::err_' in error_message_lower
        ):
            error_message = f"Connection error: {error_message}\n\n" \
                          f"VPN Setup Required:\n" \
                          f"1. If using VPN proxy, create .env file with: VPN_PROXY=http://proxy:port\n" \
                          f"2. If using VPN extension, install it in scraper Chrome (first run)\n" \
                          f"3. If using system VPN, ensure it's connected\n" \
                          f"4. Verify you can access the website manually"
        elif (
            'no such window' in error_message_lower
            or 'target window already closed' in error_message_lower
            or 'web view not found' in error_message_lower
        ):
            error_message = (
                "Chrome closed or lost the automation window. "
                f"Close any other Chrome using the scraper profile "
                f"({SCRAPER_CHROME_PROFILE}), then try again.\n\n"
                f"Details: {error_message}"
            )
        elif (
            'session not created' in error_message_lower
            or 'only supports chrome version' in error_message_lower
            or 'chromedriver' in error_message_lower
            or 'unable to discover open window' in error_message_lower
            or '#0 0x' in error_message
        ):
            error_message = f"ChromeDriver compatibility error detected. This usually means ChromeDriver version doesn't match Chrome version.\n\n" \
                          f"SOLUTION:\n" \
                          f"1. The app will automatically download compatible ChromeDriver\n" \
                          f"2. Make sure Chrome browser is installed and up to date\n" \
                          f"3. Try scraping again - it should work automatically\n\n" \
                          f"Technical details: {error_message}"
        else:
            error_message = f"Error during scraping: {error_message}\n\n" \
                          f"If this is a VPN issue, ensure VPN is configured (see VPN Setup in README)"
        
        return jsonify({
            'success': False,
            'error': error_message
        }), 500
        
    finally:
        # Close the driver to free resources (we create a new one each time)
        if driver:
            try:
                logger.info("Closing Chrome driver...")
                driver.quit()
            except Exception as e:
                logger.warning(f"Error while quitting driver: {e}")
                pass


# Error handlers for better JSON responses
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response"""
    return jsonify({
        'success': False,
        'error': f'Endpoint not found: {request.path}. Please check the URL and ensure the Flask server is running with the latest code.'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response"""
    return jsonify({
        'success': False,
        'error': f'Internal server error: {str(error)}. Please check the server logs for more details.'
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions with JSON response"""
    return jsonify({
        'success': False,
        'error': f'Unexpected error: {str(e)} (at handler)'
    }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("Town Scraper Web Application")
    print("=" * 70)
    print(f"Scraper Chrome Profile: {SCRAPER_CHROME_PROFILE}")
    print(f"Target URL: {TARGET_URL}")
    if VPN_PROXY:
        print(f"VPN Proxy: {VPN_PROXY}")
    else:
        print("VPN: Using system VPN or extension (configure in .env if needed)")
    
    # Print available routes for debugging
    print("\nAvailable routes:")
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    
    print("\nStarting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 70)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        print("Done.")
