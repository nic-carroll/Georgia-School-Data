#!/usr/bin/env python3
"""
Third-Party Application Registry Data Builder

Fetches Georgia Southern's live third-party vendor security/privacy review
tracker (a Google Sheet the IT team maintains by hand as new vendors are
requested/reviewed/renewed) and converts it into JSON for the Third-Party
Apps registry page (thirdpartyapps.html), the same way the GOSA scripts in
this directory turn CSVs into fetch-on-demand JSON for the other pages.

Source: a Google Sheet, exported as CSV over HTTP (public "anyone with the
link can view" sharing required -- an authenticated/private sheet will come
back as a Google login page, not CSV, and this script will fail loudly
rather than silently write a bad file).

Every row is a real vendor review record: product name, vendor, the review
status history, GDPR/FERPA/COPPA compliance claims, security attestations
(HECVAT/SOC 2), cited policy URLs, and answers to a ~29-question rubric
(GENQ1 general + DCQ1-5 Data Collection + SECQ1-5 Security + SHRQ1-5 Third
Party Data + ADVQ1-5 Advertising + USGQ1-13 USG IT Handbook, the last being
Georgia Southern's own addition on top of the upstream rubric categories).
The sheet's own rollup columns (RUBRIC: DATA COLLECTION, ..., CERTIFIED) are
all literally "NOT YET SCORED" for every row as of this writing -- this
script does NOT invent a rollup. The per-question answers (Meets/Partially/
Unmet/N/A/Unknown/Not yet scored) are real per-row values, so the client
computes its own rubric-category tallies from those at render time instead.

Deliberately dropped: the "Original Requester Email" and "Vendor Contact
Email" columns are real Georgia Southern staff / vendor contact addresses.
This script never reads them into the output at all -- not into the
gitignored copy, not into the committed one -- since client/data/ is
published to a public GitHub Pages site (see CLAUDE.md "Live demo").

"Status" and "Assessment History" are the same pipe-separated append log
(verified: identical value distributions). Segments read oldest-to-newest
left-to-right (e.g. "Information Security Review | Security Review Denied"
reads as review-in-progress, then denied) -- the rightmost segment is
treated as the current status and drives the derived `rating` badge. The
full segment list is kept as `statusHistory` so nothing is lost if that
ordering assumption is ever wrong for a given row.

Produces:
  server/data/thirdparty_apps/apps.json (gitignored, compact)
  server/data/thirdparty_apps/meta.json (gitignored, pretty)
  client/data/thirdpartyapps/apps.json (committed, compact -- fetched by
    thirdpartyapps.html)
  client/data/thirdpartyapps/meta.json (committed, pretty)

Shape of apps.json: {"<id>": {name, vendor, initialRequestDate, statusRaw,
statusHistory, rating, compliance: {gdpr, ferpa, coppa, under13,
accessibilityStatement}, security: {hecvat, soc2}, policies: {privacyPolicy,
termsOfService, accessibilityStatementUrl, trustCenter}, dataClasses,
verificationMethod, rubricScored, sourceRecords, rubric: {general: {genq1},
dataCollection: {dcq1..dcq5, notes}, security: {secq1..secq5, notes},
thirdPartyData: {shrq1..shrq5, notes}, advertising: {advq1..advq5, notes},
usgHandbook: {usgq1..usgq13, notes}}}, ...}
"""

import os
import csv
import io
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

SHEET_ID = "1GCAvxfE2_Lp5f23rH7ieviDK23dhlAY8p-ZRznc3cOk"
SHEET_GID = "1347534544"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "thirdparty_apps"))
CLIENT_OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "client", "data", "thirdpartyapps"))

# Rightmost status-history segment -> derived rating badge. Anything not
# listed here (including a blank/never-reviewed row) falls back to
# "unrated", matching the real TAMS product's own default of leaving a
# rating unset rather than guessing.
STATUS_TO_RATING = {
    "Review Complete - Submitted to Purchasing for Processing": "approved",
    "Assessment Renewed": "approved",
    "Assessment Not Renewed": "expired",
    "Security Review Denied": "denied",
    "Information Security Review": "under_review",
    "Renewal Email Provided": "renewal_pending",
}

DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_MDY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")

# The two dedicated email columns are never read (see module docstring), but
# that alone is not enough: this is a hand-maintained sheet, and addresses
# leak into free-text columns -- one "Vendor Name" cell is filled in with a
# staff member's own address. Every string that reaches the output is
# scrubbed, and the count is printed at build time so a new leak surfaces in
# the run log instead of shipping silently to the public Pages site.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_PLACEHOLDER = "[email removed]"
REDACTIONS = []


def redact_emails(value):
    """Replaces any email address inside a free-text value with a visible
    placeholder. The field is kept rather than blanked, so the surrounding
    real text survives and the redaction is auditable rather than a silent
    hole in the data."""
    if not isinstance(value, str) or not EMAIL_RE.search(value):
        return value
    REDACTIONS.extend(EMAIL_RE.findall(value))
    return EMAIL_RE.sub(EMAIL_PLACEHOLDER, value)


def scrub_emails_deep(node):
    """Final safety net over the fully assembled output: walks every string
    in the structure, so a column added to the sheet later cannot ship an
    address just because this script does not name it explicitly."""
    if isinstance(node, dict):
        return {scrub_emails_deep(k): scrub_emails_deep(v) for k, v in node.items()}
    if isinstance(node, list):
        return [scrub_emails_deep(v) for v in node]
    return redact_emails(node)


def normalize_date(raw):
    """Returns an ISO yyyy-mm-dd string, or the original string if it
    doesn't match either format seen in the source sheet (kept rather than
    dropped, so a future format change surfaces instead of vanishing)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if DATE_ISO.match(raw):
        return raw
    m = DATE_MDY.match(raw)
    if m:
        month, day, year = m.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return raw


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "app"


def make_unique_id(name, vendor, seen):
    base = slugify(f"{name}-{vendor}")
    slug = base
    n = 2
    while slug in seen:
        slug = f"{base}-{n}"
        n += 1
    seen.add(slug)
    return slug


def clean(v):
    v = (v or "").strip()
    return v if v else None


def split_multi(v):
    v = (v or "").strip()
    if not v:
        return []
    return [part.strip() for part in v.split("|") if part.strip()]


def fetch_csv_text():
    print(f"Fetching Georgia Southern third-party app tracker: {SHEET_CSV_URL}")
    req = urllib.request.Request(SHEET_CSV_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    text = raw.decode("utf-8-sig", errors="replace")
    if text.lstrip().startswith("<!DOCTYPE") or text.lstrip().startswith("<html"):
        raise RuntimeError(
            "Got an HTML page back instead of CSV -- the sheet is not "
            "shared as \"Anyone with the link can view\". Fix sharing on "
            "the Google Sheet and re-run."
        )
    return text


def build_record(row, seen_ids):
    # Redacted before slugifying: otherwise an address in either cell is
    # baked into the record key itself, where the deep scrub cannot reach it
    # without renaming records between builds.
    name = redact_emails(row["Product / Service"].strip())
    vendor = redact_emails(row["Vendor Name"].strip())
    app_id = make_unique_id(name, vendor, seen_ids)

    status_history = split_multi(row["Status"])
    current_status = status_history[-1] if status_history else None
    rating = STATUS_TO_RATING.get(current_status, "unrated")

    return app_id, {
        "name": name,
        "vendor": vendor,
        "initialRequestDate": normalize_date(row["Initial Request Date"]),
        "statusRaw": clean(row["Status"]),
        "statusHistory": status_history,
        "rating": rating,
        "compliance": {
            "gdpr": clean(row["GDPR Compliant"]) or "Unknown",
            "ferpa": clean(row["FERPA Compliant"]) or "Unknown",
            "coppa": clean(row["COPPA Compliant"]) or "Unknown",
            "under13": clean(row["Approved for children under 13"]) or "Unknown",
            "accessibilityStatement": clean(row["Accessibility Statement"]) or "Unknown",
        },
        "security": {
            "hecvat": clean(row["HECVAT"]) or "Unknown",
            "soc2": clean(row["SOC 2 Type II"]) or "Unknown",
        },
        "policies": {
            "privacyPolicy": clean(row["Privacy Policy (verified)"]),
            "termsOfService": clean(row["Terms of Service (verified)"]),
            "accessibilityStatementUrl": clean(row["Accessibility Statement URL"]),
            "trustCenter": clean(row["Trust Center"]),
        },
        "dataClasses": split_multi(row["Data Class(es)"]),
        "verificationMethod": clean(row["Verification Method"]) or "NOT YET VERIFIED",
        "rubricScored": clean(row["Rubric Scored?"]),
        "sourceRecords": int(row["Source Records"]) if clean(row["Source Records"]) and row["Source Records"].strip().isdigit() else 1,
        "rubric": {
            "general": {"genq1": clean(row["GENQ1"]) or "Not yet scored"},
            "dataCollection": {
                "questions": [clean(row[f"DCQ{i}"]) or "Not yet scored" for i in range(1, 6)],
                "notes": clean(row["DATA COLLECTION — Notes"]),
            },
            "security": {
                "questions": [clean(row[f"SECQ{i}"]) or "Not yet scored" for i in range(1, 6)],
                "notes": clean(row["SECURITY — Notes"]),
            },
            "thirdPartyData": {
                "questions": [clean(row[f"SHRQ{i}"]) or "Not yet scored" for i in range(1, 6)],
                "notes": clean(row["THIRD PARTY DATA — Notes"]),
            },
            "advertising": {
                "questions": [clean(row[f"ADVQ{i}"]) or "Not yet scored" for i in range(1, 6)],
                "notes": clean(row["ADVERTISING — Notes"]),
            },
            "usgHandbook": {
                "questions": [clean(row[f"USGQ{i}"]) or "Not yet scored" for i in range(1, 14)],
                "notes": clean(row["USG IT HANDBOOK — Notes"]),
            },
        },
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CLIENT_OUT_DIR, exist_ok=True)

    try:
        csv_text = fetch_csv_text()
    except Exception as e:
        print(f"ERROR: could not fetch the sheet -- {e}", file=sys.stderr)
        sys.exit(1)

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    print(f"Fetched {len(rows):,} rows from the sheet")

    apps = {}
    seen_ids = set()
    rating_counts = {}
    for row in rows:
        app_id, record = build_record(row, seen_ids)
        apps[app_id] = record
        rating_counts[record["rating"]] = rating_counts.get(record["rating"], 0) + 1

    apps = scrub_emails_deep(apps)

    print(f"Parsed {len(apps):,} app records")
    if REDACTIONS:
        unique = sorted(set(REDACTIONS))
        print(f"Email scan: REDACTED {len(REDACTIONS)} address(es) "
              f"({len(unique)} unique) that leaked into free-text columns:")
        for addr in unique:
            local, _, domain = addr.partition("@")
            print(f"  {local[:2]}***@{domain}")
    else:
        print("Email scan: clean -- no addresses in any output field")
    print("Derived rating breakdown:")
    for rating, count in sorted(rating_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {rating}: {count:,}")

    meta = {
        "builtAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "sourceUrl": SHEET_CSV_URL,
        "totalApps": len(apps),
        "ratingCounts": rating_counts,
    }

    for out_dir in (OUT_DIR, CLIENT_OUT_DIR):
        apps_path = os.path.join(out_dir, "apps.json")
        with open(apps_path, "w", encoding="utf-8") as f:
            json.dump(apps, f, separators=(",", ":"), sort_keys=True)
        apps_size_kb = os.path.getsize(apps_path) / 1024
        print(f"Wrote {len(apps):,} app records to {apps_path} ({apps_size_kb:.0f} KB)")

        meta_path = os.path.join(out_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, sort_keys=True)
        print(f"Wrote metadata to {meta_path}")


if __name__ == "__main__":
    main()
