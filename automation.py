import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import pandas as pd

# Import your RSS aggregator
# from rss_aggregator import DonorRSSAggregator

class DailyDonorAlert:
    """
    Automated daily scanner with email alerts
    Run this once per day via cron/scheduler
    """
    
    def __init__(self, email_to, email_from=None, email_password=None):
        self.email_to = email_to
        self.email_from = email_from or os.getenv('EMAIL_FROM')
        self.email_password = email_password or os.getenv('EMAIL_PASSWORD')
        
        # Email settings for Gmail (adjust for other providers)
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def run_daily_scan(self):
        """Run the RSS scan"""
        print(f"\n🗓️  DAILY SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)
        
        # Import and run your aggregator
        # For now, this is a placeholder - you'll integrate your actual code
        from rss_donor_aggregator import DonorRSSAggregator
        
        aggregator = DonorRSSAggregator(
            country="Tanzania",
            sectors=["education", "health"]
        )
        
        results = aggregator.scan_all_feeds()
        
        return results
    
    def send_email_alert(self, df):
        """Send email with new opportunities"""
        
        if len(df) == 0:
            print("📧 No new opportunities - skipping email")
            return
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🎯 {len(df)} New Donor Opportunities - {datetime.now().strftime("%b %d, %Y")}'
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        
        # Create HTML email body
        html = self.create_email_html(df)
        
        msg.attach(MIMEText(html, 'html'))
        
        # Attach CSV
        timestamp = datetime.now().strftime('%Y%m%d')
        csv_filename = f'opportunities_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)
        
        with open(csv_filename, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={csv_filename}')
        msg.attach(attachment)
        
        # Send email
        try:
            print(f"📧 Sending email to {self.email_to}...")
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print("✅ Email sent successfully!")
            
        except Exception as e:
            print(f"⚠️ Email error: {e}")
            print("💡 Make sure you've enabled 'App Passwords' in Gmail settings")
    
    def create_email_html(self, df):
        """Create HTML email content"""
        
        # Sort by relevance
        df = df.sort_values('relevance_score', ascending=False)
        
        # Get high priority
        high_priority = df[df['relevance_score'] >= 7]
        urgent = df[df['deadline'].notna()]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #f3f4f6; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .opportunity {{ border-left: 4px solid #2563eb; padding: 15px; margin: 15px 0; background: #fafafa; }}
                .high-priority {{ border-left-color: #dc2626; }}
                .urgent {{ border-left-color: #f59e0b; }}
                .label {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 12px; margin-right: 5px; }}
                .label-priority {{ background: #dc2626; color: white; }}
                .label-urgent {{ background: #f59e0b; color: white; }}
                .label-sector {{ background: #2563eb; color: white; }}
                a {{ color: #2563eb; text-decoration: none; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Daily Donor Opportunities Report</h1>
                <p>Tanzania • Education & Health • {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <p><strong>Total New Opportunities:</strong> {len(df)}</p>
                <p><strong>High Priority (8-10):</strong> {len(high_priority)}</p>
                <p><strong>With Deadlines:</strong> {len(urgent)}</p>
            </div>
        """
        
        # Add urgent opportunities first
        if len(urgent) > 0:
            html += """
            <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h2>🚨 URGENT - Upcoming Deadlines</h2>
            """
            
            for _, row in urgent.head(5).iterrows():
                sectors_str = ', '.join(row['sectors']) if isinstance(row['sectors'], list) else str(row['sectors'])
                html += f"""
                <div class="opportunity urgent">
                    <span class="label label-urgent">DEADLINE: {row['deadline']}</span>
                    <h3>{row['title']}</h3>
                    <p><strong>Source:</strong> {row['source']}</p>
                    <p><strong>Sectors:</strong> {sectors_str}</p>
                    {f"<p><strong>Amount:</strong> {row['amount']}</p>" if row['amount'] else ""}
                    <p>{row['description'][:200]}...</p>
                    <p><a href="{row['url']}" target="_blank">View Full Opportunity →</a></p>
                </div>
                """
            
            html += "</div>"
        
        # Add high priority opportunities
        if len(high_priority) > 0:
            html += "<h2>⭐ High Priority Opportunities</h2>"
            
            for _, row in high_priority.head(10).iterrows():
                sectors_str = ', '.join(row['sectors']) if isinstance(row['sectors'], list) else str(row['sectors'])
                html += f"""
                <div class="opportunity high-priority">
                    <span class="label label-priority">RELEVANCE: {row['relevance_score']}/10</span>
                    <span class="label label-sector">{sectors_str}</span>
                    <h3>{row['title']}</h3>
                    <p><strong>Source:</strong> {row['source']}</p>
                    {f"<p><strong>Deadline:</strong> {row['deadline']}</p>" if row['deadline'] else ""}
                    {f"<p><strong>Amount:</strong> {row['amount']}</p>" if row['amount'] else ""}
                    <p>{row['description'][:250]}...</p>
                    <p><a href="{row['url']}" target="_blank">View Full Opportunity →</a></p>
                </div>
                """
        
        # Add all other opportunities
        other = df[df['relevance_score'] < 7]
        if len(other) > 0:
            html += f"<h2>📋 Other Opportunities ({len(other)})</h2>"
            html += "<p><em>See attached CSV for complete list</em></p>"
        
        html += """
            <div class="footer">
                <p>This is an automated daily report from your Donor Opportunity Tracker.</p>
                <p>To stop receiving these emails or adjust settings, update your configuration.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def run(self):
        """Main execution"""
        print("\n🤖 AUTOMATED DAILY DONOR SCAN")
        print("="*70)
        
        # Run scan
        results = self.run_daily_scan()
        
        # Send email if we have results
        if len(results) > 0:
            self.send_email_alert(results)
        else:
            print("\n📭 No new opportunities today - no email sent")
        
        print("\n✅ Daily scan complete!")
        print("="*70)


# SETUP INSTRUCTIONS
def print_setup_instructions():
    """Print setup guide"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   AUTOMATION SETUP GUIDE                              ║
╚══════════════════════════════════════════════════════════════════════╝

📧 EMAIL SETUP (Gmail):
1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Generate an App Password:
   - Visit: https://myaccount.google.com/apppasswords
   - Select 'Mail' and your device
   - Copy the 16-character password

4. Create a .env file in your project folder:
   
   EMAIL_FROM=your_email@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password
   EMAIL_TO=your_email@gmail.com

📅 DAILY AUTOMATION:

OPTION 1 - Linux/Mac (Cron):
---------------------------------
1. Open crontab:
   crontab -e

2. Add this line (runs daily at 9 AM):
   0 9 * * * cd /path/to/your/project && /path/to/python automation.py

OPTION 2 - Windows (Task Scheduler):
-------------------------------------
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: C:\\Python\\python.exe
   - Arguments: C:\\path\\to\\automation.py
   - Start in: C:\\path\\to\\project

OPTION 3 - Cloud Deployment (FREE):
------------------------------------
Deploy to a free cloud service that runs it for you:

A) Railway.app (Recommended):
   - Connect GitHub repo
   - Add cron schedule
   - Set environment variables
   
B) Heroku (with scheduler add-on):
   - Deploy your app
   - Add Heroku Scheduler
   - Run: python automation.py

C) PythonAnywhere (free tier):
   - Upload your code
   - Set up scheduled task

🧪 TEST IT FIRST:
-----------------
python automation.py

This will run once and send you an email if opportunities are found.

💡 TIPS:
- Start by running manually for a week to ensure it works
- Check spam folder for first email
- Adjust relevance thresholds based on results
- Add more RSS feeds as you discover them
    """)


# RUN
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        print_setup_instructions()
    else:
        # Load email from environment or config
        EMAIL_TO = os.getenv('EMAIL_TO', 'your_email@gmail.com')
        
        if EMAIL_TO == 'your_email@gmail.com':
            print("⚠️  Please configure your email first!")
            print("Run: python automation.py setup")
            sys.exit(1)
        
        # Run the daily scan
        scanner = DailyDonorAlert(email_to=EMAIL_TO)
        scanner.run()