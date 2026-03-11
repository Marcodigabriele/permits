import requests
import json
from datetime import datetime, timedelta

PERMITS_API = "https://phl.carto.com/api/v2/sql"

TARGET_ZIPS = {
    "19123","19122","19121","19130","19134","19145","19146","19147","19148",
    "19125","19103","19102","19107","19106","19129","19127","19128","19119","19118"
}

def get_permits(days_back=1):
    print(f"Fetching permits from OpenDataPhilly (last {days_back} days)...")
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    zip_list = ",".join(f"'{z}'" for z in TARGET_ZIPS)
    query = f"""SELECT permitnumber, address, zip, typeofwork, description, contractorname, opa_account_num, approvedscope, permitissuedate, status, lat, lng FROM permits WHERE zip IN ({zip_list}) AND permitissuedate >= '{since_date}' AND typeofwork IS NOT NULL ORDER BY permitissuedate DESC LIMIT 500"""
    try:
        resp = requests.get(PERMITS_API, params={"q": query, "format": "json"}, timeout=30)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        permits = []
        for row in rows:
            t = str(row.get("typeofwork", "")).upper()
            ptype = "Other"
            if "NEW CONSTRUCTION" in t or "NEW CONST" in t: ptype = "New Construction"
            elif "DEMO" in t: ptype = "Demolition"
            elif "ADDITION" in t: ptype = "Addition"
            elif "ALTERATION" in t or "RENOVATION" in t: ptype = "Renovation/Alteration"
            issue_date = row.get("permitissuedate", "")
            if issue_date:
                try: issue_date = datetime.strptime(issue_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                except: pass
            permits.append({"permit_number": row.get("permitnumber",""), "address": row.get("address",""), "zip": str(row.get("zip","")).strip(), "permit_type": ptype, "type_of_work": row.get("typeofwork",""), "description": row.get("description",""), "contractor": row.get("contractorname",""), "opa_account": row.get("opa_account_num",""), "scope": row.get("approvedscope",""), "issue_date": issue_date, "status": row.get("status",""), "lat": row.get("lat"), "lng": row.get("lng"), "scraped_at": datetime.utcnow().isoformat()})
        print(f"  Got {len(permits)} permits")
        return permits
    except Exception as e:
        print(f"  Permit fetch error: {e}")
        return []

def get_all_recent_permits(days_back=90):
    return get_permits(days_back=days_back)
