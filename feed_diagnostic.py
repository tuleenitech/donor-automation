import feedparser
import requests
from datetime import datetime
import time

class FeedDiagnostic:
    """
    Diagnostic tool to check which RSS feeds are working
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_all_feeds(self):
        """Get the same feed list from your aggregator"""
        return {
            'FundsForNGOs': 'https://www2.fundsforngos.org/feed/',
            'Devex Funding': 'https://www.devex.com/news/funding/rss',
            'ReliefWeb Tanzania': 'https://reliefweb.int/updates?advanced-search=%28PC236%29&format=rss',
            'ReliefWeb Jobs EA': 'https://reliefweb.int/jobs?search=east+africa&format=rss',
            'USAID Business': 'https://www.usaid.gov/rss/business.xml',
            'UNICEF ESA': 'https://www.unicef.org/esa/press-releases/rss.xml',
            'WHO Africa': 'https://www.afro.who.int/rss.xml',
            'UNDP Africa': 'https://www.undp.org/africa/rss.xml',
            'UN OCHA EA': 'https://www.unocha.org/rss/east-and-central-africa.xml',
            'Global Fund': 'https://www.theglobalfund.org/en/rss/',
            'Global Partnership Education': 'https://www.globalpartnership.org/rss.xml',
            'Education Cannot Wait': 'https://www.educationcannotwait.org/feed/',
            'Gavi Alliance': 'https://www.gavi.org/rss.xml',
            'AfDB News': 'https://www.afdb.org/en/rss/news-press-releases',
            'EAC': 'https://www.eac.int/rss',
            'GlobalGiving': 'https://www.globalgiving.org/aboutus/media/rss/',
            'Chuffed': 'https://blog.chuffed.org/feed/',
            'Humentum': 'https://www.humentum.org/feed',
            'UK FCDO': 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom',
        }
    
    def test_feed(self, name, url):
        """Test a single feed and return detailed status"""
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print('-'*70)
        
        result = {
            'name': name,
            'url': url,
            'status': 'Unknown',
            'error': None,
            'entries_count': 0,
            'last_updated': None,
            'feed_title': None,
            'http_status': None
        }
        
        try:
            # First, try to access the URL directly
            print("  [1/3] Checking HTTP connection...")
            response = requests.get(url, headers=self.headers, timeout=15)
            result['http_status'] = response.status_code
            
            if response.status_code == 200:
                print(f"  ✅ HTTP {response.status_code} OK")
            else:
                print(f"  ⚠️ HTTP {response.status_code}")
                result['status'] = f'HTTP {response.status_code}'
                result['error'] = f'Server returned {response.status_code}'
                return result
            
            # Parse the feed
            print("  [2/3] Parsing feed...")
            feed = feedparser.parse(url)
            
            # Check if feed parsed successfully
            if feed.bozo:
                print(f"  ⚠️ Feed parsing error: {feed.bozo_exception}")
                result['status'] = 'Parse Error'
                result['error'] = str(feed.bozo_exception)
                
                # Still try to get some info
                if hasattr(feed, 'feed'):
                    result['feed_title'] = feed.feed.get('title', 'Unknown')
                if hasattr(feed, 'entries') and len(feed.entries) > 0:
                    result['entries_count'] = len(feed.entries)
                    print(f"  ℹ️  Despite error, found {len(feed.entries)} entries")
                
                return result
            
            # Feed is valid
            print("  ✅ Feed parsed successfully")
            result['status'] = 'Working'
            
            # Get feed info
            if hasattr(feed, 'feed'):
                result['feed_title'] = feed.feed.get('title', 'Unknown')
                result['last_updated'] = feed.feed.get('updated', 'Unknown')
                print(f"  📰 Feed Title: {result['feed_title']}")
                print(f"  🕒 Last Updated: {result['last_updated']}")
            
            # Count entries
            print("  [3/3] Checking entries...")
            result['entries_count'] = len(feed.entries)
            print(f"  📊 Found {result['entries_count']} entries")
            
            # Show sample of recent entries
            if result['entries_count'] > 0:
                print(f"\n  📋 Sample entries (most recent 3):")
                for i, entry in enumerate(feed.entries[:3], 1):
                    title = entry.get('title', 'No title')
                    published = entry.get('published', entry.get('updated', 'No date'))
                    print(f"    {i}. {title[:60]}...")
                    print(f"       Published: {published}")
            else:
                print("  ⚠️ Feed is valid but has no entries")
            
            print(f"\n  ✅ SUCCESS - Feed is working properly")
            
        except requests.exceptions.Timeout:
            print("  ❌ Connection timeout")
            result['status'] = 'Timeout'
            result['error'] = 'Connection timed out after 15 seconds'
            
        except requests.exceptions.ConnectionError:
            print("  ❌ Connection failed")
            result['status'] = 'Connection Error'
            result['error'] = 'Could not connect to server'
            
        except Exception as e:
            print(f"  ❌ Unexpected error: {str(e)}")
            result['status'] = 'Error'
            result['error'] = str(e)
        
        return result
    
    def run_full_diagnostic(self):
        """Test all feeds and generate report"""
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║               RSS FEED DIAGNOSTIC TOOL                               ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(self.get_all_feeds())} RSS feeds...\n")
        
        feeds = self.get_all_feeds()
        results = []
        
        for name, url in feeds.items():
            result = self.test_feed(name, url)
            results.append(result)
            time.sleep(1)  # Be polite to servers
        
        # Generate summary report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """Generate summary report"""
        print("\n\n")
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║                         DIAGNOSTIC REPORT                            ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        
        # Count statuses
        working = [r for r in results if r['status'] == 'Working']
        errors = [r for r in results if r['status'] not in ['Working', 'Unknown']]
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total feeds tested: {len(results)}")
        print(f"  ✅ Working: {len(working)}")
        print(f"  ❌ Errors: {len(errors)}")
        print(f"  Success rate: {len(working)/len(results)*100:.1f}%")
        
        # Working feeds
        if working:
            print(f"\n✅ WORKING FEEDS ({len(working)}):")
            for r in working:
                print(f"  • {r['name']}: {r['entries_count']} entries")
        
        # Broken feeds
        if errors:
            print(f"\n❌ PROBLEMATIC FEEDS ({len(errors)}):")
            for r in errors:
                print(f"\n  • {r['name']}")
                print(f"    Status: {r['status']}")
                print(f"    Error: {r['error']}")
                print(f"    URL: {r['url']}")
        
        # Recommendations
        print("\n\n💡 RECOMMENDATIONS:")
        
        if len(errors) > len(working):
            print("  ⚠️ Most feeds are having issues. This could be:")
            print("    1. Network/firewall blocking RSS requests")
            print("    2. Your IP being rate-limited")
            print("    3. Many sites changed their RSS URLs")
            print("\n  Try:")
            print("    - Run this from a different network")
            print("    - Wait a few hours and try again")
            print("    - Use a VPN if your network blocks RSS")
        
        elif errors:
            print("  ⚠️ Some feeds need to be updated:")
            for r in errors:
                print(f"    - Remove or update: {r['name']}")
        
        else:
            print("  ✅ All feeds working! Your RSS aggregator should work great.")
        
        # Additional tips
        print("\n\n📝 NEXT STEPS:")
        print("  1. Remove broken feeds from rss_aggregator.py")
        print("  2. Try to find updated RSS URLs for broken feeds")
        print("  3. Focus on the working feeds for now")
        print("  4. Run this diagnostic weekly to catch changes")
        
        print("\n" + "="*70 + "\n")


# RUN DIAGNOSTIC
if __name__ == "__main__":
    diagnostic = FeedDiagnostic()
    
    print("\n🔍 Starting comprehensive RSS feed diagnostic...")
    print("⏱️  This will take 2-3 minutes to test all feeds...\n")
    
    results = diagnostic.run_full_diagnostic()
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"feed_diagnostic_{timestamp}.txt"
    
    print(f"\n💾 Full diagnostic report saved to: {filename}")
    print("\n✅ Diagnostic complete!")