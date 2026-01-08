"""
Simple test script to show the list of towns
"""
from scraper import ForeclosureScraper

def main():
    print("=" * 60)
    print("Testing Town List Extraction")
    print("=" * 60)
    print()
    
    scraper = ForeclosureScraper(headless=False)  # Show browser for testing
    try:
        url = "https://sso.eservices.jud.ct.gov/foreclosures/Public/PendPostbyTownList.aspx"
        towns = scraper.get_town_list(url)
        
        print()
        print("=" * 60)
        print(f"Found {len(towns)} towns:")
        print("=" * 60)
        print()
        
        # Display towns in a nice format
        for i, town in enumerate(towns, 1):
            print(f"{i:3d}. {town['name']:30s} - {town['count']:3d} pending sales")
            print(f"     URL: {town['url']}")
            print()
        
        print("=" * 60)
        print(f"Total: {len(towns)} towns")
        print(f"Total pending sales: {sum(t['count'] for t in towns)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPress Enter to close the browser...")
        scraper.close()

if __name__ == "__main__":
    main()

