"""
permit_scraper.py — Pulls new construction permits from OpenDataPhilly
Uses the free Licenses & Inspections permits API (no key required)
Filters to target zip codes
"""

import requests
import json
from datetime import datetime, timedelta

# OpenDataPhilly L&I Permits API
PERMITS_API = "https://phl.carto.com/api/v2/sql"

TARGET_ZIPS = {
    "19123","19122","19121","19130","19134","19145","19146","19147","19148",
    "19125","19103","19102","19107","19106","19129","19127","19128","19119","19118"
}

# Permit type keywords to track
PERMIT_KEYWORDS = [
    "NEW CONSTRUCTION",
    "ADDITION",
    "ALTERATION",
    "RENOVATION",
    "DEMOLITION"
]


def get_permits(days_back=1):
    """
    Fetch permits issued in the last N days from OpenDataPhilly.
    Returns list of permit dicts filtered to target zip codes.
    """
    print(f"Fetching permits from OpenDataPhilly (last {days_back} days)...")

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    # Build zip code filter
    zip_list = ",".join(f"'{z}'" for z in TARGET_ZIPS)

    query = f"""
        SELECT
            permitnumber,
            address,
            unit,
            zip,
            typeofwork,
            description,
            contractorname,
            opa_account_num,
            approvedscope,
            mostrecentinsp,
            permitissuedate,
            status,
            lat,
            lng
        FROM permits
        WHERE
            zip IN ({zip_list})
            AND permitissuedate >= '{since_date}'
            AND typeofwork IS NOT NULL
        ORDER BY permitissuedate DESC
        LIMIT 500
    """

    params = {
        "q": query,
        "format": "json"
    }

    try:
        resp = requests.get(PERMITS_API, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("rows", [])

        permits = []
        for row in rows:
            type_of_work = str(row.get("typeofwork", "")).upper()

            # Classify permit type
            permit_type = "Other"
            if "NEW CONSTRUCTION" in type_of_work or "NEW CONST" in type_of_work:
                permit_type = "New Construction"
            elif "DEMO" in type_of_work:
                permit_type = "Demolition"
            elif "ADDITION" in type_of_work:
                permit_type = "Addition"
            elif "ALTERATION" in type_of_work or "RENOVATION" in type_of_work or "INTERIOR" in type_of_work:
                permit_type = "Renovation/Alteration"

            # Parse issue date
            issue_date = row.get("permitissuedate", "")
            if issue_date:
                try:
                    issue_date = datetime.strptime(issue_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    pass

            permits.append({
                "permit_number":   row.get("permitnumber", ""),
                "address":         row.get("address", ""),
                "zip":             str(row.get("zip", "")).strip(),
                "permit_type":     permit_type,
                "type_of_work":    row.get("typeofwork", ""),
                "description":     row.get("description", ""),
                "contractor":      row.get("contractorname", ""),
                "opa_account":     row.get("opa_account_num", ""),
                "scope":           row.get("approvedscope", ""),
                "issue_date":      issue_date,
                "status":          row.get("status", ""),
                "lat":             row.get("lat"),
                "lng":             row.get("lng"),
                "scraped_at":      datetime.utcnow().isoformat()
            })

        print(f"  ✓ Got {len(permits)} permits in target zip codes")

        # Summary by type
        from collections import Counter
        types = Counter(p["permit_type"] for p in permits)
        for t, count in types.most_common():
            print(f"    {t}: {count}")

        return permits

    except Exception as e:
        print(f"  ✗ Permit fetch error: {e}")
        return []


def get_all_recent_permits(days_back=90):
    """
    Fetch last 90 days of permits for initial Airtable population.
    """
    return get_permits(days_back=days_back)


if __name__ == "__main__":
    permits = get_permits(days_back=7)
    print(f"\nTotal: {len(permits)} permits")
    if permits:
        print("Sample:", json.dumps(permits[0], indent=2))
