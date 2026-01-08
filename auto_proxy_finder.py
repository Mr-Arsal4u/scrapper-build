#!/usr/bin/env python3
"""
Python-based free proxy finder and tester
More reliable than bash version
"""

import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_proxies():
    """Fetch free proxies from multiple sources"""
    proxies = []
    
    print("Fetching proxies from multiple sources...")
    
    # Source 1: ProxyScrape API
    try:
        print("  Trying ProxyScrape...")
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            proxies.extend([line.strip() for line in lines if ':' in line and line.strip()])
            print(f"    ✓ Got {len([p for p in proxies if ':' in p])} proxies")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
    
    # Source 2: GitHub proxy lists
    try:
        print("  Trying GitHub proxy lists...")
        url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            new_proxies = [line.strip() for line in lines if ':' in line and line.strip() and not line.startswith('#')]
            proxies.extend(new_proxies)
            print(f"    ✓ Got {len(new_proxies)} more proxies")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
    
    # Source 3: ProxyList
    try:
        print("  Trying ProxyList...")
        url = "https://www.proxyscan.io/api/proxy?format=txt&limit=50"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            new_proxies = [line.strip() for line in lines if ':' in line and line.strip()]
            proxies.extend(new_proxies)
            print(f"    ✓ Got {len(new_proxies)} more proxies")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
    
    # Remove duplicates and validate format
    unique_proxies = []
    seen = set()
    for proxy in proxies:
        proxy = proxy.strip()
        if ':' in proxy and proxy not in seen:
            parts = proxy.split(':')
            if len(parts) == 2 and parts[1].isdigit():
                unique_proxies.append(proxy)
                seen.add(proxy)
    
    print(f"\n✓ Total unique proxies: {len(unique_proxies)}")
    return unique_proxies


def test_proxy(proxy):
    """Test if a proxy is working"""
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Test with a simple request
        response = requests.get(
            'https://api.ipify.org',
            proxies=proxies,
            timeout=5
        )
        
        if response.status_code == 200 and response.text.strip():
            return {
                'proxy': proxy,
                'working': True,
                'ip': response.text.strip(),
                'speed': response.elapsed.total_seconds()
            }
    except Exception as e:
        pass
    
    return {'proxy': proxy, 'working': False}


def find_working_proxy(max_tests=30):
    """Find a working proxy"""
    print("\n" + "="*50)
    print("Free Proxy Finder")
    print("="*50 + "\n")
    
    # Fetch proxies
    proxies = fetch_proxies()
    
    if not proxies:
        print("\n❌ No proxies found. Check your internet connection.")
        return None
    
    # Test proxies
    print(f"\nTesting up to {max_tests} proxies...")
    print("-" * 50)
    
    working_proxies = []
    tested = 0
    
    # Use thread pool for faster testing
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {
            executor.submit(test_proxy, proxy): proxy 
            for proxy in proxies[:max_tests]
        }
        
        for future in as_completed(future_to_proxy):
            tested += 1
            result = future.result()
            
            if result['working']:
                working_proxies.append(result)
                print(f"  [{tested:2d}] {result['proxy']:25s} ✓ WORKING! (IP: {result['ip']}, Speed: {result['speed']:.2f}s)")
            else:
                print(f"  [{tested:2d}] {result['proxy']:25s} ✗ Failed")
            
            # Stop if we found a good one
            if working_proxies:
                break
    
    if not working_proxies:
        print("\n❌ No working proxies found.")
        print("\nSuggestions:")
        print("  1. Run this script again (new proxies)")
        print("  2. Use Windscribe free tier (more reliable)")
        print("  3. Use ProtonVPN free (system VPN)")
        return None
    
    # Get the fastest working proxy
    best = min(working_proxies, key=lambda x: x['speed'])
    
    print("\n" + "="*50)
    print("✓ Found Working Proxy!")
    print("="*50)
    print(f"Proxy: http://{best['proxy']}")
    print(f"Speed: {best['speed']:.2f} seconds")
    print(f"IP: {best['ip']}")
    
    return f"http://{best['proxy']}"


def update_env_file(proxy_url):
    """Update .env file with working proxy"""
    env_file = ".env"
    
    # Backup existing .env
    if os.path.exists(env_file):
        import shutil
        from datetime import datetime
        backup = f"{env_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(env_file, backup)
        print(f"\n✓ Backed up existing .env to {backup}")
    
    # Read existing .env or create new
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update VPN_PROXY
    env_vars['VPN_PROXY'] = proxy_url
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# VPN Proxy Configuration\n")
        f.write(f"VPN_PROXY={proxy_url}\n")
        if 'VPN_PROXY_USER' in env_vars:
            f.write(f"VPN_PROXY_USER={env_vars['VPN_PROXY_USER']}\n")
        if 'VPN_PROXY_PASS' in env_vars:
            f.write(f"VPN_PROXY_PASS={env_vars['VPN_PROXY_PASS']}\n")
    
    print(f"✓ Updated {env_file} with working proxy")
    print("\nYou can now run the scraper:")
    print("  ./run_with_vpn.sh")
    print("  or")
    print("  python simple_scraper.py")


if __name__ == "__main__":
    try:
        proxy_url = find_working_proxy(max_tests=30)
        if proxy_url:
            update_env_file(proxy_url)
            print("\n⚠️  Note: Free proxies die frequently.")
            print("   Run this script again if proxy stops working.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


