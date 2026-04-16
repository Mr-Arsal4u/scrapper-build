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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import time
import socket
import json
import uuid
from datetime import datetime, timedelta
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for sessions

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


def scrape_town_leads_from_page(driver, town_name):
    """
    Scrape leads from the currently loaded town detail page (single tab approach)
    Returns list of lead dictionaries
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


def get_chromedriver_path():
    """Get ChromeDriver path, handling webdriver-manager bug"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        import os
        
        # Get the cache directory
        cache_dir = os.path.expanduser("~/.wdm")
        driver_path = ChromeDriverManager().install()
        
        # Check if it's actually the chromedriver executable
        if os.path.isfile(driver_path) and os.access(driver_path, os.X_OK):
            # Check if it's not a text file (webdriver-manager bug)
            try:
                with open(driver_path, 'rb') as f:
                    header = f.read(4)
                    # ELF binary (Linux) or MZ (Windows) or Mach-O (macOS)
                    if header.startswith(b'\x7fELF') or header.startswith(b'MZ') or header.startswith(b'\xcf\xfa'):
                        return driver_path
            except:
                pass
        
        # If driver_path is wrong, find the actual chromedriver
        # webdriver-manager extracts to a subdirectory
        driver_dir = os.path.dirname(driver_path)
        for root, dirs, files in os.walk(driver_dir):
            for file in files:
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        return full_path
        
        # Fallback: try to find in common locations
        return driver_path
    except Exception as e:
        print(f"Warning: Could not use webdriver-manager: {e}")
        return None


def create_chrome_driver():
    """
    Create a separate Chrome WebDriver instance for scraping.
    This doesn't interfere with user's existing Chrome sessions.
    
    VPN Support:
    - If VPN_PROXY is set, uses proxy
    - Otherwise, uses system VPN or allows VPN extension in scraper Chrome
    """
    chrome_options = Options()
    
    # Use separate profile for scraping (doesn't interfere with user's Chrome)
    # This profile can have VPN extensions installed
    # Add timestamp to make it unique if needed
    import uuid
    unique_profile = f"{SCRAPER_CHROME_PROFILE}-{uuid.uuid4().hex[:8]}"
    chrome_options.add_argument(f"--user-data-dir={SCRAPER_CHROME_PROFILE}")
    
    # Kill any existing Chrome instances using this profile
    try:
        import subprocess
        # Find Chrome processes using this profile
        subprocess.run(["pkill", "-f", SCRAPER_CHROME_PROFILE], 
                      stderr=subprocess.DEVNULL, timeout=2)
        time.sleep(0.5)  # Wait a moment for processes to die
    except:
        pass  # Ignore errors
    
    # Additional options for stability and compatibility
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent to avoid detection
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Set page load strategy
    chrome_options.page_load_strategy = 'normal'
    
    # VPN/Proxy support
    if VPN_PROXY:
        print(f"Using VPN proxy: {VPN_PROXY}")
        chrome_options.add_argument(f"--proxy-server={VPN_PROXY}")
        if VPN_PROXY_USER and VPN_PROXY_PASS:
            # Note: Selenium doesn't support proxy auth directly, 
            # but we can use an extension or handle it differently
            pass
    else:
        # No proxy configured - will use VPN extension if installed in Chrome profile
        print("No proxy configured - using system VPN or Chrome extension (if installed)")
        print("💡 Tip: Install a VPN extension in the scraper's Chrome for easy VPN access")
    
    try:
        # Try to get ChromeDriver path
        driver_path = get_chromedriver_path()
        
        if driver_path and os.path.exists(driver_path):
            print(f"Using ChromeDriver: {driver_path}")
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback: let Selenium find ChromeDriver automatically
            print("Using system ChromeDriver...")
            driver = webdriver.Chrome(options=chrome_options)
        
        print("Chrome driver created successfully")
        return driver
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful error message
        if "chromedriver" in error_msg.lower() or "executable" in error_msg.lower():
            raise Exception(
                f"ChromeDriver error: {error_msg}\n\n"
                f"SOLUTION:\n"
                f"1. Make sure Chrome browser is installed\n"
                f"2. The app will try to download ChromeDriver automatically\n"
                f"3. If it fails, you can manually install ChromeDriver:\n"
                f"   - Download from: https://chromedriver.chromium.org/\n"
                f"   - Extract and add to PATH\n\n"
                f"Original error: {error_msg}"
            )
        else:
            raise Exception(f"Failed to initialize Chrome driver: {error_msg}")


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
                        column_order = ['row_number', 'town', 'sale_date', 'docket_number', 'address', 'sale_type', 'docket_url', 'view_notice_url']
                        
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
                import traceback
                traceback.print_exc()
    
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


@app.route('/trigger-scheduler', methods=['POST'])
def trigger_scheduler():
    """Manually trigger the automated scrape job"""
    try:
        # Run the job in a background thread to avoid blocking
        import threading
        thread = threading.Thread(target=automated_scrape_job)
        thread.daemon = True
        thread.start()
        return jsonify({
            'success': True,
            'message': 'Automated scrape job started in background'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/scheduler-status')
def scheduler_status():
    """Get status of the scheduler and last run"""
    status = {
        'scheduler_running': True,
        'last_run': None,
        'last_count': 0,
        'next_run': None,
        'leads': []
    }
    
    # Get last run info from file
    if os.path.exists(LAST_LEAD_COUNT_FILE):
        try:
            with open(LAST_LEAD_COUNT_FILE, 'r') as f:
                data = json.load(f)
                status['last_run'] = data.get('timestamp')
                status['last_count'] = data.get('count', 0)
                status['leads'] = data.get('leads', [])
        except:
            pass
    
    return jsonify(status)


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


@app.route('/scrape-leads', methods=['POST'])
def scrape_leads():
    """
    Scrape leads from town detail pages
    Expects JSON with 'towns' array in request body
    """
    driver = None
    try:
        # Get town names from request
        data = request.get_json()
        if not data or 'towns' not in data:
            return jsonify({
                'success': False,
                'error': 'No towns provided. Please scrape towns first.'
            }), 400
        
        town_names = data['towns']
        if not town_names or len(town_names) == 0:
            return jsonify({
                'success': False,
                'error': 'Town list is empty.'
            }), 400
        
        # Create Chrome driver
        driver = create_chrome_driver()
        
        # Save the current window/tab (if any) to return to it later
        original_window = None
        try:
            original_window = driver.current_window_handle
        except:
            pass
        
        # Scrape leads from each town's detail page using a single persistent tab
        all_leads = []
        print(f"\nScraping leads from {len(town_names)} towns...")
        print("Using single persistent tab for all towns (more stable)...")
        
        # Process all towns by navigating to each URL directly
        for i, town_name in enumerate(town_names, 1):
            print(f"[{i}/{len(town_names)}] Processing {town_name}...")
            
            try:
                # Construct the town detail URL
                town_url = f"{BASE_URL}/PendPostbyTownDetails.aspx?town={town_name}"
                
                # Navigate to the town's detail page
                print(f"  Navigating to {town_name}...")
                try:
                    driver.get(town_url)
                except Exception as nav_error:
                    print(f"  Navigation error for {town_name}: {nav_error}")
                    # Try to continue with next town
                    continue
                
                # Scrape leads from the current page
                town_leads = scrape_town_leads_from_page(driver, town_name)
                all_leads.extend(town_leads)
                
                # Small delay between towns to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Failed to scrape {town_name}: {e}")
                continue
        
        print(f"\nTotal leads scraped: {len(all_leads)}")
        
        # Store leads in a temporary file instead of session (session cookies are too small)
        lead_file_id = str(uuid.uuid4())
        lead_file_path = os.path.join(LEADS_STORAGE_DIR, f"{lead_file_id}.json")
        excel_file_path = None
        
        try:
            # Save to JSON file
            with open(lead_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'leads': all_leads,
                    'lead_count': len(all_leads),
                    'created_at': datetime.now().isoformat()
                }, f, indent=2)
            
            # Also save to Excel file
            excel_file_path = None
            excel_filename = None
            if all_leads:
                excel_filename = f"foreclosure_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                excel_file_path = os.path.join(os.path.dirname(__file__), excel_filename)
                
                # Create DataFrame from leads - include ALL data
                df = pd.DataFrame(all_leads)
                
                print(f"📊 Creating Excel from {len(all_leads)} leads")
                print(f"   DataFrame shape: {df.shape}")
                print(f"   Columns: {list(df.columns)}")
                
                # Reorder columns for better readability (preferred order)
                # But include ALL columns from the data
                column_order = ['row_number', 'town', 'sale_date', 'docket_number', 'address', 'sale_type', 'docket_url', 'view_notice_url']
                
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
                
                # Save to Excel
                try:
                    if len(df) > 0:
                        df.to_excel(excel_file_path, index=False, engine='openpyxl')
                        print(f"✅ Saved {len(all_leads)} leads to Excel: {excel_file_path}")
                        print(f"   DataFrame shape: {df.shape}")
                        print(f"   Columns in Excel: {list(df.columns)}")
                    else:
                        print(f"⚠️  Warning: DataFrame is empty, not saving Excel file")
                        excel_file_path = None
                        excel_filename = None
                except Exception as e:
                    print(f"❌ Error saving Excel file: {e}")
                    import traceback
                    traceback.print_exc()
                    excel_file_path = None
                    excel_filename = None
            
            # Only store the file ID in session (small)
            session['lead_file_id'] = lead_file_id
            session['scrape_completed'] = True
            if excel_file_path:
                session['excel_filename'] = excel_filename
            
            # Cleanup old files
            cleanup_old_lead_files()
        except Exception as e:
            print(f"Error saving leads to file: {e}")
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': True,
            'leads': all_leads,  # Still return in response for immediate display
            'lead_count': len(all_leads),
            'redirect': True,  # Signal frontend to redirect
            'excel_file': excel_filename if excel_file_path else None
        })
        
    except Exception as e:
        error_message = str(e)
        
        # Provide helpful error messages
        if 'stacktrace' in error_message.lower() or 'unknown' in error_message.lower() or '#0 0x' in error_message:
            error_message = f"ChromeDriver compatibility error detected.\n\n" \
                          f"This usually means ChromeDriver version doesn't match Chrome version.\n\n" \
                          f"SOLUTION:\n" \
                          f"1. The app will automatically download compatible ChromeDriver\n" \
                          f"2. Make sure Chrome browser is installed and up to date\n" \
                          f"3. Try scraping again - it should work automatically\n\n" \
                          f"Technical details: {error_message[:200]}"
        elif 'timeout' in error_message.lower() or 'connection' in error_message.lower() or 'refused' in error_message.lower():
            error_message = f"Connection error: {error_message}\n\n" \
                          f"VPN Setup Required:\n" \
                          f"1. If using VPN proxy, create .env file with: VPN_PROXY=http://proxy:port\n" \
                          f"2. If using VPN extension, install it in scraper Chrome (first run)\n" \
                          f"3. If using system VPN, ensure it's connected\n" \
                          f"4. Verify you can access the website manually"
        elif 'chromedriver' in error_message.lower() or 'executable' in error_message.lower():
            error_message = f"ChromeDriver error: {error_message}\n\n" \
                          f"SOLUTION:\n" \
                          f"1. Make sure Chrome browser is installed\n" \
                          f"2. The app will try to download ChromeDriver automatically\n" \
                          f"3. If it fails, check internet connection and try again"
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
                driver.quit()
            except:
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
        driver.get(TARGET_URL)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_Panel1")))
        
        # Minimal wait for dynamic content (reduced from 3 seconds)
        time.sleep(0.5)
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the panel div containing towns
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
        
        # Extract all <a> tags inside the panel
        town_links = panel.find_all('a')
        town_names = []
        
        for link in town_links:
            town_name = link.get_text(strip=True)
            # Only add non-empty town names
            if town_name:
                town_names.append(town_name)
        
        if not town_names:
            return jsonify({
                'success': False,
                'error': 'No town names found. Please verify VPN is connected and the page loaded correctly.\n\n' +
                         'VPN Setup:\n' +
                         '1. If using VPN proxy, set VPN_PROXY in .env file\n' +
                         '2. If using VPN extension, install it in the scraper Chrome (first run)\n' +
                         '3. If using system VPN, ensure it\'s connected'
            }), 400
        
        # Return only town names (leads will be scraped separately when button is clicked)
        return jsonify({
            'success': True,
            'towns': town_names,
            'town_count': len(town_names)
        })
        
    except Exception as e:
        error_message = str(e)
        
        # Provide helpful error messages
        if 'stacktrace' in error_message.lower() or 'unknown' in error_message.lower() or '#0 0x' in error_message:
            error_message = f"ChromeDriver compatibility error detected.\n\n" \
                          f"This usually means ChromeDriver version doesn't match Chrome version.\n\n" \
                          f"SOLUTION:\n" \
                          f"1. The app will automatically download compatible ChromeDriver\n" \
                          f"2. Make sure Chrome browser is installed and up to date\n" \
                          f"3. Try scraping again - it should work automatically\n\n" \
                          f"Technical details: {error_message[:200]}"
        elif 'timeout' in error_message.lower() or 'connection' in error_message.lower() or 'refused' in error_message.lower():
            error_message = f"Connection error: {error_message}\n\n" \
                          f"VPN Setup Required:\n" \
                          f"1. If using VPN proxy, create .env file with: VPN_PROXY=http://proxy:port\n" \
                          f"2. If using VPN extension, install it in scraper Chrome (first run)\n" \
                          f"3. If using system VPN, ensure it's connected\n" \
                          f"4. Verify you can access the website manually"
        elif 'chromedriver' in error_message.lower() or 'executable' in error_message.lower():
            error_message = f"ChromeDriver error: {error_message}\n\n" \
                          f"SOLUTION:\n" \
                          f"1. Make sure Chrome browser is installed\n" \
                          f"2. The app will try to download ChromeDriver automatically\n" \
                          f"3. If it fails, check internet connection and try again"
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
                driver.quit()
            except:
                pass


def automated_scrape_job():
    """
    Automated job that runs every 5 minutes:
    1. Scrapes town list
    2. Scrapes leads from all towns
    3. Compares with previous count
    4. Saves only new leads to Excel if count increased
    """
    # Get and increment scheduler run count
    scheduler_run_count = get_and_increment_scheduler_count()
    
    print("\n" + "=" * 70)
    print(f"[SCHEDULER] Automated scrape started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[SCHEDULER] Run count: {scheduler_run_count}")
    print("=" * 70)
    
    # Cleanup old files after every 10 runs
    if scheduler_run_count % 10 == 0:
        print(f"[SCHEDULER] 🧹 Cleanup triggered (every 10 runs) - Deleting oldest 5 JSON and 5 Excel files...")
        cleanup_old_files_by_count()
    
    driver = None
    try:
        # Step 1: Get town list
        print("[SCHEDULER] Step 1: Scraping town list...")
        town_names = []
        
        try:
            driver = create_chrome_driver()
            driver.get(TARGET_URL)
            
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_Panel1")))
            time.sleep(0.5)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            panel = soup.find('div', id='ctl00_cphBody_Panel1')
            
            if not panel:
                print("[SCHEDULER] ERROR: Could not find towns panel")
                if driver:
                    driver.quit()
                return
            
            town_links = panel.find_all('a')
            for link in town_links:
                town_name = link.get_text(strip=True)
                if town_name:
                    town_names.append(town_name)
            
            print(f"[SCHEDULER] Found {len(town_names)} towns")
            
            if not town_names:
                print("[SCHEDULER] No towns found, skipping...")
                if driver:
                    driver.quit()
                return
            
        except Exception as e:
            print(f"[SCHEDULER] ERROR getting town list: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return
        
        # Step 2: Scrape leads from all towns (reuse same driver)
        print(f"[SCHEDULER] Step 2: Scraping leads from {len(town_names)} towns...")
        all_leads = []
        
        try:
            for i, town_name in enumerate(town_names, 1):
                print(f"[SCHEDULER] [{i}/{len(town_names)}] Processing {town_name}...")
                
                try:
                    town_url = f"{BASE_URL}/PendPostbyTownDetails.aspx?town={town_name}"
                    driver.get(town_url)
                    town_leads = scrape_town_leads_from_page(driver, town_name)
                    all_leads.extend(town_leads)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[SCHEDULER] Error scraping {town_name}: {e}")
                    continue
            
            print(f"[SCHEDULER] Total leads scraped: {len(all_leads)}")
            
        except Exception as e:
            print(f"[SCHEDULER] ERROR during lead scraping: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        # Step 3: Compare with previous count and save new leads
        print("[SCHEDULER] Step 3: Comparing with previous count...")
        
        # Load previous count
        previous_count = 0
        previous_leads = []
        if os.path.exists(LAST_LEAD_COUNT_FILE):
            try:
                with open(LAST_LEAD_COUNT_FILE, 'r') as f:
                    data = json.load(f)
                    previous_count = data.get('count', 0)
                    previous_leads = data.get('leads', [])
            except Exception as e:
                print(f"[SCHEDULER] Error loading previous count: {e}")
        
        current_count = len(all_leads)
        
        print(f"[SCHEDULER] Previous count: {previous_count}, Current count: {current_count}")
        
        # Step 4: If count increased, save new leads
        if current_count > previous_count:
            print(f"[SCHEDULER] ✅ Lead count increased! ({previous_count} → {current_count})")
            print(f"[SCHEDULER] Finding new leads...")
            
            # Get new leads (by comparing docket numbers)
            previous_dockets = {lead.get('docket_number', '') for lead in previous_leads if lead.get('docket_number')}
            new_leads = [lead for lead in all_leads 
                        if lead.get('docket_number', '') and 
                        lead.get('docket_number', '') not in previous_dockets]
            
            if new_leads:
                print(f"[SCHEDULER] ✅ Found {len(new_leads)} new leads!")
                print(f"[SCHEDULER] Count increased: {previous_count} → {current_count}")
                
                # Save new leads to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_filename = f"new_leads_{timestamp}.xlsx"
                excel_file_path = os.path.join(os.path.dirname(__file__), excel_filename)
                
                df = pd.DataFrame(new_leads)
                
                # Reorder columns for better readability (preferred order)
                # But include ALL columns from the data
                column_order = ['row_number', 'town', 'sale_date', 'docket_number', 'address', 
                              'sale_type', 'docket_url', 'view_notice_url']
                
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
                
                df.to_excel(excel_file_path, index=False, engine='openpyxl')
                print(f"[SCHEDULER] ✅ Saved {len(new_leads)} new leads to: {excel_filename}")
                print(f"[SCHEDULER]    Columns: {list(df.columns)}")
                
                # Also save full leads list
                full_excel_filename = f"all_leads_{timestamp}.xlsx"
                full_excel_path = os.path.join(os.path.dirname(__file__), full_excel_filename)
                df_all = pd.DataFrame(all_leads)
                
                # Reorder columns for full leads too
                if ordered_columns:
                    # Make sure we have all columns from all_leads
                    all_columns_all = list(df_all.columns)
                    ordered_columns_all = []
                    for col in column_order:
                        if col in all_columns_all:
                            ordered_columns_all.append(col)
                    for col in all_columns_all:
                        if col not in ordered_columns_all:
                            ordered_columns_all.append(col)
                    if ordered_columns_all:
                        df_all = df_all[ordered_columns_all]
                
                df_all.to_excel(full_excel_path, index=False, engine='openpyxl')
                print(f"[SCHEDULER] ✅ Saved all {current_count} leads to: {full_excel_filename}")
                print(f"[SCHEDULER]    Columns: {list(df_all.columns)}")
            else:
                print(f"[SCHEDULER] No new unique leads found (duplicates)")
        else:
            print(f"[SCHEDULER] No increase in lead count (same or decreased)")
        
        # Save current count for next comparison
        try:
            with open(LAST_LEAD_COUNT_FILE, 'w') as f:
                json.dump({
                    'count': current_count,
                    'leads': all_leads,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            print(f"[SCHEDULER] ✅ Saved current count ({current_count} leads) for next comparison")
            
            # Also save to a session-accessible file for frontend
            # Find the latest session file or create a new one
            try:
                # Store in a way that frontend can access
                latest_file_id = str(uuid.uuid4())
                latest_file_path = os.path.join(LEADS_STORAGE_DIR, f"{latest_file_id}.json")
                with open(latest_file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'leads': all_leads,
                        'lead_count': current_count,
                        'created_at': datetime.now().isoformat()
                    }, f, indent=2)
                print(f"[SCHEDULER] Saved leads to session file: {latest_file_id}")
            except Exception as e:
                print(f"[SCHEDULER] Warning: Could not save session file: {e}")
        except Exception as e:
            print(f"[SCHEDULER] Error saving count: {e}")
        
        print(f"[SCHEDULER] ✅ Automated scrape completed")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"[SCHEDULER] ❌ ERROR in automated scrape: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70 + "\n")
        if driver:
            try:
                driver.quit()
            except:
                pass


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
    
    # Start scheduler for automatic scraping every 5 minutes
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=automated_scrape_job,
        trigger=IntervalTrigger(minutes=5),
        id='auto_scrape_job',
        name='Automated scraping every 5 minutes',
        replace_existing=True
    )
    scheduler.start()
    print("\n✅ Automated scheduler started - will scrape every 5 minutes")
    print("   First run will start in 5 minutes")
    print("   Or click 'Scrape Towns' button to run manually now")
    
    print("\nStarting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 70)
    
    try:
        # Disable reloader to prevent scheduler from starting multiple times
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.shutdown()
        print("Done.")
