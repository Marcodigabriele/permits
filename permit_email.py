"""
permit_email.py — Sends daily permit digest to Marco@Rarityre.com via Gmail
Requires env vars: GMAIL_USER, GMAIL_APP_PASSWORD
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

GMAIL_USER        = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TO_EMAIL          = "Marco@Rarityre.com"

TYPE_COLORS = {
    "New Construction":      "#ff4f4f",
    "Demolition":            "#f5a623",
    "Addition":              "#34c77b",
    "Renovation/Alteration": "#7a9ff5",
    "Other":                 "#7a7f96",
}


def build_email_html(permits: List[Dict], date_str: str) -> str:
    if not permits:
        return f"""
        <div style="font-family:monospace;background:#0f1117;color:#e8eaf0;padding:32px;border-radius:8px;">
            <h2 style="color:#f5a623;">Philly Permits — {date_str}</h2>
            <p style="color:#7a7f96;">No new permits found in target zip codes today.</p>
        </div>
        """

    # Group by zip
    by_zip = defaultdict(list)
    for p in permits:
        by_zip[p.get("zip", "Unknown")].append(p)

    # Stats
    new_const = sum(1 for p in permits if p.get("permit_type") == "New Construction")
    demos     = sum(1 for p in permits if p.get("permit_type") == "Demolition")
    renos     = sum(1 for p in permits if "Renovation" in p.get("permit_type", ""))

    rows_html = ""
    for zip_code in sorted(by_zip.keys()):
        zip_permits = by_zip[zip_code]
        rows_html += f"""
        <tr>
            <td colspan="4" style="background:#1a1d27;color:#f5a623;font-weight:700;
                padding:10px 14px;font-size:13px;border-top:2px solid #2a2d3a;">
                📍 {zip_code} — {len(zip_permits)} permit{'s' if len(zip_permits) > 1 else ''}
            </td>
        </tr>
        """
        for p in zip_permits:
            color = TYPE_COLORS.get(p.get("permit_type", "Other"), "#7a7f96")
            rows_html += f"""
            <tr style="border-bottom:1px solid #2a2d3a;">
                <td style="padding:10px 14px;color:#e8eaf0;font-size:12px;">
                    {p.get("address", "—")}
                </td>
                <td style="padding:10px 14px;">
                    <span style="background:{color}22;color:{color};border:1px solid {color}44;
                        padding:2px 8px;border-radius:3px;font-size:11px;white-space:nowrap;">
                        {p.get("permit_type", "—")}
                    </span>
                </td>
                <td style="padding:10px 14px;color:#7a7f96;font-size:11px;">
                    {p.get("contractor", "—")}
                </td>
                <td style="padding:10px 14px;color:#7a7f96;font-size:11px;">
                    {p.get("issue_date", "—")}
                </td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#0a0c12;">
    <div style="max-width:700px;margin:0 auto;font-family:'DM Mono',monospace,sans-serif;">

        <!-- Header -->
        <div style="background:#0f1117;border-bottom:1px solid #2a2d3a;padding:24px 28px;">
            <div style="font-size:22px;font-weight:700;color:#e8eaf0;">
                Philly <span style="color:#f5a623;">Permits</span>
            </div>
            <div style="font-size:12px;color:#7a7f96;margin-top:4px;">
                Daily digest — {date_str}
            </div>
        </div>

        <!-- Stats -->
        <div style="display:flex;background:#1a1d27;border-bottom:1px solid #2a2d3a;">
            <div style="flex:1;padding:16px 20px;border-right:1px solid #2a2d3a;">
                <div style="font-size:24px;font-weight:700;color:#e8eaf0;">{len(permits)}</div>
                <div style="font-size:10px;color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                    Total Permits
                </div>
            </div>
            <div style="flex:1;padding:16px 20px;border-right:1px solid #2a2d3a;">
                <div style="font-size:24px;font-weight:700;color:#ff4f4f;">{new_const}</div>
                <div style="font-size:10px;color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                    New Construction
                </div>
            </div>
            <div style="flex:1;padding:16px 20px;border-right:1px solid #2a2d3a;">
                <div style="font-size:24px;font-weight:700;color:#f5a623;">{demos}</div>
                <div style="font-size:10px;color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                    Demolitions
                </div>
            </div>
            <div style="flex:1;padding:16px 20px;">
                <div style="font-size:24px;font-weight:700;color:#7a9ff5;">{renos}</div>
                <div style="font-size:10px;color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                    Renovations
                </div>
            </div>
        </div>

        <!-- Table -->
        <div style="background:#0f1117;padding:0;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#1a1d27;">
                        <th style="padding:10px 14px;text-align:left;font-size:10px;
                            color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                            Address
                        </th>
                        <th style="padding:10px 14px;text-align:left;font-size:10px;
                            color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                            Type
                        </th>
                        <th style="padding:10px 14px;text-align:left;font-size:10px;
                            color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                            Contractor
                        </th>
                        <th style="padding:10px 14px;text-align:left;font-size:10px;
                            color:#7a7f96;text-transform:uppercase;letter-spacing:0.8px;">
                            Issued
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div style="background:#1a1d27;padding:16px 28px;border-top:1px solid #2a2d3a;">
            <div style="font-size:11px;color:#7a7f96;">
                Rarity Real Estate · Philly Deals Platform ·
                <a href="https://app.softr.io" style="color:#f5a623;text-decoration:none;">
                    View Dashboard →
                </a>
            </div>
        </div>

    </div>
    </body>
    </html>
    """
    return html


def send_permit_digest(permits: List[Dict]) -> bool:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("  ✗ Missing GMAIL_USER or GMAIL_APP_PASSWORD env vars")
        return False

    date_str = datetime.now().strftime("%B %d, %Y")
    new_only = [p for p in permits if p.get("permit_type") == "New Construction"]
    total    = len(permits)

    subject = f"🏗 Philly Permits — {total} new permits ({len(new_only)} new construction) · {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = TO_EMAIL

    html_content = build_email_html(permits, date_str)
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        print(f"  ✓ Email sent to {TO_EMAIL} ({total} permits)")
        return True
    except Exception as e:
        print(f"  ✗ Email failed: {e}")
        return False


if __name__ == "__main__":
    # Test with mock data
    mock = [
        {"address": "123 Test St", "zip": "19123", "permit_type": "New Construction",
         "contractor": "ABC Builders", "issue_date": "2024-01-15", "description": "New 3-story SFH"},
        {"address": "456 Oak Ave", "zip": "19125", "permit_type": "Demolition",
         "contractor": "Demo Co", "issue_date": "2024-01-15", "description": "Full demolition"},
    ]
    send_permit_digest(mock)
