#!/usr/bin/env python3
"""
Simple HTTP-based scraper for Connecticut Judicial foreclosure website
Uses HTTP requests with proxy support - no browser automation needed
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://sso.eservices.jud.ct.gov/foreclosures/Public"
TOWN_LIST_URL = f"{BASE_URL}/PendPostbyTownList.aspx"
OUTPUT_DIR = "scraped_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Proxy/VPN Configuration
# Set these environment variables or modify below:
# export VPN_PROXY="http://proxy-host:port"
# export VPN_PROXY="socks5://socks-proxy-host:port"
VPN_PROXY = os.getenv("VPN_PROXY", "")
VPN_PROXY_USER = os.getenv("VPN_PROXY_USER", "")
VPN_PROXY_PASS = os.getenv("VPN_PROXY_PASS", "")


class ForeclosureScraper:
    def __init__(self, proxy=None, proxy_user=None, proxy_pass=None):
        """Initialize scraper with optional proxy"""
        self.session = requests.Session()
        
        # Set up proxy if provided
        if proxy:
            self.proxies = {
                'http': proxy,
                'https': proxy
            }
            print(f"Using proxy: {proxy}")
        else:
            self.proxies = None
            print("No proxy configured - using direct connection")
        
        # Set headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Handle proxy authentication if needed
        if proxy_user and proxy_pass:
            from requests.auth import HTTPProxyAuth
            self.session.auth = HTTPProxyAuth(proxy_user, proxy_pass)
    
    def get_page(self, url, retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url,
                    proxies=self.proxies,
                    timeout=30,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    print(f"  Attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2)
                else:
                    raise Exception(f"Failed to fetch {url} after {retries} attempts: {e}")
    
    def get_town_list(self):
        """Get list of all towns from the main page"""
        print(f"Fetching town list from: {TOWN_LIST_URL}")
        
        try:
            response = self.get_page(TOWN_LIST_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the panel containing towns
            panel = soup.find('div', id='ctl00_cphBody_Panel1')
            if not panel:
                # Try alternative selectors
                panel = soup.find('div', class_='panel') or soup.find('div', id='Panel1')
            
            if not panel:
                print("ERROR: Could not find towns panel. Page structure may have changed.")
                print("Page content preview:")
                print(response.text[:500])
                return []
            
            # Find all town links
            town_links = panel.find_all('a', href=True)
            towns = []
            
            for link in town_links:
                href = link.get('href', '')
                town_name = link.get_text(strip=True)
                
                # Check if it's a town detail link
                if 'PendPostbyTownDetails.aspx' in href and town_name:
                    towns.append({
                        'name': town_name,
                        'url': urljoin(BASE_URL, href)
                    })
            
            print(f"Found {len(towns)} towns")
            return towns
            
        except Exception as e:
            print(f"ERROR getting town list: {e}")
            if "403" in str(e) or "Forbidden" in str(e):
                print("\n⚠️  VPN/PROXY REQUIRED!")
                print("This website requires VPN access.")
                print("Please configure VPN_PROXY environment variable:")
                print("  export VPN_PROXY='http://your-vpn-proxy:port'")
                print("  or create .env file with: VPN_PROXY=http://proxy:port")
            raise
    
    def get_town_leads(self, town_name, town_url):
        """Get foreclosure leads for a specific town"""
        leads = []
        
        try:
            response = self.get_page(town_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with leads
            table = soup.find('table', id='ctl00_cphBody_GridView1')
            
            if not table:
                # No leads for this town
                return leads
            
            # Parse table rows (skip header)
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 4:
                    continue
                
                try:
                    # Extract data from cells
                    row_num = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                    
                    # Sale Date
                    sale_date = ""
                    if len(cells) > 1:
                        sale_date_elem = cells[1].find('span') or cells[1]
                        sale_date = sale_date_elem.get_text(separator=' ', strip=True)
                        sale_date = ' '.join(sale_date.split())
                    
                    # Docket Number
                    docket_number = ""
                    docket_url = ""
                    if len(cells) > 2:
                        docket_link = cells[2].find('a')
                        if docket_link:
                            docket_number = docket_link.get_text(strip=True)
                            href = docket_link.get('href', '')
                            if href:
                                docket_url = urljoin(BASE_URL, href)
                        else:
                            docket_number = cells[2].get_text(strip=True)
                    
                    # Property Address and Sale Type
                    address = ""
                    sale_type = ""
                    if len(cells) > 3:
                        property_elem = cells[3].find('span') or cells[3]
                        property_text = property_elem.get_text(separator=' ', strip=True)
                        property_text = ' '.join(property_text.split())
                        
                        if "ADDRESS:" in property_text.upper():
                            parts = property_text.split("ADDRESS:", 1)
                            if len(parts) > 1:
                                sale_type_part = parts[0].replace("PUBLIC AUCTION FORECLOSURE SALE:", "").strip()
                                sale_type = sale_type_part if sale_type_part else "PUBLIC AUCTION FORECLOSURE SALE"
                                address = parts[1].strip()
                            else:
                                address = property_text
                                sale_type = "PUBLIC AUCTION FORECLOSURE SALE"
                        else:
                            address = property_text
                            sale_type = "PUBLIC AUCTION FORECLOSURE SALE"
                    
                    # View Full Notice URL
                    view_notice_url = ""
                    if len(cells) > 4:
                        view_link = cells[4].find('a')
                        if view_link:
                            href = view_link.get('href', '')
                            if href:
                                view_notice_url = urljoin(BASE_URL, href)
                    
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
            
            return leads
            
        except Exception as e:
            print(f"  Error scraping {town_name}: {e}")
            return leads
    
    def scrape_all(self):
        """Scrape all towns and their leads"""
        print("=" * 70)
        print("Foreclosure Scraper - Simple HTTP Version")
        print("=" * 70)
        
        # Get town list
        towns = self.get_town_list()
        if not towns:
            print("No towns found. Exiting.")
            return
        
        # Scrape leads from each town
        all_leads = []
        total_towns = len(towns)
        
        print(f"\nScraping leads from {total_towns} towns...")
        print("=" * 70)
        
        for i, town in enumerate(towns, 1):
            town_name = town['name']
            town_url = town['url']
            
            print(f"[{i}/{total_towns}] Scraping {town_name}...")
            
            leads = self.get_town_leads(town_name, town_url)
            all_leads.extend(leads)
            
            print(f"  Found {len(leads)} leads for {town_name}")
            
            # Be respectful - small delay between requests
            time.sleep(0.5)
        
        print("\n" + "=" * 70)
        print(f"Total leads scraped: {len(all_leads)}")
        print("=" * 70)
        
        # Save to Excel
        if all_leads:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_file = os.path.join(OUTPUT_DIR, f"foreclosure_leads_{timestamp}.xlsx")
            
            df = pd.DataFrame(all_leads)
            column_order = ['row_number', 'town', 'sale_date', 'docket_number', 'address', 
                          'sale_type', 'docket_url', 'view_notice_url']
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            df.to_excel(excel_file, index=False, engine='openpyxl')
            print(f"\n✅ Saved to: {excel_file}")
            
            # Also save as JSON
            json_file = os.path.join(OUTPUT_DIR, f"foreclosure_leads_{timestamp}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'leads': all_leads,
                    'lead_count': len(all_leads),
                    'scraped_at': datetime.now().isoformat()
                }, f, indent=2)
            print(f"✅ Also saved to: {json_file}")
        else:
            print("\n⚠️  No leads found. Check VPN/proxy configuration.")
        
        return all_leads


def main():
    """Main function"""
    # Load .env if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Get proxy from environment or use default
    proxy = os.getenv("VPN_PROXY", VPN_PROXY)
    proxy_user = os.getenv("VPN_PROXY_USER", VPN_PROXY_USER)
    proxy_pass = os.getenv("VPN_PROXY_PASS", VPN_PROXY_PASS)
    
    if not proxy:
        print("⚠️  WARNING: No VPN_PROXY configured!")
        print("This website requires VPN access.")
        print("Set VPN_PROXY environment variable or create .env file")
        print("Example: export VPN_PROXY='http://proxy-host:port'")
        print("\nContinuing anyway...\n")
    
    # Create scraper and run
    scraper = ForeclosureScraper(proxy=proxy, proxy_user=proxy_user, proxy_pass=proxy_pass)
    
    try:
        scraper.scrape_all()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


