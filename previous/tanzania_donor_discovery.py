import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re
import json

class TanzaniaDonorDiscovery:
    def __init__(self):
        self.country = "Tanzania"
        self.sectors = ["education", "health"]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_comprehensive_donor_list(self):
        """
        Comprehensive list of donors active in Tanzania - Education & Health focus
        Categorized by type for better tracking
        """
        return {
            'bilateral_donors': [
                {
                    'name': 'USAID Tanzania',
                    'url': 'https://www.usaid.gov/tanzania',
                    'grants_page': 'https://www.usaid.gov/tanzania/work-with-us',
                    'focus': ['health', 'education', 'governance'],
                    'typical_range': '$50K - $5M',
                    'notes': 'Major funder in Tanzania, regular RFPs'
                },
                {
                    'name': 'UK FCDO Tanzania',
                    'url': 'https://www.gov.uk/world/organisations/dfid-tanzania',
                    'grants_page': 'https://www.ukaiddirect.org/',
                    'focus': ['education', 'health', 'governance'],
                    'typical_range': '£10K - £1M',
                    'notes': 'UK Aid Direct specifically for small organizations'
                },
                {
                    'name': 'Irish Aid Tanzania',
                    'url': 'https://www.ireland.ie/en/dfa/missions/tanzania/',
                    'grants_page': 'https://www.irishaid.ie/what-we-do/countries-where-we-work/our-partner-countries/tanzania/',
                    'focus': ['health', 'education', 'governance'],
                    'typical_range': '€20K - €500K',
                    'notes': 'Strong focus on health and education'
                },
                {
                    'name': 'Swiss Agency for Development (SDC) Tanzania',
                    'url': 'https://www.eda.admin.ch/countries/tanzania/en/home.html',
                    'grants_page': 'https://www.eda.admin.ch/countries/tanzania/en/home/international-cooperation.html',
                    'focus': ['health', 'education', 'governance'],
                    'typical_range': 'CHF 50K - CHF 1M',
                    'notes': 'Focus on Southern Highlands'
                },
                {
                    'name': 'Canada (Global Affairs) Tanzania',
                    'url': 'https://www.international.gc.ca/country-pays/tanzania-tanzanie/index.aspx',
                    'grants_page': 'https://www.international.gc.ca/world-monde/funding-financement/index.aspx',
                    'focus': ['education', 'health', 'gender'],
                    'typical_range': 'CAD 25K - CAD 1M',
                    'notes': 'Strong education focus'
                }
            ],
            
            'multilateral_donors': [
                {
                    'name': 'Global Fund Tanzania',
                    'url': 'https://www.theglobalfund.org/en/portfolio/tanzania/',
                    'grants_page': 'https://www.theglobalfund.org/en/funding-model/',
                    'focus': ['health', 'HIV/AIDS', 'TB', 'malaria'],
                    'typical_range': '$500K - $10M+',
                    'notes': 'Large health programs, often through CCM'
                },
                {
                    'name': 'EU Tanzania',
                    'url': 'https://www.eeas.europa.eu/tanzania_en',
                    'grants_page': 'https://webgate.ec.europa.eu/europeaid/online-services/',
                    'focus': ['education', 'health', 'governance'],
                    'typical_range': '€50K - €5M',
                    'notes': 'Check PADOR registration requirement'
                },
                {
                    'name': 'World Bank Tanzania',
                    'url': 'https://www.worldbank.org/en/country/tanzania',
                    'grants_page': 'https://projects.worldbank.org/en/projects-operations/projects-list?countrycode_exact=TZ',
                    'focus': ['education', 'health', 'infrastructure'],
                    'typical_range': '$100K - $50M+',
                    'notes': 'Large projects, often government partnerships'
                },
                {
                    'name': 'African Development Bank',
                    'url': 'https://www.afdb.org/en/countries/east-africa/tanzania',
                    'grants_page': 'https://www.afdb.org/en/projects-and-operations',
                    'focus': ['education', 'health', 'infrastructure'],
                    'typical_range': '$200K - $10M+',
                    'notes': 'Infrastructure and systems strengthening'
                }
            ],
            
            'un_agencies': [
                {
                    'name': 'UNICEF Tanzania',
                    'url': 'https://www.unicef.org/tanzania/',
                    'grants_page': 'https://www.unicef.org/tanzania/opportunities',
                    'focus': ['education', 'health', 'child protection'],
                    'typical_range': '$30K - $500K',
                    'notes': 'Strong focus on children and youth'
                },
                {
                    'name': 'WHO Tanzania',
                    'url': 'https://www.afro.who.int/countries/united-republic-of-tanzania',
                    'grants_page': 'https://www.who.int/about/careers',
                    'focus': ['health', 'disease prevention'],
                    'typical_range': '$50K - $1M',
                    'notes': 'Health systems and disease control'
                },
                {
                    'name': 'UNDP Tanzania',
                    'url': 'https://www.undp.org/tanzania',
                    'grants_page': 'https://www.undp.org/tanzania/procurement-notices',
                    'focus': ['governance', 'livelihoods', 'health'],
                    'typical_range': '$25K - $1M',
                    'notes': 'Check procurement notices regularly'
                },
                {
                    'name': 'UNESCO Tanzania',
                    'url': 'https://en.unesco.org/fieldoffice/daressalaam',
                    'grants_page': 'https://en.unesco.org/funding',
                    'focus': ['education', 'culture', 'science'],
                    'typical_range': '$20K - $500K',
                    'notes': 'Education quality and access'
                },
                {
                    'name': 'UNFPA Tanzania',
                    'url': 'https://tanzania.unfpa.org/',
                    'grants_page': 'https://tanzania.unfpa.org/en/opportunities',
                    'focus': ['health', 'reproductive health', 'youth'],
                    'typical_range': '$30K - $500K',
                    'notes': 'Maternal health, family planning'
                }
            ],
            
            'foundations': [
                {
                    'name': 'Bill & Melinda Gates Foundation',
                    'url': 'https://www.gatesfoundation.org/',
                    'grants_page': 'https://www.gatesfoundation.org/about/how-we-work/general-information/grant-opportunities',
                    'focus': ['health', 'education', 'agriculture'],
                    'typical_range': '$100K - $10M+',
                    'notes': 'Invitation only, but tracks innovations'
                },
                {
                    'name': 'Aga Khan Foundation',
                    'url': 'https://www.akdn.org/our-agencies/aga-khan-foundation',
                    'grants_page': 'https://www.akdn.org/akf-east-africa',
                    'focus': ['education', 'health', 'early childhood'],
                    'typical_range': '$50K - $2M',
                    'notes': 'Active in Tanzania, especially Coast region'
                },
                {
                    'name': 'Comic Relief',
                    'url': 'https://www.comicrelief.com/',
                    'grants_page': 'https://www.comicrelief.com/funding',
                    'focus': ['health', 'education', 'livelihoods'],
                    'typical_range': '£10K - £500K',
                    'notes': 'Rolling applications, UK-based'
                },
                {
                    'name': 'Mastercard Foundation',
                    'url': 'https://mastercardfdn.org/',
                    'grants_page': 'https://mastercardfdn.org/partnerships/',
                    'focus': ['education', 'youth employment'],
                    'typical_range': '$500K - $50M',
                    'notes': 'Large education programs in East Africa'
                },
                {
                    'name': 'Open Society Foundations',
                    'url': 'https://www.opensocietyfoundations.org/',
                    'grants_page': 'https://www.opensocietyfoundations.org/grants',
                    'focus': ['education', 'health', 'rights'],
                    'typical_range': '$25K - $500K',
                    'notes': 'Equity and access focus'
                },
                {
                    'name': 'Conrad N. Hilton Foundation',
                    'url': 'https://www.hiltonfoundation.org/',
                    'grants_page': 'https://www.hiltonfoundation.org/grants',
                    'focus': ['health', 'safe water'],
                    'typical_range': '$100K - $2M',
                    'notes': 'Invitation only but track their work'
                }
            ],
            
            'crowdfunding_platforms': [
                {
                    'name': 'GlobalGiving',
                    'url': 'https://www.globalgiving.org/',
                    'grants_page': 'https://www.globalgiving.org/fundraise/',
                    'focus': ['various'],
                    'typical_range': '$5K - $50K',
                    'notes': 'Must qualify and get verified'
                },
                {
                    'name': 'Chuffed',
                    'url': 'https://chuffed.org/',
                    'grants_page': 'https://chuffed.org/start-fundraising',
                    'focus': ['various'],
                    'typical_range': '$1K - $30K',
                    'notes': 'Social enterprise friendly'
                },
                {
                    'name': 'Benevity',
                    'url': 'https://www.benevity.com/',
                    'grants_page': 'https://causes.benevity.org/',
                    'focus': ['various'],
                    'typical_range': '$500 - $10K',
                    'notes': 'Corporate giving platform'
                }
            ]
        }
    
    def check_opportunity_page(self, donor):
        """Check donor page for active opportunities with detailed analysis"""
        print(f"  🔍 Checking {donor['name']}...")
        
        try:
            response = requests.get(donor['grants_page'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text().lower()
            
            # Enhanced keyword detection
            active_indicators = {
                'open': ['open', 'accepting applications', 'now accepting'],
                'deadline': ['deadline', 'due date', 'closing date', 'submissions by'],
                'call': ['call for proposals', 'rfp', 'request for proposal', 'funding opportunity'],
                'apply': ['apply now', 'submit application', 'application form']
            }
            
            signals = {}
            for category, keywords in active_indicators.items():
                signals[category] = any(kw in text for kw in keywords)
            
            activity_score = sum(signals.values())
            
            # Extract dates
            deadlines = self.extract_dates_advanced(soup)
            
            # Look for dollar amounts
            amounts = self.extract_funding_amounts(text)
            
            return {
                'donor': donor['name'],
                'type': donor.get('type', 'Unknown'),
                'url': donor['grants_page'],
                'sectors': ', '.join(donor['focus']),
                'typical_range': donor.get('typical_range', 'Unknown'),
                'activity_score': activity_score,
                'has_open_call': signals['call'],
                'has_deadline': signals['deadline'],
                'deadlines_found': ', '.join(deadlines[:3]),
                'amounts_mentioned': ', '.join(amounts[:2]),
                'notes': donor.get('notes', ''),
                'checked': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
        except Exception as e:
            print(f"    ⚠️ Error: {str(e)[:50]}")
            return {
                'donor': donor['name'],
                'type': donor.get('type', 'Unknown'),
                'url': donor['grants_page'],
                'sectors': ', '.join(donor['focus']),
                'typical_range': donor.get('typical_range', 'Unknown'),
                'activity_score': 0,
                'has_open_call': False,
                'has_deadline': False,
                'deadlines_found': 'Error checking',
                'amounts_mentioned': '',
                'notes': donor.get('notes', ''),
                'checked': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
    
    def extract_dates_advanced(self, soup):
        """Extract dates with better parsing"""
        dates = []
        text = soup.get_text()
        
        patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))[:5]
    
    def extract_funding_amounts(self, text):
        """Extract funding amounts mentioned"""
        patterns = [
            r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?(?:\s?[KMB])?',
            r'(?:USD|EUR|GBP|CHF)\s?\d+(?:,\d{3})*',
            r'£\s?\d+(?:,\d{3})*(?:\.\d{2})?(?:\s?[KMB])?',
            r'€\s?\d+(?:,\d{3})*(?:\.\d{2})?(?:\s?[KMB])?'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))[:5]
    
    def scan_all(self):
        """Main scanning function"""
        print("="*70)
        print("🇹🇿 TANZANIA DONOR DISCOVERY SYSTEM")
        print("🎯 Focus: Education & Health")
        print("="*70)
        
        all_donors_dict = self.get_comprehensive_donor_list()
        all_results = []
        
        for category, donors in all_donors_dict.items():
            print(f"\n📂 Scanning {category.replace('_', ' ').title()} ({len(donors)} donors)")
            print("-" * 70)
            
            for i, donor in enumerate(donors, 1):
                donor['type'] = category.replace('_', ' ').title()
                result = self.check_opportunity_page(donor)
                all_results.append(result)
                time.sleep(2)  # Be respectful
        
        df = pd.DataFrame(all_results)
        
        # Sort by activity score
        df = df.sort_values('activity_score', ascending=False)
        
        return df
    
    def generate_report(self, df):
        """Generate prioritized report"""
        print("\n" + "="*70)
        print("📊 SCAN COMPLETE - DONOR ANALYSIS REPORT")
        print("="*70)
        
        print(f"\n✅ Total donors scanned: {len(df)}")
        print(f"🔥 High activity (score 3+): {len(df[df['activity_score'] >= 3])}")
        print(f"⚡ Medium activity (score 2): {len(df[df['activity_score'] == 2])}")
        print(f"💤 Low activity (score 0-1): {len(df[df['activity_score'] <= 1])}")
        
        print("\n🏆 TOP PRIORITY DONORS (Activity Score 3+):")
        print("-" * 70)
        top = df[df['activity_score'] >= 3]
        if len(top) > 0:
            for _, row in top.iterrows():
                print(f"\n⭐ {row['donor']} (Score: {row['activity_score']})")
                print(f"   Type: {row['type']}")
                print(f"   Range: {row['typical_range']}")
                print(f"   URL: {row['url']}")
                if row['deadlines_found'] and row['deadlines_found'] != 'Error checking':
                    print(f"   📅 Deadlines: {row['deadlines_found']}")
                print(f"   💡 {row['notes']}")
        else:
            print("   No high-activity donors detected. Check medium activity list.")
        
        print("\n\n⚡ MEDIUM PRIORITY DONORS (Activity Score 2):")
        print("-" * 70)
        medium = df[df['activity_score'] == 2]
        for _, row in medium.head(5).iterrows():
            print(f"• {row['donor']} - {row['url']}")
        
        return df


# RUN THE SCAN
if __name__ == "__main__":
    system = TanzaniaDonorDiscovery()
    
    print("\n🚀 Starting comprehensive donor scan...")
    print("⏱️  This will take 3-5 minutes...\n")
    
    results = system.scan_all()
    report = system.generate_report(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Full results
    filename = f"tanzania_donors_full_{timestamp}.csv"
    results.to_csv(filename, index=False)
    print(f"\n💾 Full results: {filename}")
    
    # Priority list
    priority = results[results['activity_score'] >= 2]
    priority_file = f"tanzania_donors_PRIORITY_{timestamp}.csv"
    priority.to_csv(priority_file, index=False)
    print(f"⭐ Priority list: {priority_file}")
    
    print("\n✅ Scan complete! Review the priority file first.")