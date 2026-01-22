import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time

class DeepDonorScraper:
    """
    Deep scrapers for specific high-priority donors
    Each donor gets a custom scraper based on their site structure
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.opportunities = []
    
    def scrape_usaid_tanzania(self):
        """Scrape USAID Tanzania opportunities"""
        print("🔍 Scraping USAID Tanzania...")
        
        urls = [
            'https://www.usaid.gov/tanzania/work-with-us',
            'https://www.grants.gov/search-grants.html?keywords=tanzania'
        ]
        
        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for opportunity announcements
                opportunities = soup.find_all(['div', 'article', 'section'], 
                                             class_=lambda x: x and any(k in str(x).lower() 
                                             for k in ['opportunity', 'notice', 'announcement', 'grant']))
                
                for opp in opportunities:
                    title_elem = opp.find(['h2', 'h3', 'h4', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Skip if not education/health related
                    if not any(word in title.lower() for word in 
                              ['education', 'health', 'school', 'medical', 'clinic', 'learning']):
                        continue
                    
                    link = opp.find('a', href=True)
                    full_url = link['href'] if link else ''
                    if full_url and not full_url.startswith('http'):
                        full_url = 'https://www.usaid.gov' + full_url
                    
                    self.opportunities.append({
                        'donor': 'USAID Tanzania',
                        'title': title,
                        'url': full_url,
                        'deadline': self.extract_deadline(opp.get_text()),
                        'amount': self.extract_amount(opp.get_text()),
                        'description': opp.get_text(strip=True)[:300],
                        'sectors': self.classify_sectors(title + ' ' + opp.get_text()),
                        'scraped': datetime.now().strftime('%Y-%m-%d')
                    })
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ⚠️ Error scraping USAID: {e}")
        
        print(f"  ✅ Found {len([o for o in self.opportunities if o['donor']=='USAID Tanzania'])} opportunities")
    
    def scrape_uk_aid_direct(self):
        """Scrape UK Aid Direct"""
        print("🔍 Scraping UK Aid Direct...")
        
        try:
            url = 'https://www.ukaiddirect.org/apply/'
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # UK Aid Direct typically has clear call announcements
            calls = soup.find_all(['div', 'section'], 
                                 class_=lambda x: x and 'call' in str(x).lower())
            
            for call in calls:
                title_elem = call.find(['h1', 'h2', 'h3'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Look for "Apply" or "Guidelines" links
                links = call.find_all('a', href=True)
                apply_link = ''
                for link in links:
                    if any(word in link.get_text().lower() for word in ['apply', 'guideline', 'download']):
                        apply_link = link['href']
                        break
                
                if not apply_link.startswith('http'):
                    apply_link = 'https://www.ukaiddirect.org' + apply_link
                
                text = call.get_text()
                
                self.opportunities.append({
                    'donor': 'UK Aid Direct',
                    'title': title,
                    'url': apply_link or url,
                    'deadline': self.extract_deadline(text),
                    'amount': self.extract_amount(text) or '£10,000 - £1,000,000',
                    'description': text[:300],
                    'sectors': self.classify_sectors(title + ' ' + text),
                    'scraped': datetime.now().strftime('%Y-%m-%d')
                })
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  ⚠️ Error scraping UK Aid Direct: {e}")
        
        print(f"  ✅ Found {len([o for o in self.opportunities if o['donor']=='UK Aid Direct'])} opportunities")
    
    def scrape_global_fund(self):
        """Scrape Global Fund opportunities"""
        print("🔍 Scraping Global Fund...")
        
        try:
            url = 'https://www.theglobalfund.org/en/funding-model/'
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Global Fund has structured funding information
            sections = soup.find_all(['div', 'article'], 
                                    class_=lambda x: x and any(k in str(x).lower() 
                                    for k in ['funding', 'grant', 'opportunity']))
            
            for section in sections:
                title_elem = section.find(['h2', 'h3', 'h4'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Only health-related (Global Fund is health-focused)
                if not any(word in title.lower() for word in 
                          ['health', 'hiv', 'tb', 'malaria', 'disease']):
                    continue
                
                links = section.find_all('a', href=True)
                main_link = links[0]['href'] if links else ''
                if main_link and not main_link.startswith('http'):
                    main_link = 'https://www.theglobalfund.org' + main_link
                
                text = section.get_text()
                
                self.opportunities.append({
                    'donor': 'Global Fund',
                    'title': title,
                    'url': main_link or url,
                    'deadline': self.extract_deadline(text),
                    'amount': self.extract_amount(text) or '$500K - $10M+',
                    'description': text[:300],
                    'sectors': ['health', 'HIV/AIDS', 'TB', 'malaria'],
                    'scraped': datetime.now().strftime('%Y-%m-%d')
                })
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  ⚠️ Error scraping Global Fund: {e}")
        
        print(f"  ✅ Found {len([o for o in self.opportunities if o['donor']=='Global Fund'])} opportunities")
    
    def scrape_unicef_tanzania(self):
        """Scrape UNICEF Tanzania"""
        print("🔍 Scraping UNICEF Tanzania...")
        
        try:
            url = 'https://www.unicef.org/tanzania/opportunities'
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # UNICEF often lists opportunities as articles or cards
            items = soup.find_all(['article', 'div'], 
                                 class_=lambda x: x and any(k in str(x).lower() 
                                 for k in ['opportunity', 'tender', 'vacancy', 'call']))
            
            for item in items:
                title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                link = item.find('a', href=True)
                full_url = link['href'] if link else ''
                if full_url and not full_url.startswith('http'):
                    full_url = 'https://www.unicef.org' + full_url
                
                text = item.get_text()
                
                self.opportunities.append({
                    'donor': 'UNICEF Tanzania',
                    'title': title,
                    'url': full_url or url,
                    'deadline': self.extract_deadline(text),
                    'amount': self.extract_amount(text) or '$30K - $500K',
                    'description': text[:300],
                    'sectors': self.classify_sectors(title + ' ' + text),
                    'scraped': datetime.now().strftime('%Y-%m-%d')
                })
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  ⚠️ Error scraping UNICEF: {e}")
        
        print(f"  ✅ Found {len([o for o in self.opportunities if o['donor']=='UNICEF Tanzania'])} opportunities")
    
    def scrape_globalgiving(self):
        """Scrape GlobalGiving campaigns"""
        print("🔍 Scraping GlobalGiving Tanzania projects...")
        
        try:
            # GlobalGiving search for Tanzania education/health
            searches = [
                'https://www.globalgiving.org/search/?size=25&nextPage=1&sortField=sortorder&selectedCountries=tanzania&loadAllResults=true',
            ]
            
            for url in searches:
                response = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # GlobalGiving uses project cards
                projects = soup.find_all(['div', 'article'], 
                                        class_=lambda x: x and 'project' in str(x).lower())
                
                for proj in projects[:10]:  # Limit to first 10
                    title_elem = proj.find(['h3', 'h4', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Filter for education/health
                    text = proj.get_text()
                    if not any(word in text.lower() for word in 
                              ['education', 'health', 'school', 'medical', 'learning', 'children']):
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
                        'amount': self.extract_amount(text) or '$5K - $50K',
                        'description': text[:300],
                        'sectors': self.classify_sectors(title + ' ' + text),
                        'scraped': datetime.now().strftime('%Y-%m-%d')
                    })
                
                time.sleep(2)
                
        except Exception as e:
            print(f"  ⚠️ Error scraping GlobalGiving: {e}")
        
        print(f"  ✅ Found {len([o for o in self.opportunities if o['donor']=='GlobalGiving'])} opportunities")
    
    def extract_deadline(self, text):
        """Extract deadline from text"""
        patterns = [
            r'deadline[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'closing[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_amount(self, text):
        """Extract funding amount"""
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
        text_lower = text.lower()
        
        sector_map = {
            'education': ['education', 'school', 'learning', 'training', 'literacy', 'scholarship', 'student', 'teacher'],
            'health': ['health', 'medical', 'hospital', 'clinic', 'healthcare', 'nutrition', 'disease', 'treatment'],
            'child_protection': ['child', 'children', 'youth', 'protection', 'safeguarding'],
            'maternal_health': ['maternal', 'mother', 'pregnancy', 'reproductive'],
            'water_sanitation': ['water', 'sanitation', 'wash', 'hygiene'],
        }
        
        for sector, keywords in sector_map.items():
            if any(kw in text_lower for kw in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    def scrape_all(self):
        """Run all scrapers"""
        print("="*70)
        print("🎯 DEEP DONOR SCRAPING - Education & Health Focus")
        print("="*70)
        
        self.scrape_usaid_tanzania()
        self.scrape_uk_aid_direct()
        self.scrape_global_fund()
        self.scrape_unicef_tanzania()
        self.scrape_globalgiving()
        
        print("\n" + "="*70)
        print(f"✅ Total opportunities found: {len(self.opportunities)}")
        print("="*70)
        
        return pd.DataFrame(self.opportunities)
    
    def generate_summary(self, df):
        """Generate opportunity summary"""
        if len(df) == 0:
            print("\n⚠️ No opportunities found. This could mean:")
            print("  - Sites have changed structure (scrapers need updating)")
            print("  - No active calls right now")
            print("  - Check the URLs manually")
            return
        
        print("\n📊 OPPORTUNITIES BY DONOR:")
        print(df['donor'].value_counts().to_string())
        
        print("\n🎯 OPPORTUNITIES BY SECTOR:")
        all_sectors = []
        for sectors in df['sectors']:
            if isinstance(sectors, list):
                all_sectors.extend(sectors)
        sector_counts = pd.Series(all_sectors).value_counts()
        print(sector_counts.to_string())
        
        print("\n⏰ OPPORTUNITIES WITH DEADLINES:")
        with_deadlines = df[df['deadline'].notna()]
        print(f"  {len(with_deadlines)} out of {len(df)} have clear deadlines")
        
        if len(with_deadlines) > 0:
            print("\n🔥 URGENT - With Deadlines:")
            for _, row in with_deadlines.iterrows():
                print(f"  • {row['donor']}: {row['title']}")
                print(f"    Deadline: {row['deadline']}")
                print(f"    URL: {row['url']}\n")


# RUN THE DEEP SCRAPE
if __name__ == "__main__":
    scraper = DeepDonorScraper()
    
    print("\n🚀 Starting deep scrape of priority donors...")
    print("⏱️  This may take 2-3 minutes...\n")
    
    results = scraper.scrape_all()
    scraper.generate_summary(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"donor_opportunities_detailed_{timestamp}.csv"
    
    results.to_csv(filename, index=False)
    print(f"\n💾 Detailed opportunities saved to: {filename}")
    
    # Save urgent opportunities (with deadlines)
    urgent = results[results['deadline'].notna()]
    if len(urgent) > 0:
        urgent_file = f"URGENT_opportunities_{timestamp}.csv"
        urgent.to_csv(urgent_file, index=False)
        print(f"🚨 Urgent opportunities saved to: {urgent_file}")
    
    print("\n✅ Deep scrape complete!")
    print("💡 Next: Review the CSV files and visit the URLs for full details")