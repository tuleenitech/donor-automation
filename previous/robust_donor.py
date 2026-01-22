import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
import json

class RobustDonorScraper:
    """
    More resilient scraper that works with real-world messy websites
    Includes fallbacks and better error handling
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.opportunities = []
    
    def fetch_with_retry(self, url, max_retries=2):
        """Fetch URL with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"    Fetching {url[:60]}...")
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"    ⚠️ Attempt {attempt+1} failed: {str(e)[:50]}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    return None
    
    def scrape_grants_gov(self):
        """Scrape Grants.gov for Tanzania opportunities"""
        print("\n🔍 Scraping Grants.gov (US Federal Grants)...")
        
        try:
            # Search for Tanzania grants
            url = 'https://www.grants.gov/search-results-detail/353633'  # Example format
            # Note: Grants.gov requires specific search, we'll use a general approach
            
            search_url = 'https://www.grants.gov/web/grants/search-grants.html'
            response = self.fetch_with_retry(search_url)
            
            if not response:
                print("    ℹ️ Grants.gov requires interactive search. Skipping automated scrape.")
                print("    💡 Manual check recommended: https://www.grants.gov/search-grants.html")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Grants.gov is JavaScript-heavy, may not scrape well
            print("    ℹ️ Grants.gov uses dynamic loading. Consider using their API instead.")
            print("    📌 Action: Check manually or use Grants.gov RSS feeds")
            
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
    
    def scrape_devex(self):
        """Scrape Devex funding opportunities"""
        print("\n🔍 Scraping Devex.com...")
        
        try:
            # Devex lists funding opportunities
            url = 'https://www.devex.com/funding'
            response = self.fetch_with_retry(url)
            
            if not response:
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Devex uses cards or list items for opportunities
            items = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|opportunity', re.I))
            
            count = 0
            for item in items[:15]:  # Check first 15
                title_elem = item.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|heading', re.I))
                
                if not title_elem:
                    title_elem = item.find('a')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Filter for relevance
                text = item.get_text().lower()
                if not any(word in text for word in ['tanzania', 'east africa', 'africa', 'education', 'health']):
                    continue
                
                link = item.find('a', href=True)
                full_url = link['href'] if link else ''
                if full_url and not full_url.startswith('http'):
                    full_url = 'https://www.devex.com' + full_url
                
                self.opportunities.append({
                    'donor': 'Multiple (via Devex)',
                    'title': title,
                    'url': full_url,
                    'deadline': self.extract_deadline(item.get_text()),
                    'amount': self.extract_amount(item.get_text()),
                    'description': item.get_text(strip=True)[:250],
                    'sectors': self.classify_sectors(text),
                    'source': 'Devex',
                    'scraped': datetime.now().strftime('%Y-%m-%d')
                })
                count += 1
            
            print(f"    ✅ Found {count} opportunities on Devex")
            
        except Exception as e:
            print(f"    ⚠️ Error scraping Devex: {e}")
    
    def scrape_reliefweb(self):
        """Scrape ReliefWeb jobs/tenders (includes grants)"""
        print("\n🔍 Scraping ReliefWeb...")
        
        try:
            # ReliefWeb has structured data
            urls = [
                'https://reliefweb.int/updates?advanced-search=%28PC236%29_%28C47%29',  # Tanzania
                'https://reliefweb.int/jobs?search=tanzania'
            ]
            
            count = 0
            for url in urls:
                response = self.fetch_with_retry(url)
                if not response:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # ReliefWeb uses article tags
                articles = soup.find_all('article', class_=re.compile(r'node', re.I))
                
                for article in articles[:10]:
                    title_elem = article.find(['h2', 'h3', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    link = article.find('a', href=True)
                    full_url = link['href'] if link else ''
                    if full_url and not full_url.startswith('http'):
                        full_url = 'https://reliefweb.int' + full_url
                    
                    text = article.get_text()
                    
                    self.opportunities.append({
                        'donor': 'Various (via ReliefWeb)',
                        'title': title,
                        'url': full_url,
                        'deadline': self.extract_deadline(text),
                        'amount': self.extract_amount(text),
                        'description': text[:250],
                        'sectors': self.classify_sectors(text),
                        'source': 'ReliefWeb',
                        'scraped': datetime.now().strftime('%Y-%m-%d')
                    })
                    count += 1
                
                time.sleep(2)
            
            print(f"    ✅ Found {count} opportunities on ReliefWeb")
            
        except Exception as e:
            print(f"    ⚠️ Error scraping ReliefWeb: {e}")
    
    def scrape_globalgiving_api(self):
        """Try GlobalGiving's search"""
        print("\n🔍 Scraping GlobalGiving Tanzania projects...")
        
        try:
            url = 'https://www.globalgiving.org/search/?size=25&nextPage=1&sortField=sortorder&selectedLocations=00tanzania'
            response = self.fetch_with_retry(url)
            
            if not response:
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for project listings
            projects = soup.find_all(['div', 'article'], class_=re.compile(r'project|card|item', re.I))
            
            count = 0
            for proj in projects[:15]:
                title_elem = proj.find(['h2', 'h3', 'h4', 'a'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                text = proj.get_text().lower()
                
                # Filter for education/health
                if not any(word in text for word in ['education', 'health', 'school', 'medical', 'children']):
                    continue
                
                link = proj.find('a', href=True)
                full_url = link['href'] if link else ''
                if full_url and not full_url.startswith('http'):
                    full_url = 'https://www.globalgiving.org' + full_url
                
                self.opportunities.append({
                    'donor': 'GlobalGiving',
                    'title': title,
                    'url': full_url,
                    'deadline': 'Rolling',
                    'amount': '$1,000 - $50,000',
                    'description': proj.get_text(strip=True)[:250],
                    'sectors': self.classify_sectors(text),
                    'source': 'GlobalGiving',
                    'scraped': datetime.now().strftime('%Y-%m-%d')
                })
                count += 1
            
            print(f"    ✅ Found {count} projects on GlobalGiving")
            
        except Exception as e:
            print(f"    ⚠️ Error scraping GlobalGiving: {e}")
    
    def scrape_google_search_simulation(self):
        """
        Simulate what you'd find via Google search
        This shows you WHERE to look manually
        """
        print("\n🔍 Generating Google Search Targets...")
        
        search_queries = [
            "Tanzania education grants 2025",
            "Tanzania health funding opportunities",
            "East Africa NGO grants education",
            "call for proposals Tanzania 2025",
            "Tanzania USAID grants",
            "UK aid Tanzania applications"
        ]
        
        print("\n    💡 RECOMMENDED MANUAL SEARCHES:")
        for i, query in enumerate(search_queries, 1):
            print(f"    {i}. Google: '{query}'")
        
        print("\n    📌 KEY SITES TO BOOKMARK:")
        sites = [
            "https://www.grants.gov - US Federal grants",
            "https://www.devex.com/funding - Global opportunities",
            "https://reliefweb.int - Humanitarian jobs/tenders",
            "https://www.globalgiving.org - Crowdfunding platform",
            "https://www.fundsforngos.org - NGO funding database",
            "https://www.philanthropy.com - Foundation news"
        ]
        
        for site in sites:
            print(f"    • {site}")
    
    def extract_deadline(self, text):
        """Extract deadline from text"""
        if not text:
            return None
        
        patterns = [
            r'deadline[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'closes?[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_amount(self, text):
        """Extract funding amount"""
        if not text:
            return None
        
        patterns = [
            r'\$\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'(?:USD|EUR|GBP)\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'£\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'€\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def classify_sectors(self, text):
        """Classify sectors from text"""
        sectors = []
        if not text:
            return ['general']
        
        text_lower = text.lower()
        
        sector_map = {
            'education': ['education', 'school', 'learning', 'training', 'literacy', 'scholarship'],
            'health': ['health', 'medical', 'hospital', 'clinic', 'healthcare', 'nutrition'],
            'child_welfare': ['child', 'children', 'youth', 'orphan'],
            'water': ['water', 'sanitation', 'wash'],
        }
        
        for sector, keywords in sector_map.items():
            if any(kw in text_lower for kw in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    def scrape_all(self):
        """Run all scrapers"""
        print("="*70)
        print("🎯 ROBUST DONOR OPPORTUNITY SCRAPER")
        print("="*70)
        
        self.scrape_devex()
        self.scrape_reliefweb()
        self.scrape_globalgiving_api()
        self.scrape_google_search_simulation()
        self.scrape_grants_gov()
        
        print("\n" + "="*70)
        
        if len(self.opportunities) == 0:
            print("⚠️ No opportunities scraped automatically.")
            print("\n💡 THIS IS NORMAL! Here's why:")
            print("   1. Most donor sites are JavaScript-heavy (need browser automation)")
            print("   2. Sites change frequently (scrapers need constant updates)")
            print("   3. Many require login/registration to see full opportunities")
            print("\n🎯 NEXT STEPS:")
            print("   → Use the manual search targets I listed above")
            print("   → I'll show you how to use APIs instead")
            print("   → We can build a browser automation version")
            return pd.DataFrame()
        
        print(f"✅ Total opportunities found: {len(self.opportunities)}")
        print("="*70)
        
        df = pd.DataFrame(self.opportunities)
        
        # Ensure all expected columns exist
        expected_columns = ['donor', 'title', 'url', 'deadline', 'amount', 'description', 'sectors', 'source', 'scraped']
        for col in expected_columns:
            if col not in df.columns:
                df[col] = None
        
        return df
    
    def generate_summary(self, df):
        """Generate opportunity summary"""
        if len(df) == 0:
            return
        
        print("\n📊 OPPORTUNITIES FOUND:")
        print(f"Total: {len(df)}")
        
        if 'source' in df.columns:
            print("\n📌 By Source:")
            print(df['source'].value_counts().to_string())
        
        if 'sectors' in df.columns:
            print("\n🎯 By Sector:")
            all_sectors = []
            for sectors in df['sectors']:
                if isinstance(sectors, list):
                    all_sectors.extend(sectors)
            if all_sectors:
                print(pd.Series(all_sectors).value_counts().to_string())
        
        with_deadlines = df[df['deadline'].notna()] if 'deadline' in df.columns else pd.DataFrame()
        
        if len(with_deadlines) > 0:
            print(f"\n⏰ Opportunities with deadlines: {len(with_deadlines)}")


# RUN THE SCRAPER
if __name__ == "__main__":
    scraper = RobustDonorScraper()
    
    print("\n🚀 Starting robust donor scraping...")
    print("⏱️  This will take 2-3 minutes...\n")
    
    results = scraper.scrape_all()
    
    if len(results) > 0:
        scraper.generate_summary(results)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"opportunities_found_{timestamp}.csv"
        
        results.to_csv(filename, index=False)
        print(f"\n💾 Results saved to: {filename}")
        
        # Save urgent ones if any
        if 'deadline' in results.columns:
            urgent = results[results['deadline'].notna()]
            if len(urgent) > 0:
                urgent_file = f"URGENT_opps_{timestamp}.csv"
                urgent.to_csv(urgent_file, index=False)
                print(f"🚨 Urgent opportunities: {urgent_file}")
    
    print("\n" + "="*70)
    print("✅ SCRAPING COMPLETE")
    print("="*70)
    
    print("\n📝 IMPORTANT NOTES:")
    print("• Web scraping is fragile - sites change constantly")
    print("• Consider these BETTER alternatives:")
    print("  1. Use donor RSS feeds (more reliable)")
    print("  2. Sign up for email alerts from each donor")
    print("  3. Use aggregator APIs (Devex, FundsForNGOs)")
    print("  4. Browser automation with Selenium (next step)")