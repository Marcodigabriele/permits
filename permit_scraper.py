import requests
import json
from datetime import datetime, timedelta

PERMITS_API = "https://phl.carto.com/api/v2/sql"

TARGET_ZIPS = {
    "19123","19122","19121","19130","19134","19145","19146","19147","19148",
    "19125","19103","19102","19107","19106","19129","19127","19128","19119","19118"
}

def get_column_names():
    """Fetch actual column names from the permits table."""
    query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'permits' ORDER BY ordinal_position"
    resp = requests.get(PERMITS_API, params={"q": query, "format": "json"}, timeout=30)
    if resp.status_code == 200:
        cols = [r["column_name"] for r in resp.json().get("rows", [])]
        print(f"  Permits table columns: {cols}")
        return cols
    else:
        print(f"  Could not fetch columns: {resp.text[:200]}")
        return []

def get_permits(days_back=1):
    print(f"Fetching permits from OpenDataPhilly (last {days_back} days)...")

    # First discover real column names
    cols = get_column_names()

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    zip_list = ",".join(f"'{z}'" for z in TARGET_ZIPS)

    # Build SELECT only from columns that exist
    def col(name): return name if name in cols else None

    select_parts = ["ST_Y(the_geom) AS lat", "ST_X(the_geom) AS lng"]
    for c in ["permitnumber", "address", "zip", "typeofwork", "contractorname",
              "approvedscope", "permitissuedate", "status", "description",
              "opa_account_num", "mostrecentinsp"]:
        if c in cols:
            select_parts.append(c)

    select_clause = ", ".join(select_parts)

    # Find the right date column
    date_col = None
    for candidate in ["permitissuedate", "issuedate", "issue_date", "permitdate"]:
        if candidate in cols:
            date_col = candidate
            break

    if not date_col:
        print("  Could not find date column!")
        return []

    query = (
        f"SELECT {select_clause} FROM permits "
        f"WHERE zip IN ({zip_list}) "
        f"AND {date_col} >= '{since_date}' "
        f"ORDER BY {date_col} DESC "
        f"LIMIT 500"
    )

    try:
        resp = requests.get(PERMITS_API, params={"q": query, "format": "json"}, timeout=30)
        print(f"  API status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  API error: {resp.text[:500]}")
            return []

        rows = resp.json().get("rows", [])
        permits = []
        for row in rows:
            t = str(row.get("typeofwork", "")).upper()
            ptype = "Other"
            if "NEW CONSTRUCTION" in t or "NEW CONST" in t:
                ptype = "New Construction"
            elif "DEMO" in t:
                ptype = "Demolition"
            elif "ADDITION" in t:
                ptype = "Addition"
            elif "ALTERATION" in t or "RENOVATION" in t or "INTERIOR" in t:
                ptype = "Renovation/Alteration"

            issue_date = row.get(date_col, "")
            if issue_date:
                try:
                    issue_date = datetime.strptime(issue_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    pass

            permits.append({
                "permit_number": row.get("permitnumber", ""),
                "address":       row.get("address", ""),
                "zip":           str(row.get("zip", "")).strip(),
                "permit_type":   ptype,
                "type_of_work":  row.get("typeofwork", ""),
                "description":   row.get("description", ""),
                "contractor":    row.get("contractorname", ""),
                "scope":         row.get("approvedscope", ""),
                "issue_date":    issue_date,
                "status":        row.get("status", ""),
                "lat":           row.get("lat"),
                "lng":           row.get("lng"),
                "scraped_at":    datetime.utcnow().isoformat()
            })

        print(f"  Got {len(permits)} permits")
        from collections import Counter
        for t, c in Counter(p["permit_type"] for p in permits).most_common():
            print(f"    {t}: {c}")
        return permits

    except Exception as e:
        print(f"  Permit fetch error: {e}")
        return []

def get_all_recent_permits(days_back=90):
    return get_permits(days_back=days_back)

if __name__ == "__main__":
    permits = get_permits(days_back=7)
    print(f"\nTotal: {len(permits)} permits")
    if permits:
        print("Sample:", json.dumps(permits[0], indent=2))
