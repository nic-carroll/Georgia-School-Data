#!/usr/bin/env python3
"""
GOSA Downloadable Data Daily Update Checker & Ingestion Tool
Scrapes https://goews.georgia.gov/dashboards-data-report-card/downloadable-data
Tracks manifest in server/data/gosa/manifest.json
Downloads new and updated CSV/XLS data files and generates daily update reports.
"""

import os
import sys
import json
import re
import hashlib
import time
from datetime import datetime
import urllib.request
import urllib.parse
from html.parser import HTMLParser

GOSA_PAGE_URL = "https://goews.georgia.gov/dashboards-data-report-card/downloadable-data?utm_source=gosa.georgia.gov"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gosa"))
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")
REPORT_FILE = os.path.join(DATA_DIR, "latest_update_report.json")

# User Agent header for fetching
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

class GOSAPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href' and val:
                    # Check if link points to downloadable csv/xls/xlsx
                    val_lower = val.lower()
                    if any(ext in val_lower for ext in ['.csv', '.xls', '.xlsx']):
                        self.links.append(val)

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

RETRY_COOLDOWN_DAYS = 30

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                manifest.setdefault("blocked", {})
                return manifest
        except Exception as e:
            print(f"Warning: Failed to load manifest: {e}")
    return {"last_checked": None, "files": {}, "blocked": {}}

def save_manifest(manifest):
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def fetch_page_links():
    print(f"Fetching GOSA data page: {GOSA_PAGE_URL}")
    req = urllib.request.Request(GOSA_PAGE_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
            parser = GOSAPageParser()
            parser.feed(html)
            # Deduplicate links
            return list(dict.fromkeys(parser.links))
    except Exception as e:
        print(f"Error fetching GOSA page: {e}")
        return []

def categorize_filename(filename):
    fn = filename.upper()
    # Prefix-anchored so e.g. "...Enrolled_in_College..._Redacted.xlsx" doesn't
    # false-match 'ACT' inside 'REDACTED' and get filed under act_scores.
    if fn.startswith('ACT'):
        return 'act_scores'
    elif fn.startswith('SAT'):
        return 'sat_scores'
    elif fn.startswith('C11') or fn.startswith('C12') or 'POSTSECONDARY' in fn:
        return 'postsecondary_outcomes'
    elif 'AP_' in fn or 'ADVANCED' in fn:
        return 'ap_scores'
    elif 'ATTENDANCE' in fn:
        return 'attendance'
    elif 'CERTIFIED_PERSONNEL' in fn:
        return 'certified_personnel'
    elif 'DIRECT' in fn or 'CERTIFICATION' in fn:
        return 'direct_cert'
    elif 'DROPOUT' in fn:
        return 'dropout_rates'
    elif 'EDUCATOR' in fn or 'INEXPERIENCED' in fn or 'OUT_OF_FIELD' in fn:
        return 'educator_qualifications'
    elif 'FESR' in fn or 'PPE' in fn:
        return 'financial_efficiency'
    elif 'EOC' in fn:
        return 'milestones_eoc'
    elif 'EOG' in fn:
        return 'milestones_eog'
    elif 'CRCT' in fn:
        return 'crct'
    elif 'LEXILE' in fn:
        return 'lexile_scores'
    elif 'MOBILITY' in fn or 'CHURN' in fn:
        return 'mobility'
    elif 'GRADUATION_RATE' in fn:
        return 'graduation_rate'
    elif 'EGWA' in fn:
        return 'egwa'
    elif 'ELL' in fn or 'EL_EXIT' in fn:
        return 'ell'
    elif 'ENROLLMENT' in fn:
        return 'enrollment'
    elif 'GAA' in fn:
        return 'gaa'
    elif 'GHSWT' in fn:
        return 'ghswt'
    elif 'GHSGT' in fn:
        return 'ghsgt'
    elif 'HOPE' in fn:
        return 'hope_scholarship'
    elif 'HS_COMPLETER' in fn or 'HIGHSCHOOL_COMPLETERS' in fn:
        return 'hs_completers'
    elif 'RETAINED' in fn:
        return 'retention'
    elif 'REVENUES' in fn and 'EXPENDITURES' in fn:
        return 'revenue_expenditures'
    elif 'SALARIES' in fn:
        return 'salaries_benefits'
    else:
        return 'general'

def normalize_url(url):
    """Percent-encode raw spaces/unsafe characters in the path while leaving
    already-escaped sequences (%20, etc.) untouched, e.g. GOSA sometimes
    links to '.../7-12 Dropout Rate_2020_Dec112020.csv' with a literal space."""
    parsed = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(parsed.path, safe="/%:@")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, safe_path, parsed.query, parsed.fragment))

def download_file(url, category):
    url = normalize_url(url)
    cat_dir = os.path.join(DATA_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    filename = os.path.basename(urllib.parse.urlparse(url).path)
    if not filename:
        filename = f"dataset_{hashlib.md5(url.encode()).hexdigest()[:8]}.csv"

    filepath = os.path.join(cat_dir, filename)
    req = urllib.request.Request(url, headers=HEADERS)

    print(f"  Downloading: {url} -> {category}/{filename}")
    try:
        with urllib.request.urlopen(req, timeout=60) as response, open(filepath, 'wb') as out_file:
            content = response.read()
            out_file.write(content)
            
            md5_hash = hashlib.md5(content).hexdigest()
            file_size = len(content)
            return {
                "filename": filename,
                "filepath": filepath,
                "relative_path": f"{category}/{filename}",
                "size_bytes": file_size,
                "md5": md5_hash,
                "url": url,
                "downloaded_at": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"  Failed downloading {url}: {e}")
        return None

YEAR_RE = re.compile(r'(?<!\d)(?:19|20)\d{2}(?!\d)')
FY_YEAR_RE = re.compile(r'FY(\d{2})(?!\d)', re.IGNORECASE)

def extract_year(filename):
    """Best-effort data year: the earliest plausible year token in the filename.
    Filenames embed the data year first, followed by a later processing/export
    timestamp (e.g. 'Attendance_2011_MAR_23_2020.csv' -> 2011, not 2020).
    Some FESR/PPE files only carry a two-digit fiscal year (e.g. 'FY19')."""
    years = [int(m.group(0)) for m in YEAR_RE.finditer(filename)]
    if years:
        return min(years)
    fy_years = [2000 + int(m.group(1)) for m in FY_YEAR_RE.finditer(filename)]
    return min(fy_years) if fy_years else None

def build_coverage_report(manifest):
    """Per-category summary of which data years are on disk and which
    contiguous years are missing, so gaps are visible without manually
    diffing folders against the GOSA site."""
    by_category = {}
    for file_info in manifest["files"].values():
        category = file_info["relative_path"].split("/")[0]
        year = extract_year(file_info["filename"])
        if year:
            by_category.setdefault(category, set()).add(year)

    blocked_years_by_category = {}
    for info in manifest["blocked"].values():
        category = info.get("category")
        year = extract_year(info.get("filename", ""))
        if category and year:
            blocked_years_by_category.setdefault(category, set()).add(year)

    coverage = {}
    for category, years in sorted(by_category.items()):
        years_present = sorted(years)
        blocked_years = sorted(blocked_years_by_category.get(category, set()))
        full_range = range(years_present[0], years_present[-1] + 1)
        missing = [y for y in full_range if y not in years]
        coverage[category] = {
            "years_present": years_present,
            "missing_years_in_range": missing,
            "unreachable_years_blocked_by_source": blocked_years
        }
    return coverage

def check_for_updates():
    ensure_dirs()
    manifest = load_manifest()
    new_links = fetch_page_links()

    print(f"Found {len(new_links)} dataset download link(s) on GOSA page.")

    new_files = []
    refetched_files = []
    updated_files = []
    unchanged_count = 0
    skipped_blocked = 0
    still_blocked = []

    now = datetime.now()

    for url in new_links:
        filename = os.path.basename(urllib.parse.urlparse(url).path)
        category = categorize_filename(filename)

        # Existing successful download
        was_known_url = url in manifest["files"]
        file_info = manifest["files"].get(url)
        if file_info:
            filepath = os.path.join(DATA_DIR, file_info["relative_path"])
            if os.path.exists(filepath):
                unchanged_count += 1
                continue
            # Local copy missing (e.g. raw CSVs are gitignored and this is a
            # fresh clone) — refetch it, but don't report it as "new" below.

        # Respect cooldown on URLs already known to be blocked (e.g. Cloudflare
        # bot-challenge on legacy goews.georgia.gov/gosa.georgia.gov paths) so we
        # don't hammer the source daily with requests we know will fail.
        blocked_info = manifest["blocked"].get(url)
        if blocked_info:
            last_attempt = datetime.fromisoformat(blocked_info["last_attempt"])
            if (now - last_attempt).days < RETRY_COOLDOWN_DAYS:
                skipped_blocked += 1
                still_blocked.append(blocked_info)
                continue

        result = download_file(url, category)
        if result:
            manifest["files"][url] = result
            manifest["blocked"].pop(url, None)
            if was_known_url:
                refetched_files.append(result)
            else:
                new_files.append(result)
        else:
            attempts = blocked_info["attempts"] + 1 if blocked_info else 1
            blocked_entry = {
                "url": url,
                "filename": filename,
                "category": category,
                "first_failed": blocked_info["first_failed"] if blocked_info else now.isoformat(),
                "last_attempt": now.isoformat(),
                "attempts": attempts
            }
            manifest["blocked"][url] = blocked_entry
            still_blocked.append(blocked_entry)

    coverage = build_coverage_report(manifest)

    # Update manifest timestamp
    now_iso = now.isoformat()
    manifest["last_checked"] = now_iso
    save_manifest(manifest)

    # Save daily update report
    report = {
        "timestamp": now_iso,
        "total_tracked_files": len(manifest["files"]),
        "new_files_count": len(new_files),
        "refetched_files_count": len(refetched_files),
        "updated_files_count": len(updated_files),
        "unchanged_files_count": unchanged_count,
        "blocked_files_count": len(manifest["blocked"]),
        "skipped_blocked_this_run": skipped_blocked,
        "new_files": new_files,
        "refetched_files": refetched_files,
        "updated_files": updated_files,
        "blocked_files": sorted(still_blocked, key=lambda b: (b["category"], b["filename"])),
        "coverage_by_category": coverage
    }

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print("\n--- GOSA Update Summary ---")
    print(f"Last Checked: {now_iso}")
    print(f"Total Tracked Files: {len(manifest['files'])}")
    print(f"New Files Ingested: {len(new_files)}")
    print(f"Re-fetched (known URL, missing local copy): {len(refetched_files)}")
    print(f"Updated Files: {len(updated_files)}")
    print(f"Blocked/Unreachable Files: {len(manifest['blocked'])} ({skipped_blocked} skipped this run under cooldown)")
    print("\nCoverage by category:")
    for category, info in sorted(coverage.items()):
        gap_note = f", missing {info['missing_years_in_range']}" if info["missing_years_in_range"] else ""
        blocked_note = f", {len(info['unreachable_years_blocked_by_source'])} yr(s) blocked at source" if info["unreachable_years_blocked_by_source"] else ""
        print(f"  {category}: {info['years_present'][0]}-{info['years_present'][-1]}{gap_note}{blocked_note}")
    print(f"\nReport saved to: {REPORT_FILE}\n")

    return report

if __name__ == "__main__":
    check_for_updates()
