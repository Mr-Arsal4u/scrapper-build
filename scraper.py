"""
Foreclosure Scraper - Extracts foreclosure leads from Connecticut Judicial website
"""
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


class ForeclosureScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=old')
            chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--remote-debugging-port=9222')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def get_town_list(self, url):
        """Extract list of towns with their links from the main page"""
        print(f"Fetching town list from: {url}")
        print("⚠️  Note: This website requires VPN access. Ensure your VPN is connected.")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load (longer wait for VPN)
            
            # Wait for the content to load - look for the Panel div that contains towns
            self.wait.until(EC.presence_of_element_located((By.ID, "ctl00_cphBody_Panel1")))
        except Exception as e:
            error_msg = f"Failed to access URL. This website requires VPN access.\n"
            error_msg += f"Please ensure:\n"
            error_msg += f"1. Your VPN is connected and active\n"
            error_msg += f"2. You can access the website manually in your browser\n"
            error_msg += f"3. Your network connection is stable\n"
            error_msg += f"Original error: {str(e)}"
            raise ConnectionError(error_msg)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        towns = []
        
        # Find the panel div that contains all towns
        panel = soup.find('div', id='ctl00_cphBody_Panel1')
        if not panel:
            # Fallback: search entire page
            panel = soup
        
        # Get the entire text content of the panel
        panel_html = str(panel)
        
        # Find all links with pattern PendPostbyTownDetails.aspx?town=
        links = panel.find_all('a', href=re.compile(r'PendPostbyTownDetails\.aspx\?town='))
        
        for link in links:
            town_name = link.get_text(strip=True)
            href = link.get('href')
            
            if town_name and href:
                count = 0
                
                # Method 1: Look for count in the HTML after this link
                link_html = str(link)
                link_pos = panel_html.find(link_html)
                
                if link_pos != -1:
                    # Get text/html after the link (up to 200 chars or next <br>)
                    after_link = panel_html[link_pos + len(link_html):link_pos + len(link_html) + 200]
                    # Extract count from pattern like: <span> (</span><span>2</span><span>)</span>
                    # Or simpler: just find (number) pattern
                    count_match = re.search(r'\((\d+)\)', after_link)
                    if count_match:
                        count = int(count_match.group(1))
                
                # Method 2: If count still 0, try getting next sibling text
                if count == 0:
                    # Get all next siblings until <br>
                    current = link.next_sibling
                    text_after = ""
                    while current:
                        if hasattr(current, 'get_text'):
                            text_after += current.get_text()
                        elif isinstance(current, str):
                            text_after += current
                        if hasattr(current, 'name') and current.name == 'br':
                            break
                        current = getattr(current, 'next_sibling', None)
                    
                    count_match = re.search(r'\((\d+)\)', text_after)
                    if count_match:
                        count = int(count_match.group(1))
                
                # Build full URL
                if href.startswith('http'):
                    full_url = href
                else:
                    base_url = url.rsplit('/', 1)[0]
                    full_url = f"{base_url}/{href}"
                
                towns.append({
                    'name': town_name,
                    'url': full_url,
                    'count': count
                })
        
        print(f"Found {len(towns)} towns")
        return towns
    
    def extract_leads_from_town(self, town_url, town_name):
        """Extract all leads from a specific town's page"""
        print(f"Extracting leads from {town_name}...")
        try:
            self.driver.get(town_url)
            time.sleep(2)
            
            # Wait for table to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            except:
                print(f"  No table found for {town_name}")
                return []
        except Exception as e:
            print(f"  ⚠️  Connection error for {town_name}: {str(e)}")
            print(f"  Make sure VPN is still connected")
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        leads = []
        
        # Find the table containing foreclosure data
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        # Extract data from each cell
                        row_num = cells[0].get_text(strip=True)
                        sale_date_time = cells[1].get_text(strip=True)
                        
                        # Extract docket number (usually in a link)
                        docket_link = cells[2].find('a')
                        docket_number = docket_link.get_text(strip=True) if docket_link else cells[2].get_text(strip=True)
                        
                        # Extract property details
                        property_info = cells[3].get_text(strip=True)
                        
                        # Try to extract address from property info
                        address_match = re.search(r'ADDRESS:\s*(.+?)(?:\s*View|$)', property_info, re.IGNORECASE)
                        address = address_match.group(1).strip() if address_match else property_info
                        
                        # Extract sale type
                        sale_type_match = re.search(r'PUBLIC AUCTION FORECLOSURE SALE:\s*([^ADDRESS]+)', property_info, re.IGNORECASE)
                        sale_type = sale_type_match.group(1).strip() if sale_type_match else "PUBLIC AUCTION FORECLOSURE SALE"
                        
                        # Extract view full notice link if available
                        view_link = cells[3].find('a', href=re.compile(r'PendPostDetailPublic'))
                        view_notice_url = ""
                        if view_link:
                            href = view_link.get('href')
                            if href:
                                if href.startswith('http'):
                                    view_notice_url = href
                                else:
                                    base_url = town_url.rsplit('/', 1)[0]
                                    view_notice_url = f"{base_url}/{href}"
                        
                        if docket_number and sale_date_time:
                            leads.append({
                                'Town': town_name,
                                'Row #': row_num,
                                'Sale Date': sale_date_time,
                                'Docket Number': docket_number,
                                'Sale Type': sale_type,
                                'Address': address,
                                'View Full Notice URL': view_notice_url,
                                'Scraped Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except Exception as e:
                        print(f"  Error parsing row: {e}")
                        continue
        
        print(f"  Extracted {len(leads)} leads from {town_name}")
        return leads
    
    def scrape_all_leads(self, base_url):
        """Scrape all leads from all towns"""
        all_leads = []
        
        # Get list of towns
        towns = self.get_town_list(base_url)
        
        # Extract leads from each town
        for town in towns:
            if town['count'] > 0:  # Only process towns with pending sales
                leads = self.extract_leads_from_town(town['url'], town['name'])
                all_leads.extend(leads)
                time.sleep(1)  # Be respectful with requests
        
        return all_leads, towns
    
    def save_to_excel(self, leads, filename='foreclosure_leads.xlsx'):
        """Save leads to Excel file"""
        if not leads:
            print("No leads to save")
            return
        
        df = pd.DataFrame(leads)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Saved {len(leads)} leads to {filename}")
        return filename
    
    def close(self):
        """Close the browser"""
        self.driver.quit()


if __name__ == "__main__":
    # Test the scraper
    scraper = ForeclosureScraper(headless=True)
    try:
        url = "https://sso.eservices.jud.ct.gov/foreclosures/Public/PendPostbyTownList.aspx"
        leads, towns = scraper.scrape_all_leads(url)
        scraper.save_to_excel(leads)
        print(f"\nTotal leads scraped: {len(leads)}")
    finally:
        scraper.close()

