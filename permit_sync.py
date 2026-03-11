"""
permit_sync.py — Syncs permits to Airtable Permits table
"""

import os
import requests
import json
import time
from typing import List, Dict

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
TABLE_NAME = "Permits"

BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

FIELD_MAP = {
    "permit_number":  "Permit Number",
    "address":        "Address",
    "zip":            "Zip",
    "permit_type":    "Permit Type",
    "type_of_work":   "Type of Work",
    "description":    "Description",
    "contractor":     "Contractor",
    "scope":          "Scope",
    "issue_date":     "Issue Date",
    "status":         "Status",
    "lat":            "Lat",
    "lng":            "Lng",
    "scraped_at":     "Last Updated"
}

NUMERIC_FIELDS = {"Lat", "Lng"}


def permit_to_fields(permit: Dict) -> Dict:
    fields = {}
    for our_key, at_key in FIELD_MAP.items():
        val = permit.get(our_key)
        if val is None or val == "":
            continue
        if at_key in NUMERIC_FIELDS:
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
        elif isinstance(val, float):
            val = round(val, 6)
        fields[at_key] = str(val) if not isinstance(val, (int, float)) else val
    return fields


def get_existing_permit_numbers() -> Dict[str, str]:
    """Fetch existing permit numbers → record IDs."""
    existing = {}
    offset = None

    while True:
        params = {"fields[]": "Permit Number", "pageSize": 100}
        if offset:
            params["offset"] = offset

        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"  ✗ Failed to fetch existing permits: {resp.text[:200]}")
            return {}

        data = resp.json()
        for rec in data.get("records", []):
            pnum = rec.get("fields", {}).get("Permit Number", "")
            if pnum:
                existing[pnum] = rec["id"]

        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.2)

    return existing


def batch_upsert_permits(permits: List[Dict]) -> int:
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("  ✗ Missing Airtable credentials")
        return 0

    print(f"Syncing {len(permits)} permits to Airtable...")
    existing = get_existing_permit_numbers()
    print(f"  Found {len(existing)} existing permit records")

    to_create = []
    to_update = []

    for permit in permits:
        fields = permit_to_fields(permit)
        pnum = permit.get("permit_number", "")
        if pnum in existing:
            to_update.append({"id": existing[pnum], "fields": fields})
        else:
            to_create.append({"fields": fields})

    written = 0

    for i in range(0, len(to_create), 10):
        batch = to_create[i:i+10]
        resp = requests.post(BASE_URL, headers=HEADERS,
                             data=json.dumps({"records": batch}), timeout=15)
        if resp.status_code in (200, 201):
            written += len(batch)
        else:
            print(f"  ✗ Create failed: {resp.status_code} {resp.text[:200]}")
        time.sleep(0.25)

    for i in range(0, len(to_update), 10):
        batch = to_update[i:i+10]
        resp = requests.patch(BASE_URL, headers=HEADERS,
                              data=json.dumps({"records": batch}), timeout=15)
        if resp.status_code == 200:
            written += len(batch)
        else:
            print(f"  ✗ Update failed: {resp.status_code} {resp.text[:200]}")
        time.sleep(0.25)

    print(f"  ✓ Wrote {written} permit records ({len(to_create)} new, {len(to_update)} updated)")
    return written
