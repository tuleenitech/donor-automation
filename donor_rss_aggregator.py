import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ImprovedDonorRSSAggregator:
    """
    ENHANCED RSS Feed aggregator specifically optimized for orphanage funding
    Focuses on child welfare, education, and community development opportunities
    """
    
    def __init__(self, country="Tanzania", sectors=None, show_all=False, email_alerts=False):
        self.country = country.lower()
        self.sectors = [s.lower() for s in (sectors or ["education", "health", "agriculture", "food", "children"])]
        self.opportunities = []
        self.show_all = show_all
        self.email_alerts = email_alerts
        self.seen_urls = self.load_seen_urls() if not show_all else set()
        
        # ORPHANAGE-SPECIFIC KEYWORDS (weighted heavily in scoring)
        self.orphanage_keywords = [
            'orphan', 'orphanage', 'children', 'child welfare', 'vulnerable children',
            'ovc', 'child care', 'childcare', 'foster', 'adoption', 'street children',
            'child protection', 'children in need', 'disadvantaged children',
            'children\'s home', 'residential care', 'family support'
        ]
    
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
        COMPREHENSIVE list of RSS feeds - OPTIMIZED FOR ORPHANAGES
        Includes child-focused, education, and community development sources
        """
        return {
            # === MAJOR AGGREGATORS (Best sources!) ===
            'FundsForNGOs - All Grants': {
                'url': 'https://www2.fundsforngos.org/feed/',
                'type': 'aggregator',
                'keywords': ['tanzania', 'east africa', 'africa', 'children', 'orphan', 'education'],
                'priority': 'high'
            },
            'Devex - Funding Opportunities': {
                'url': 'https://www.devex.com/news/feed.rss',
                'type': 'aggregator',
                'keywords': ['tanzania', 'east africa', 'africa', 'children'],
                'priority': 'high'
            },
            'GrantWatch - Africa': {
                'url': 'https://www.grantwatch.com/rss.xml',
                'type': 'aggregator',
                'keywords': ['africa', 'children', 'education', 'tanzania'],
                'priority': 'high'
            },
            'Foundation Directory Online': {
                'url': 'https://fconline.foundationcenter.org/rss/',
                'type': 'aggregator',
                'keywords': ['africa', 'children', 'education'],
                'priority': 'medium'
            },
            
            # === CHILD-FOCUSED ORGANIZATIONS (CRITICAL FOR ORPHANAGES) ===
            'Save the Children International': {
                'url': 'https://www.savethechildren.net/rss.xml',
                'type': 'children',
                'keywords': ['tanzania', 'africa', 'children', 'orphan'],
                'priority': 'very_high'
            },
            'UNICEF - East and Southern Africa': {
                'url': 'https://www.unicef.org/esa/press-releases/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa', 'children', 'orphan'],
                'priority': 'very_high'
            },
            'World Vision International': {
                'url': 'https://www.wvi.org/rss.xml',
                'type': 'children',
                'keywords': ['tanzania', 'africa', 'children', 'orphan', 'vulnerable'],
                'priority': 'very_high'
            },
            'ChildFund International': {
                'url': 'https://www.childfund.org/feed/',
                'type': 'children',
                'keywords': ['africa', 'children', 'education', 'tanzania'],
                'priority': 'very_high'
            },
            'SOS Children\'s Villages': {
                'url': 'https://www.sos-childrensvillages.org/news/rss',
                'type': 'children',
                'keywords': ['africa', 'children', 'orphan', 'family care'],
                'priority': 'very_high'
            },
            
            # === EDUCATION-SPECIFIC (Aligned with orphanage needs) ===
            'Global Partnership for Education': {
                'url': 'https://www.globalpartnership.org/rss.xml',
                'type': 'education',
                'keywords': ['tanzania', 'africa', 'education', 'children'],
                'priority': 'high'
            },
            'Education Cannot Wait': {
                'url': 'https://www.educationcannotwait.org/feed/',
                'type': 'education',
                'keywords': ['africa', 'education', 'children', 'crisis'],
                'priority': 'high'
            },
            'Room to Read': {
                'url': 'https://www.roomtoread.org/feed/',
                'type': 'education',
                'keywords': ['africa', 'education', 'children', 'literacy'],
                'priority': 'high'
            },
            'UNESCO Education': {
                'url': 'http://www.unevoc.unesco.org/unevoc_rss.xml',
                'type': 'UN',
                'keywords': ['education', 'africa', 'children'],
                'priority': 'medium'
            },
            
            # === HEALTH & NUTRITION (Important for orphanages) ===
            'WHO Africa': {
                'url': 'https://www.afro.who.int/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'africa', 'health', 'children'],
                'priority': 'medium'
            },
            'Gavi Alliance (Vaccines)': {
                'url': 'https://www.gavi.org/rss.xml',
                'type': 'foundation',
                'keywords': ['tanzania', 'africa', 'health', 'children'],
                'priority': 'medium'
            },
            'Global Fund': {
                'url': 'https://www.theglobalfund.org/data/rss-feeds/updates/',
                'type': 'foundation',
                'keywords': ['tanzania', 'africa', 'health'],
                'priority': 'medium'
            },
            'Nutrition International': {
                'url': 'https://www.nutritionintl.org/feed/',
                'type': 'foundation',
                'keywords': ['africa', 'nutrition', 'children', 'tanzania'],
                'priority': 'medium'
            },
            
            # === FOOD SECURITY & AGRICULTURE ===
            'World Food Programme (WFP)': {
                'url': 'https://www.wfp.org/news/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'africa', 'food', 'children', 'nutrition'],
                'priority': 'high'
            },
            'Food and Agriculture Organization (FAO)': {
                'url': 'https://www.fao.org/news/rss/en/',
                'type': 'UN',
                'keywords': ['tanzania', 'africa', 'agriculture', 'food', 'nutrition'],
                'priority': 'medium'
            },
            'CGIAR - Agricultural Research': {
                'url': 'https://www.cgiar.org/news/feed/',
                'type': 'multilateral',
                'keywords': ['tanzania', 'africa', 'agriculture', 'food'],
                'priority': 'medium'
            },
            'Alliance for a Green Revolution in Africa (AGRA)': {
                'url': 'https://agra.org/feed/',
                'type': 'foundation',
                'keywords': ['tanzania', 'east africa', 'agriculture', 'food'],
                'priority': 'medium'
            },
            'International Fund for Agricultural Development (IFAD)': {
                'url': 'https://www.ifad.org/en/rss',
                'type': 'multilateral',
                'keywords': ['tanzania', 'africa', 'agriculture', 'rural'],
                'priority': 'medium'
            },
            
            # === COMMUNITY DEVELOPMENT ===
            'UNDP Africa': {
                'url': 'https://www.undp.org/africa/rss.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa', 'africa', 'development'],
                'priority': 'medium'
            },
            'UN OCHA East Africa': {
                'url': 'https://www.unocha.org/rss/east-and-central-africa.xml',
                'type': 'UN',
                'keywords': ['tanzania', 'east africa', 'humanitarian'],
                'priority': 'medium'
            },
            
            # === BILATERAL DONORS ===
            'USAID - Business Opportunities': {
                'url': 'https://www.usaid.gov/rss/business.xml',
                'type': 'bilateral',
                'keywords': ['tanzania', 'east africa', 'africa', 'children', 'education'],
                'priority': 'high'
            },
            'UK FCDO - News': {
                'url': 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom',
                'type': 'bilateral',
                'keywords': ['tanzania', 'africa', 'development', 'children'],
                'priority': 'medium'
            },
            
            # === REGIONAL ORGANIZATIONS ===
            'African Development Bank': {
                'url': 'https://www.afdb.org/en/news-and-events/adf/rss',
                'type': 'multilateral',
                'keywords': ['tanzania', 'east africa', 'development'],
                'priority': 'medium'
            },
            'East African Community': {
                'url': 'https://www.eac.int/rss',
                'type': 'regional',
                'keywords': ['tanzania', 'east africa'],
                'priority': 'medium'
            },
            
            # === GENERAL FUNDING & GRANTS ===
            'ReliefWeb - Funding Announcements': {
                'url': 'https://reliefweb.int/updates?query=grant+OR+funding&format=rss',
                'type': 'aggregator',
                'keywords': ['tanzania', 'africa', 'children', 'education'],
                'priority': 'high'
            },
            'GlobalGiving - Tanzania': {
                'url': 'https://www.globalgiving.org/aboutus/media/rss/',
                'type': 'platform',
                'keywords': ['tanzania', 'africa', 'children'],
                'priority': 'high'
            },
            'Humentum': {
                'url': 'https://www.humentum.org/feed',
                'type': 'aggregator',
                'keywords': ['africa', 'grant', 'funding', 'ngo'],
                'priority': 'medium'
            },
            
            # === FAITH-BASED ORGANIZATIONS (Often support orphanages) ===
            'Catholic Relief Services': {
                'url': 'https://www.crs.org/rss.xml',
                'type': 'faith_based',
                'keywords': ['africa', 'tanzania', 'children', 'community'],
                'priority': 'high'
            },
        }
    
    def parse_feed(self, feed_name, feed_info):
        """Parse a single RSS feed with enhanced filtering"""
        print(f"   Checking: {feed_name}...")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            
            if feed.bozo:  # Feed parsing error
                print(f"    ⚠️  Feed error: {feed_name}")
                return 0
            
            if not feed.entries:
                print(f"    ℹ️  No entries found")
                return 0
            
            count = 0
            for entry in feed.entries[:30]:  # Check last 30 items (increased)
                entry_url = entry.get('link', '')
                
                # Skip if already seen (unless show_all mode)
                if not self.show_all and entry_url in self.seen_urls:
                    continue
                
                # Get entry details
                title = entry.get('title', '')
                description = entry.get('summary', entry.get('description', ''))
                published = entry.get('published', entry.get('updated', ''))
                
                # Combine text for relevance check
                full_text = f"{title} {description}".lower()
                
                # ENHANCED RELEVANCE CHECKS
                
                # 1. Check for ORPHANAGE-specific keywords (highest priority)
                has_orphanage_keyword = any(kw in full_text for kw in self.orphanage_keywords)
                
                # 2. Check geographic relevance
                geo_relevant = any(kw in full_text for kw in feed_info['keywords'])
                
                # 3. Check sector relevance
                sector_relevant = any(sector in full_text for sector in self.sectors)
                
                # 4. Check for funding keywords
                funding_keywords = ['grant', 'funding', 'opportunity', 'proposal', 'rfp', 
                                   'call', 'application', 'tender', 'competition', 'award',
                                   'donation', 'sponsor', 'partnership', 'support']
                has_funding_keyword = any(kw in full_text for kw in funding_keywords)
                
                # 5. Calculate relevance score early
                relevance = self.calculate_relevance(full_text, feed_info)
                
                # INCLUSION LOGIC (more sophisticated)
                include = False
                
                # Priority 1: High orphanage relevance
                if has_orphanage_keyword and has_funding_keyword:
                    include = True
                
                # Priority 2: Geographic + Sector + Funding
                elif geo_relevant and sector_relevant and has_funding_keyword:
                    include = True
                
                # Priority 3: High relevance score regardless
                elif relevance >= 6 and has_funding_keyword:
                    include = True
                
                if include:
                    self.opportunities.append({
                        'source': feed_name,
                        'source_type': feed_info['type'],
                        'priority': feed_info.get('priority', 'medium'),
                        'title': title,
                        'description': description[:600],  # Longer description
                        'url': entry_url,
                        'published': published,
                        'deadline': self.extract_deadline(full_text),
                        'amount': self.extract_amount(full_text),
                        'sectors': self.classify_sectors(full_text),
                        'relevance_score': relevance,
                        'orphanage_specific': has_orphanage_keyword,
                        'discovered': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'is_new': entry_url not in self.seen_urls
                    })
                    
                    self.seen_urls.add(entry_url)
                    count += 1
            
            if count > 0:
                print(f"    ✅ Found {count} relevant opportunities")
            return count
            
        except Exception as e:
            print(f"    ❌ Error parsing {feed_name}: {str(e)[:80]}")
            return 0
    
    def calculate_relevance(self, text, feed_info):
        """
        Enhanced relevance scoring (0-10) with orphanage focus
        """
        score = 0
        
        # ORPHANAGE-SPECIFIC SCORING (most important)
        orphanage_matches = sum(1 for kw in self.orphanage_keywords if kw in text)
        if orphanage_matches >= 3:
            score += 5  # Very high weight
        elif orphanage_matches >= 2:
            score += 4
        elif orphanage_matches >= 1:
            score += 3
        
        # Geography points
        if self.country in text:
            score += 2
        elif 'east africa' in text:
            score += 1.5
        elif 'africa' in text:
            score += 1
        
        # Sector points (reduced weight compared to orphanage keywords)
        sector_matches = sum(1 for sector in self.sectors if sector in text)
        score += min(sector_matches * 0.5, 2)  # Cap at 2 points
        
        # Feed priority bonus
        priority_bonus = {
            'very_high': 1.5,
            'high': 1,
            'medium': 0.5,
            'low': 0
        }
        score += priority_bonus.get(feed_info.get('priority', 'medium'), 0)
        
        # Urgency points
        if any(word in text for word in ['deadline', 'closing soon', 'urgent', 'apply now', 'limited time']):
            score += 1
        
        return min(round(score, 1), 10)  # Cap at 10
    
    def extract_deadline(self, text):
        """Extract deadline from text - improved patterns"""
        patterns = [
            r'deadline[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'closes?[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'application deadline[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'submit by[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_amount(self, text):
        """Extract funding amount - improved patterns"""
        patterns = [
            r'(?:up to|maximum|max|worth)\s+\$\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'\$\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'(?:USD|EUR|GBP|TZS)\s?\d+(?:,\d{3})*(?:\s?(?:million|thousand|[KMB]))?',
            r'\d+(?:,\d{3})*\s+(?:USD|EUR|GBP|TZS)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def classify_sectors(self, text):
        """Enhanced sector classification"""
        sectors = []
        
        sector_keywords = {
            'orphan_care': ['orphan', 'orphanage', 'residential care', 'children\'s home', 'foster'],
            'child_welfare': ['child welfare', 'child protection', 'vulnerable children', 'ovc', 'street children'],
            'education': ['education', 'school', 'learning', 'training', 'literacy', 'student', 'teacher'],
            'health': ['health', 'medical', 'hospital', 'clinic', 'healthcare', 'nutrition', 'disease'],
            'food_security': ['food security', 'hunger', 'malnutrition', 'food', 'feeding', 'meal'],
            'water_sanitation': ['water', 'sanitation', 'wash', 'hygiene', 'toilet'],
            'agriculture': ['agriculture', 'farming', 'crop', 'livestock', 'garden'],
            'community_development': ['community', 'development', 'empowerment', 'capacity building'],
            'psychosocial': ['counseling', 'mental health', 'trauma', 'psychosocial', 'wellbeing'],
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in text for kw in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    def scan_all_feeds(self):
        """Scan all RSS feeds"""
        print("="*70)
        print(" 🌍 ORPHANAGE DONOR RSS FEED AGGREGATOR")
        print(f" 📍 Focus: {self.country.title()} | {', '.join(self.sectors).title()}")
        print(f" 🎯 Orphanage-Optimized Search")
        if self.show_all:
            print(" 📋 Mode: SHOW ALL (including previously seen)")
        print("="*70)
        
        feeds = self.get_donor_feeds()
        
        # Organize by priority
        very_high = {k:v for k,v in feeds.items() if v.get('priority') == 'very_high'}
        high = {k:v for k,v in feeds.items() if v.get('priority') == 'high'}
        medium = {k:v for k,v in feeds.items() if v.get('priority') == 'medium'}
        
        print(f"\n 📡 Scanning {len(feeds)} RSS feeds...")
        print(f"    - Very High Priority: {len(very_high)}")
        print(f"    - High Priority: {len(high)}")
        print(f"    - Medium Priority: {len(medium)}\n")
        
        total_found = 0
        
        # Scan very high priority first
        if very_high:
            print(" 🔴 VERY HIGH PRIORITY FEEDS (Child-focused):")
            for feed_name, feed_info in very_high.items():
                found = self.parse_feed(feed_name, feed_info)
                total_found += found
                time.sleep(0.5)
        
        # Then high priority
        if high:
            print("\n 🟠 HIGH PRIORITY FEEDS:")
            for feed_name, feed_info in high.items():
                found = self.parse_feed(feed_name, feed_info)
                total_found += found
                time.sleep(0.5)
        
        # Finally medium priority
        if medium:
            print("\n 🟡 MEDIUM PRIORITY FEEDS:")
            for feed_name, feed_info in medium.items():
                found = self.parse_feed(feed_name, feed_info)
                total_found += found
                time.sleep(0.5)
        
        print("\n" + "="*70)
        
        new_count = len([o for o in self.opportunities if o.get('is_new', True)])
        orphanage_specific = len([o for o in self.opportunities if o.get('orphanage_specific', False)])
        
        if self.show_all:
            print(f" ✅ Scan complete! Found {len(self.opportunities)} relevant opportunities")
            print(f"    - {new_count} are NEW")
            print(f"    - {orphanage_specific} are ORPHANAGE-SPECIFIC 🎯")
            print(f"    - {len(self.opportunities)-new_count} previously seen")
        else:
            print(f" ✅ Scan complete! Found {new_count} NEW relevant opportunities")
            if orphanage_specific > 0:
                print(f"    - {orphanage_specific} are ORPHANAGE-SPECIFIC 🎯")
        
        print("="*70)
        
        # Save seen URLs
        self.save_seen_urls()
        
        if len(self.opportunities) == 0:
            print("\n ℹ️  No new opportunities found this time.")
            print("    This is normal - RSS feeds update periodically.")
            print("    💡 Run this daily to catch new opportunities as they appear!")
            print("    💡 Try running with --all flag to see previously found opportunities")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.opportunities)
        
        # Sort: orphanage-specific first, then by relevance
        df = df.sort_values(['orphanage_specific', 'relevance_score'], ascending=[False, False])
        
        return df
    
    def generate_report(self, df):
        """Generate enhanced summary report"""
        if len(df) == 0:
            return
        
        print("\n" + "="*70)
        print(" 📊 OPPORTUNITY SUMMARY")
        print("="*70)
        
        print(f"\n 📈 Total opportunities: {len(df)}")
        
        orphanage_specific = df[df['orphanage_specific'] == True]
        if len(orphanage_specific) > 0:
            print(f" 🎯 ORPHANAGE-SPECIFIC: {len(orphanage_specific)} ⭐⭐⭐")
        
        print(f" 🔥 High relevance (8-10): {len(df[df['relevance_score'] >= 8])}")
        print(f" 📌 Medium relevance (5-7): {len(df[(df['relevance_score'] >= 5) & (df['relevance_score'] < 8)])}")
        
        with_deadlines = df[df['deadline'].notna()]
        if len(with_deadlines) > 0:
            print(f" ⏰ With DEADLINES: {len(with_deadlines)}")
        
        with_amounts = df[df['amount'].notna()]
        if len(with_amounts) > 0:
            print(f" 💰 With funding amounts: {len(with_amounts)}")
        
        print("\n 📁 By Source Type:")
        print(df['source_type'].value_counts().to_string())
        
        print("\n 🏷️  By Sector:")
        all_sectors = []
        for sectors in df['sectors']:
            if isinstance(sectors, list):
                all_sectors.extend(sectors)
        if all_sectors:
            sector_counts = pd.Series(all_sectors).value_counts().head(8)
            print(sector_counts.to_string())
        
        # ORPHANAGE-SPECIFIC OPPORTUNITIES (if any)
        if len(orphanage_specific) > 0:
            print("\n" + "="*70)
            print(" 🎯 TOP ORPHANAGE-SPECIFIC OPPORTUNITIES ⭐")
            print("="*70)
            
            for i, (_, row) in enumerate(orphanage_specific.head(5).iterrows(), 1):
                print(f"\n{i}. 🎯 {row['title']}")
                print(f"   📍 Source: {row['source']}")
                print(f"   ⭐ Relevance: {row['relevance_score']}/10")
                print(f"   🏷️  Sectors: {', '.join(row['sectors']) if isinstance(row['sectors'], list) else row['sectors']}")
                if row['deadline']:
                    print(f"   ⏰ Deadline: {row['deadline']}")
                if row['amount']:
                    print(f"   💰 Amount: {row['amount']}")
                print(f"   🔗 {row['url']}")
        
        # TOP OVERALL OPPORTUNITIES
        print("\n" + "="*70)
        print(" 🏆 TOP 10 MOST RELEVANT OPPORTUNITIES")
        print("="*70)
        
        for i, (_, row) in enumerate(df.head(10).iterrows(), 1):
            orphanage_marker = "🎯 " if row.get('orphanage_specific') else ""
            print(f"\n{i}. {orphanage_marker}{row['title'][:100]}")
            print(f"   📍 {row['source']}")
            print(f"   ⭐ Relevance: {row['relevance_score']}/10")
            print(f"   🏷️  {', '.join(row['sectors'][:3]) if isinstance(row['sectors'], list) else row['sectors']}")
            if row['deadline']:
                print(f"   ⏰ {row['deadline']}")
            if row['amount']:
                print(f"   💰 {row['amount']}")
            print(f"   🔗 {row['url']}")
        
        # URGENT DEADLINES
        if len(with_deadlines) > 0:
            print("\n" + "="*70)
            print(f" ⏰ URGENT - {len(with_deadlines)} OPPORTUNITIES WITH DEADLINES")
            print("="*70)
            for i, (_, row) in enumerate(with_deadlines.head(10).iterrows(), 1):
                orphanage_marker = "🎯 " if row.get('orphanage_specific') else ""
                print(f"\n{i}. {orphanage_marker}{row['title'][:80]}")
                print(f"   ⏰ Deadline: {row['deadline']}")
                print(f"   ⭐ Relevance: {row['relevance_score']}/10")
                print(f"   🔗 {row['url']}")


# ============================================================================
# RUN THE RSS AGGREGATOR
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check for command line flags
    show_all = '--all' in sys.argv
    
    print("\n" + "="*70)
    print(" 🌍 ORPHANAGE DONOR OPPORTUNITY FINDER")
    print(" Helping you find funding for orphan care, education & wellbeing")
    print("="*70)
    
    aggregator = ImprovedDonorRSSAggregator(
        country="Tanzania",
        sectors=["children", "education", "health", "food", "agriculture"],
        show_all=show_all,
        email_alerts=False  # Set to True if you configure email
    )
    
    if show_all:
        print("\n 📋 Running in SHOW ALL mode")
    
    print("\n ⏱️  Starting RSS feed scan (this takes 2-3 minutes)...\n")
    
    results = aggregator.scan_all_feeds()
    
    if len(results) > 0:
        aggregator.generate_report(results)
        
        # Save results with timestamps
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # 1. All results
        filename = f"donor_opportunities_{timestamp}.csv"
        results.to_csv(filename, index=False)
        print(f"\n 💾 Full results saved: {filename}")
        
        # 2. Orphanage-specific
        orphanage_specific = results[results['orphanage_specific'] == True]
        if len(orphanage_specific) > 0:
            orphanage_file = f"ORPHANAGE_SPECIFIC_{timestamp}.csv"
            orphanage_specific.to_csv(orphanage_file, index=False)
            print(f" 🎯 Orphanage-specific: {orphanage_file}")
        
        # 3. High priority (relevance >= 7)
        priority = results[results['relevance_score'] >= 7]
        if len(priority) > 0:
            priority_file = f"HIGH_PRIORITY_{timestamp}.csv"
            priority.to_csv(priority_file, index=False)
            print(f" ⭐ High priority: {priority_file}")
        
        # 4. Urgent (with deadlines)
        urgent = results[results['deadline'].notna()]
        if len(urgent) > 0:
            urgent_file = f"URGENT_DEADLINES_{timestamp}.csv"
            urgent.to_csv(urgent_file, index=False)
            print(f" ⏰ Urgent deadlines: {urgent_file}")
        
        # Success summary
        print("\n" + "="*70)
        print(" ✅ SCAN COMPLETE - NEXT STEPS:")
        print("="*70)
        print(" 1. Review the ORPHANAGE_SPECIFIC file first (highest relevance)")
        print(" 2. Check URGENT_DEADLINES for time-sensitive opportunities")
        print(" 3. Review HIGH_PRIORITY for other strong matches")
        print(" 4. Run this script DAILY to catch new opportunities")
        print(" 5. Use --all flag to review previously seen opportunities")
        print("="*70)
    
    print("\n 🙏 Good luck finding funding for the orphanage!")
    print("="*70)