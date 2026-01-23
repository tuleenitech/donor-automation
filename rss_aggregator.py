import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import json
import os

class DonorRSSAggregator:
    """
    RSS Feed aggregator for donor opportunities
    Monitors multiple donor RSS feeds and filters for relevant opportunities
    """
    
    def __init__(self, country="Tanzania", sectors=None, show_all=False):
        self.country = country.lower()
        self.sectors = [s.lower() for s in (sectors or ["education", "health", "agriculture", "food"])]
        self.opportunities = []
        self.show_all = show_all  # If True, show everything even if seen before
        self.seen_urls = self.load_seen_urls() if not show_all else set()
    
    def load_seen_urls(self):
        """Load previously seen URLs to avoid duplicates"""
        try:
            if os.path.exists('seen_opportunities.json'):
                with open('seen_opportunities.json', 'r') as f:
                    return set(json.load(f))
        except:
            pass
        return set()
    
    def save_seen_urls(self):
        """Save seen URLs for next run"""
        try:
            with open('seen_opportunities.json', 'w') as f:
                json.dump(list(self.seen_urls), f)
        except Exception as e:
            print(f"Warning: Could not save seen URLs: {e}")
    
    def get_donor_feeds(self):
        """
        EXPANDED list of RSS feeds - more sources = more opportunities!
        """
        return {
            # === MAJOR AGGREGATORS (Best sources!) ===
            'FundsForNGOs - All': {
                'url': 'https://www2.fundsforngos.org/feed/',
                'type': 'aggregator',
                'keywords': ['tanzania', 'east africa', 'africa', 'international']
            },
            'Devex - Funding News': {
                'url': 'https://www.devex.com/news/feed.rss',
                'type': 'aggregator',
                'keywords': ['tanzania', 'east africa', 'africa']
            },
            'UNESCO': {'url': 'http://www.unevoc.unesco.org/unevoc_rss.xml', 'type': 'UN', 'keywords': ['education', 'africa']},

            'ReliefWeb - Tanzania Updates': {
                'url': 'https://reliefweb.int/jobs/rss.xml',
                'type': 'aggregator',
                'keywords': ['tanzania', 'education']
            },
            'ReliefWeb - Jobs East Africa': {
                'url': 'https://reliefweb.int/jobs?search=east+africa&format=rss',
                'type': 'aggregator',
                'keywords': ['tanzania', 'east africa']
            },
            'ReliefWeb - Funding/Grants': {'url': 'https://reliefweb.int/updates?query=grant+OR+funding&format=rss', 'type': 'aggregator', 'keywords': ['tanzania', 'education']},
            'Humentum (formerly LINGOs)': {
                'url': 'https://www.humentum.org/feed',
                'type': 'aggregator',
                'keywords': ['africa', 'grant', 'funding']
            },
            
            # === BILATERAL DONORS ===
            'USAID - Business Opportunities': {
                'url': 'https://www.usaid.gov/rss/business.xml',
                'type': 'bilateral',
                'keywords': ['tanzania', 'east africa', 'africa', 'international']
            },
            'UK FCDO - News': {
                'url': 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom',
                'type': 'bilateral',
                'keywords': ['tanzania', 'africa', 'aid', 'development']
            },
            
            # === UN AGENCIES ===
            'UNICEF - East and Southern Africa': {
                'url': 'https://www.unicef.org/esa/press-releases/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa']
            },
            'WHO Africa': {
                'url': 'https://www.afro.who.int/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'africa']
            },
            'UNDP Africa': {
                'url': 'https://www.undp.org/africa/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa', 'africa']
            },
            'UN OCHA East Africa': {
                'url': 'https://www.unocha.org/rss/east-and-central-africa.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa']
            },
            
            # === FOUNDATIONS ===
            'Foundation Center - RFPs': {
                'url': 'https://www.issuelab.org/resources.rss',
                'type': 'foundation',
                'keywords': ['africa', 'education', 'health']
            },
            'Global Fund Updates': {
                'url': 'https://www.theglobalfund.org/data/rss-feeds/updates/',
                'type': 'foundation',
                'keywords': ['tanzania', 'africa', 'health']
            },
            
            # === EDUCATION SPECIFIC ===
            'Global Partnership for Education': {
                'url': 'https://www.globalpartnership.org/rss.xml',
                'type': 'multilateral',
                'keywords': ['tanzania', 'africa', 'education']
            },
            'Education Cannot Wait': {
                'url': 'https://www.educationcannotwait.org/feed/',
                'type': 'multilateral',
                'keywords': ['africa', 'education', 'crisis']
            },
            
            # === HEALTH SPECIFIC ===
            'Gavi Alliance': {
                'url': 'https://www.gavi.org/rss.xml',
                'type': 'foundation',
                'keywords': ['tanzania', 'africa', 'health', 'vaccine']
            },
            
            # === AGRICULTURE & FOOD SECURITY ===
            'CGIAR - Agricultural Research': {
                'url': 'https://www.cgiar.org/news/feed/',
                'type': 'multilateral',
                'keywords': ['tanzania', 'africa', 'agriculture', 'food', 'farming']
            },
            'Food and Agriculture Organization (FAO)': {
                'url': 'https://www.fao.org/news/rss/en/',
                'type': 'UN',
                'keywords': ['tanzania', 'africa', 'agriculture', 'food security', 'farming']
            },
            'International Fund for Agricultural Development (IFAD)': {
                'url': 'https://www.ifad.org/en/rss',
                'type': 'multilateral',
                'keywords': ['tanzania', 'africa', 'agriculture', 'rural', 'farming']
            },
            'Alliance for a Green Revolution in Africa (AGRA)': {
                'url': 'https://agra.org/feed/',
                'type': 'foundation',
                'keywords': ['tanzania', 'east africa', 'agriculture', 'farming', 'food']
            },
            'World Food Programme (WFP)': {
                'url': 'https://www.wfp.org/news/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'africa', 'food', 'hunger', 'nutrition']
            },
            
            # === REGIONAL ===
            'African Development Bank': {
                'url': 'https://www.afdb.org/en/news-and-events/adf/rss',
                'type': 'multilateral',
                'keywords': ['tanzania', 'east africa']
            },
            'East African Community': {
                'url': 'https://www.eac.int/rss',
                'type': 'regional',
                'keywords': ['tanzania', 'east africa']
            },
            
            # === PLATFORMS ===
            'GlobalGiving - Tanzania': {
                'url': 'https://www.globalgiving.org/aboutus/media/rss/',
                'type': 'platform',
                'keywords': ['tanzania', 'africa']
            },

        }
    
    def parse_feed(self, feed_name, feed_info):
        """Parse a single RSS feed"""
        print(f"  📡 Checking: {feed_name}...")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            
            if feed.bozo:  # Feed parsing error
                print(f"    ⚠️ Feed error: {feed_name}")
                return 0
            
            count = 0
            for entry in feed.entries[:20]:  # Check last 20 items
                # Skip if already seen (unless show_all mode)
                entry_url = entry.get('link', '')
                if not self.show_all and entry_url in self.seen_urls:
                    continue
                
                # Get entry details
                title = entry.get('title', '')
                description = entry.get('summary', entry.get('description', ''))
                published = entry.get('published', entry.get('updated', ''))
                
                # Combine text for relevance check
                full_text = f"{title} {description}".lower()
                
                # Check geographic relevance
                geo_relevant = any(kw in full_text for kw in feed_info['keywords'])
                
                # Check sector relevance
                sector_relevant = any(sector in full_text for sector in self.sectors)
                
                # Also check for general funding keywords
                funding_keywords = ['grant', 'funding', 'opportunity', 'proposal', 'rfp', 
                                   'call', 'application', 'tender', 'competition']
                has_funding_keyword = any(kw in full_text for kw in funding_keywords)
                
                # Only include if relevant
                if (geo_relevant or sector_relevant) and has_funding_keyword:
                    self.opportunities.append({
                        'source': feed_name,
                        'source_type': feed_info['type'],
                        'title': title,
                        'description': description[:500],
                        'url': entry_url,
                        'published': published,
                        'deadline': self.extract_deadline(full_text),
                        'amount': self.extract_amount(full_text),
                        'sectors': self.classify_sectors(full_text),
                        'relevance_score': self.calculate_relevance(full_text),
                        'discovered': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'is_new': entry_url not in self.seen_urls
                    })
                    
                    self.seen_urls.add(entry_url)
                    count += 1
            
            print(f"    ✅ Found {count} relevant opportunities")
            return count
            
        except Exception as e:
            print(f"    ⚠️ Error parsing {feed_name}: {str(e)[:60]}")
            return 0
    
    def calculate_relevance(self, text):
        """Score relevance 0-10"""
        score = 0
        
        # Geography points
        if self.country in text:
            score += 4
        elif 'east africa' in text:
            score += 3
        elif 'africa' in text:
            score += 1
        
        # Sector points
        for sector in self.sectors:
            if sector in text:
                score += 2
        
        # Urgency points
        if any(word in text for word in ['deadline', 'closing', 'urgent', 'apply now']):
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    def extract_deadline(self, text):
        """Extract deadline from text"""
        patterns = [
            r'deadline[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'closes?[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
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
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def classify_sectors(self, text):
        """Classify sectors"""
        sectors = []
        
        sector_keywords = {
            'education': ['education', 'school', 'learning', 'training', 'literacy', 'student', 'teacher'],
            'health': ['health', 'medical', 'hospital', 'clinic', 'healthcare', 'nutrition', 'disease'],
            'water': ['water', 'sanitation', 'wash', 'hygiene'],
            'agriculture': ['agriculture', 'farming', 'crop', 'livestock', 'agricu', 'farmer', 'harvest'],
            'food_security': ['food security', 'hunger', 'malnutrition', 'food system', 'food aid'],
            'governance': ['governance', 'democracy', 'rights', 'justice', 'policy'],
            'climate': ['climate', 'environment', 'sustainability', 'renewable'],
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in text for kw in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    def scan_all_feeds(self):
        """Scan all RSS feeds"""
        print("="*70)
        print("📡 RSS DONOR FEED AGGREGATOR")
        print(f"🎯 Focus: {self.country.title()} + {', '.join(self.sectors).title()}")
        if self.show_all:
            print("📋 Mode: SHOW ALL (including previously seen)")
        print("="*70)
        
        feeds = self.get_donor_feeds()
        
        print(f"\n📊 Scanning {len(feeds)} RSS feeds...\n")
        
        total_found = 0
        for feed_name, feed_info in feeds.items():
            found = self.parse_feed(feed_name, feed_info)
            total_found += found
            time.sleep(1)  # Be respectful to servers
        
        print("\n" + "="*70)
        
        new_count = len([o for o in self.opportunities if o.get('is_new', True)])
        
        if self.show_all:
            print(f"✅ Scan complete! Found {len(self.opportunities)} relevant opportunities")
            print(f"   ({new_count} are new, {len(self.opportunities)-new_count} previously seen)")
        else:
            print(f"✅ Scan complete! Found {new_count} NEW relevant opportunities")
        
        print("="*70)
        
        # Save seen URLs for next time
        self.save_seen_urls()
        
        if len(self.opportunities) == 0:
            print("\n💡 No new opportunities found this time.")
            print("   This is normal - RSS feeds update periodically.")
            print("   Run this daily to catch new opportunities as they appear!")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.opportunities)
        
        # Sort by relevance score
        df = df.sort_values('relevance_score', ascending=False)
        
        return df
    
    def generate_report(self, df):
        """Generate summary report"""
        if len(df) == 0:
            return
        
        print("\n📊 OPPORTUNITY SUMMARY:")
        print("-" * 70)
        
        print(f"\n✅ Total new opportunities: {len(df)}")
        print(f"🔥 High relevance (8-10): {len(df[df['relevance_score'] >= 8])}")
        print(f"⚡ Medium relevance (5-7): {len(df[(df['relevance_score'] >= 5) & (df['relevance_score'] < 8)])}")
        
        print("\n📌 By Source Type:")
        print(df['source_type'].value_counts().to_string())
        
        print("\n🎯 By Sector:")
        all_sectors = []
        for sectors in df['sectors']:
            if isinstance(sectors, list):
                all_sectors.extend(sectors)
        if all_sectors:
            print(pd.Series(all_sectors).value_counts().head(5).to_string())
        
        print("\n🏆 TOP 5 MOST RELEVANT OPPORTUNITIES:")
        print("-" * 70)
        
        for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
            print(f"\n{i}. {row['title']}")
            print(f"   Source: {row['source']}")
            print(f"   Relevance: {row['relevance_score']}/10")
            print(f"   Sectors: {', '.join(row['sectors']) if isinstance(row['sectors'], list) else row['sectors']}")
            if row['deadline']:
                print(f"   ⏰ Deadline: {row['deadline']}")
            if row['amount']:
                print(f"   💰 Amount: {row['amount']}")
            print(f"   🔗 {row['url']}")
        
        # Show deadlines
        with_deadlines = df[df['deadline'].notna()]
        if len(with_deadlines) > 0:
            print(f"\n\n🚨 URGENT - {len(with_deadlines)} opportunities with deadlines:")
            print("-" * 70)
            for _, row in with_deadlines.iterrows():
                print(f"• {row['title'][:60]}")
                print(f"  Deadline: {row['deadline']} | {row['url']}\n")


# RUN THE RSS AGGREGATOR
if __name__ == "__main__":
    import sys
    
    # Check for --all flag to show everything
    show_all = '--all' in sys.argv
    
    aggregator = DonorRSSAggregator(
        country="Tanzania",
        sectors=["education", "health", "agriculture", "food"],
        show_all=show_all
    )
    
    if show_all:
        print("\n🔍 Running in SHOW ALL mode - will display previously seen opportunities")
    
    print("\n🚀 Starting RSS feed scan...")
    print("⏱️  This will take 1-2 minutes...\n")
    
    results = aggregator.scan_all_feeds()
    
    if len(results) > 0:
        aggregator.generate_report(results)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"rss_opportunities_{timestamp}.csv"
        results.to_csv(filename, index=False)
        print(f"\n💾 Full results saved to: {filename}")
        
        # Save high-priority ones
        priority = results[results['relevance_score'] >= 7]
        if len(priority) > 0:
            priority_file = f"PRIORITY_opportunities_{timestamp}.csv"
            priority.to_csv(priority_file, index=False)
            print(f"⭐ High-priority opportunities: {priority_file}")
        
        # Save urgent ones
        urgent = results[results['deadline'].notna()]
        if len(urgent) > 0:
            urgent_file = f"URGENT_deadlines_{timestamp}.csv"
            urgent.to_csv(urgent_file, index=False)
            print(f"🚨 Urgent opportunities: {urgent_file}")
    
    print("\n" + "="*70)
    print("✅ RSS SCAN COMPLETE")
    print("="*70)
    
    print("\n💡 NEXT STEPS:")
    print("1. Review the generated CSV files")
    print("2. Set this to run daily (see automation guide below)")
    print("3. Add more RSS feeds as you discover them")
    
    print("\n📅 TO AUTOMATE (Run Daily):")
    print("   Linux/Mac: Add to crontab")
    print("   crontab -e")
    print("   0 9 * * * cd /path/to/project && python rss_aggregator.py")
    print("\n   Windows: Use Task Scheduler")
    print("   Or deploy to a free server (Heroku, Railway, etc.)")