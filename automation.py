"""
Donor Opportunity Automation System
Scans RSS feeds daily and sends email alerts for new opportunities
"""

import smtplib
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from rss_aggregator import DonorRSSAggregator


# -------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# -------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------
load_dotenv()


# -------------------------------------------------
# MAIN AUTOMATION CLASS
# -------------------------------------------------
class DailyDonorAlert:
    """
    Automated daily donor opportunity scanner with email alerts
    """

    def __init__(self, email_to: str):
        self.email_to = email_to
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_password = os.getenv("EMAIL_PASSWORD")

        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        self._validate_email_config()

    def _validate_email_config(self) -> None:
        """Fail fast if email config is broken"""
        missing = []

        if not self.email_from:
            missing.append("EMAIL_FROM")
        if not self.email_password:
            missing.append("EMAIL_PASSWORD")
        if not self.email_to:
            missing.append("EMAIL_TO")

        if missing:
            logger.error(" Missing required environment variables:")
            for var in missing:
                logger.error(f"   - {var}")
            logger.error("\n Fix your .env file and retry")
            sys.exit(1)

    # -------------------------------------------------
    # SCAN RSS FEEDS
    # -------------------------------------------------
    def run_daily_scan(self) -> pd.DataFrame:
        """Execute RSS feed scan"""
        logger.info(f"\n  DAILY SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        logger.info("=" * 70)

        try:
            aggregator = DonorRSSAggregator(
                country="Tanzania",
                sectors=["education", "health", "agriculture", "food"]
            )

            results = aggregator.scan_all_feeds()

            if not isinstance(results, pd.DataFrame):
                raise ValueError("Aggregator must return a pandas DataFrame")

            logger.info(f" Found {len(results)} opportunities")
            return results

        except Exception as e:
            logger.error(f" Scan failed: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame()

    # -------------------------------------------------
    # EMAIL SENDER
    # -------------------------------------------------
    def send_email_alert(self, df: pd.DataFrame) -> None:
        """Send email with opportunities"""
        if df.empty:
            logger.info(" No new opportunities — email skipped")
            return

        msg = MIMEMultipart("alternative")
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg["Subject"] = (
            f" {len(df)} New Donor Opportunities — "
            f"{datetime.now().strftime('%b %d, %Y')}"
        )

        html_body = self.create_email_html(df)
        msg.attach(MIMEText(html_body, "html"))

        csv_path = self._attach_csv(df, msg)

        try:
            logger.info(f" Sending email to {self.email_to}...")

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            logger.info(" Email sent successfully!")

        except smtplib.SMTPAuthenticationError:
            logger.error(" Authentication failed - check your App Password")
            logger.error(" Visit: https://myaccount.google.com/apppasswords")

        except smtplib.SMTPException as e:
            logger.error(f" SMTP error: {e}")

        except Exception as e:
            logger.error(f" Unexpected email error: {e}")

        finally:
            if csv_path and os.path.exists(csv_path):
                os.remove(csv_path)
                logger.debug(f" Cleaned up temporary file: {csv_path}")

    def _attach_csv(self, df: pd.DataFrame, msg: MIMEMultipart) -> str:
        """Attach CSV file to email"""
        filename = f"opportunities_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            df.to_csv(filename, index=False)

            with open(filename, "rb") as f:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(f.read())

            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"'
            )

            msg.attach(attachment)
            return filename

        except Exception as e:
            logger.error(f" Failed to attach CSV: {e}")
            return None

    # -------------------------------------------------
    # EMAIL HTML BUILDER
    # -------------------------------------------------
    def create_email_html(self, df: pd.DataFrame) -> str:
        """Generate HTML email body"""
        df = df.sort_values("relevance_score", ascending=False)

        high_priority = df[df["relevance_score"] >= 7]
        urgent = df[df["deadline"].notna()]

        def safe(val) -> str:
            """Safely convert value to string"""
            if pd.isna(val) or val in [None, ""]:
                return "N/A"
            return str(val)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #f3f4f6; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .opportunity {{ border-left: 4px solid #2563eb; padding: 15px; margin: 15px 0; background: #fafafa; }}
                .urgent {{ border-left-color: #dc2626; background: #fef2f2; }}
                .high-priority {{ border-left-color: #f59e0b; }}
                a {{ color: #2563eb; text-decoration: none; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1> Daily Donor Opportunities</h1>
                <p>Tanzania • Education, Health, Agriculture & Food Security • {datetime.now().strftime('%B %d, %Y')}</p>
            </div>

            <div class="summary">
                <h2> Summary</h2>
                <ul>
                    <li><strong>Total Opportunities:</strong> {len(df)}</li>
                    <li><strong>High Priority (8-10):</strong> {len(high_priority)}</li>
                    <li><strong>With Deadlines:</strong> {len(urgent)}</li>
                </ul>
            </div>
        """

        if not urgent.empty:
            html += """
            <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h2> URGENT - Upcoming Deadlines</h2>
            """
            
            for _, row in urgent.head(5).iterrows():
                sectors = ', '.join(row['sectors']) if isinstance(row['sectors'], list) else safe(row['sectors'])
                html += f"""
                <div class="opportunity urgent">
                    <h3>{safe(row['title'])}</h3>
                    <p><strong> Deadline:</strong> {safe(row['deadline'])}</p>
                    <p><strong>Source:</strong> {safe(row['source'])}</p>
                    <p><strong>Sectors:</strong> {sectors}</p>
                    {f"<p><strong>Amount:</strong> {safe(row['amount'])}</p>" if pd.notna(row.get('amount')) else ""}
                    <p><a href="{row['url']}" target="_blank">View Full Opportunity →</a></p>
                </div>
                """
            
            html += "</div>"

        if not high_priority.empty:
            html += "<h2> High Priority Opportunities</h2>"
            
            for _, row in high_priority.head(10).iterrows():
                sectors = ', '.join(row['sectors']) if isinstance(row['sectors'], list) else safe(row['sectors'])
                html += f"""
                <div class="opportunity high-priority">
                    <h3>{safe(row['title'])}</h3>
                    <p><strong>Relevance:</strong> {safe(row['relevance_score'])}/10</p>
                    <p><strong>Source:</strong> {safe(row['source'])}</p>
                    <p><strong>Sectors:</strong> {sectors}</p>
                    {f"<p><strong>Deadline:</strong> {safe(row['deadline'])}</p>" if pd.notna(row.get('deadline')) else ""}
                    {f"<p><strong>Amount:</strong> {safe(row['amount'])}</p>" if pd.notna(row.get('amount')) else ""}
                    <p><a href="{row['url']}" target="_blank">View Full Opportunity →</a></p>
                </div>
                """

        # Show count of other opportunities
        other = df[df['relevance_score'] < 7]
        if not other.empty:
            html += f"""
            <div style="background: #f9fafb; padding: 15px; margin: 20px 0;">
                <p><strong> Other Opportunities:</strong> {len(other)}</p>
                <p><em>See attached CSV for complete list</em></p>
            </div>
            """

        html += """
            <div class="footer">
                <p>This is an automated daily report from your Donor Opportunity Tracker.</p>
                <p>Data sourced from RSS feeds • Not affiliated with any donor organization</p>
            </div>
        </body>
        </html>
        """

        return html

    # -------------------------------------------------
    # MAIN RUNNER
    # -------------------------------------------------
    def run(self) -> None:
        """Execute the full automation workflow"""
        try:
            logger.info("\n AUTOMATED DAILY DONOR SCAN")
            logger.info("=" * 70)
            
            results = self.run_daily_scan()
            
            if not results.empty:
                self.send_email_alert(results)
            else:
                logger.info(" No opportunities found - no email sent")
            
            logger.info("\n Daily scan completed successfully")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"\n Automation failed: {e}", exc_info=True)
            sys.exit(1)

# -------------------------------------------------
# CLI ENTRYPOINT
# -------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        sys.exit(0)

    EMAIL_TO = os.getenv("EMAIL_TO")

    if not EMAIL_TO:
        logger.error(" EMAIL_TO not configured in .env file")
        logger.error(" Run: python automation.py setup")
        sys.exit(1)

    scanner = DailyDonorAlert(email_to=EMAIL_TO)
    scanner.run()