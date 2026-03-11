"""
permit_main.py — Runs the daily permit pipeline:
  1. Fetch new permits from OpenDataPhilly
  2. Sync to Airtable Permits table
  3. Send email digest
"""

import json
import sys
from datetime import datetime
from permit_scraper import get_permits, get_all_recent_permits
from permit_sync import batch_upsert_permits
from permit_email import send_permit_digest


def run(initial_load=False):
    print("=" * 55)
    print(f"  Philly Permits Pipeline — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    # Step 1: Fetch permits
    if initial_load:
        # First run — load last 90 days
        permits = get_all_recent_permits(days_back=90)
    else:
        # Daily run — last 2 days (buffer for any delays in city data)
        permits = get_permits(days_back=2)

    if not permits:
        print("\n⚠️  No permits retrieved. OpenDataPhilly may be down.")
        # Don't exit — still send email noting no permits
        send_permit_digest([])
        sys.exit(0)

    # Step 2: Sync to Airtable
    batch_upsert_permits(permits)

    # Step 3: Email digest (only truly new permits from last 1 day)
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_permits = [p for p in permits if p.get("issue_date", "") >= yesterday]

    print(f"\n📊 Results:")
    print(f"   {len(permits)} total permits synced")
    print(f"   {len(new_permits)} new permits issued since yesterday")

    new_const = [p for p in new_permits if p.get("permit_type") == "New Construction"]
    demos     = [p for p in new_permits if p.get("permit_type") == "Demolition"]
    print(f"   {len(new_const)} new construction")
    print(f"   {len(demos)} demolitions")

    send_permit_digest(new_permits)

    # Save backup
    with open("latest_permits.json", "w") as f:
        json.dump(permits[:200], f, indent=2)
    print("\n✓ Saved latest_permits.json")
    print("✓ Permit pipeline complete\n")


if __name__ == "__main__":
    import sys
    initial = "--initial" in sys.argv
    run(initial_load=initial)
