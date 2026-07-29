#!/usr/bin/env python3
"""
Build Georgia Milestones (EOC/EOG) drilldown data for the front-end dashboard.

Parses EOC/EOG CSVs in server/data/gosa/{milestones_eoc,milestones_eog}/, scoped
to the 5 most recent school years (KEEP_YEARS below -- by product decision,
the front-end drilldown only needs 5 years, and the full 10-year set pushed
the client data close to GitHub Pages' 1GB published-site limit). The
pre-2015 EOCT files use a different three-level DOES_NOT_MEET/MEETS/EXCEEDS
scale and are excluded regardless of KEEP_YEARS. Produces:

  1. server/data/gosa/milestones_dashboard/<district_code>__<test_type>_<year>.json
     One small file per District x TestType x Year (not one big file per
     district -- a single district's full history across both test types
     came out to tens of MB, far more than a single-selection drilldown UI
     should fetch for one lookup). Keyed by "CONTENT_AREA|GRADE|SUBGROUP|ENTITY".
     Includes that year+test type's State-level rows too, for a benchmark.
     Copied to client/data/milestones/ for the browser to fetch on demand.

  2. server/data/gosa/milestones_dashboard/_meta.json
     Small global index: which years/content areas/grades actually exist per
     test type (curricula changed over the years -- e.g. "Algebra I" was
     replaced by "Algebra: Concepts and Connections" in 2023-24), so the
     front-end can only offer selections that have real data instead of
     guessing. Also copied to client/data/milestones/.

GOSA suppresses small-n cells with the literal string "TFS" (Too Few
Students) instead of a number. Those rows are kept but flagged
{"suppressed": true} rather than dropped, so the UI can say "tested, but
too few students to report" instead of looking identical to "not offered
here at all".
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "gosa"))
EOC_DIR = os.path.join(DATA_DIR, "milestones_eoc")
EOG_DIR = os.path.join(DATA_DIR, "milestones_eog")
OUT_DIR = os.path.join(DATA_DIR, "milestones_dashboard")
CLIENT_OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "client", "data", "milestones"))

SUPPRESSED_CODE = "TFS"

# 5 most recent school years (out of the 10 available, 2014-15 to 2024-25 --
# see git history for build_milestones_dashboard_data.py before this scoping
# if the full range is ever needed again). String comparison sorts these
# correctly since they're all "YYYY-YY".
KEEP_YEARS = {"2020-21", "2021-22", "2022-23", "2023-24", "2024-25"}


def source_files(test_type):
    """Milestones-era files only: plain (all-grades) + *_by_GRADE/*_By_Grad variants.
    Excludes LEXILE files (different metric), EOCT files (pre-Milestones, 3-level
    scale), and GAA2 files (Alternate Assessment, different achievement levels)."""
    d = EOC_DIR if test_type == "EOC" else EOG_DIR
    files = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".csv"):
            continue
        up = fn.upper()
        if "LEXILE" in up or up.startswith("EOCT") or up.startswith("GAA2"):
            continue
        if not up.startswith(test_type):
            continue
        files.append(os.path.join(d, fn))
    return files


def parse_num(v):
    if v is None:
        return None
    v = v.strip()
    if v == "" or v == SUPPRESSED_CODE:
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() else round(f, 1)
    except ValueError:
        return None


def process_test_type(test_type, chunks, meta):
    files = source_files(test_type)
    row_count = 0
    fully_available = 0   # n and all 4 level counts present
    partially_suppressed = 0  # n present, but >=1 level count is TFS (percents are still real -- GOSA never suppresses those independently)
    fully_suppressed = 0  # NUM_TESTED_CNT itself is TFS -- nothing usable
    skipped_bad_row = 0

    for path in files:
        fname = os.path.basename(path)
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1

                year = (row.get("LONG_SCHOOL_YEAR") or "").strip()
                if year not in KEEP_YEARS:
                    continue
                dist_cd = (row.get("SCHOOL_DISTRCT_CD") or "").strip()
                instn = (row.get("INSTN_NUMBER") or "").strip()
                subgroup = (row.get("SUBGROUP_NAME") or "").strip()
                content_area = (row.get("TEST_CMPNT_TYP_NM") or "").strip()
                grade = (row.get("ACDMC_LVL") or "").strip() or "ALL GRADES"
                grade = "ALL" if grade == "ALL GRADES" else grade

                if not (year and dist_cd and instn and subgroup and content_area):
                    skipped_bad_row += 1
                    continue

                n = parse_num(row.get("NUM_TESTED_CNT"))
                l1 = parse_num(row.get("BEGIN_CNT"))
                l2 = parse_num(row.get("DEVELOPING_CNT"))
                l3 = parse_num(row.get("PROFICIENT_CNT"))
                l4 = parse_num(row.get("DISTINGUISHED_CNT"))
                l1p = parse_num(row.get("BEGIN_PCT"))
                l2p = parse_num(row.get("DEVELOPING_PCT"))
                l3p = parse_num(row.get("PROFICIENT_PCT"))
                l4p = parse_num(row.get("DISTINGUISHED_PCT"))

                # GOSA suppresses NUM_TESTED_CNT itself (whole row unusable, typically
                # n<=4) independently from suppressing individual level *_CNT values
                # (typically 1-4 students at that one level, out of a larger reported
                # group). Percents are never independently suppressed -- when a level's
                # raw count is masked, its percent is still given. We keep whatever is
                # real rather than discarding the row, but never back-compute a masked
                # count from its percent (that would defeat the point of suppression).
                record = {"n": n, "l1": l1, "l2": l2, "l3": l3, "l4": l4,
                          "l1p": l1p, "l2p": l2p, "l3p": l3p, "l4p": l4p}
                if n is None:
                    fully_suppressed += 1
                elif None in (l1, l2, l3, l4):
                    partially_suppressed += 1
                else:
                    fully_available += 1

                # Track what actually exists so the front-end never offers a
                # dead-end selection.
                ty_meta = meta[test_type]
                ty_meta["years"].add(year)
                ty_meta.setdefault("contentAreasByYear", {}).setdefault(year, set()).add(content_area)
                if grade != "ALL":
                    ty_meta["grades"].add(grade)
                ty_meta["subgroups"].add(subgroup)

                record_key = f"{content_area}|{grade}|{subgroup}"

                if dist_cd == "ALL":
                    chunks[(test_type, year, "STATE")][f"{record_key}|STATE"] = record
                else:
                    entity = "DISTRICT" if instn == "ALL" else instn
                    chunks[(test_type, year, dist_cd)][f"{record_key}|{entity}"] = record

        print(f"  parsed {fname}: running totals so far -> rows={row_count:,} full={fully_available:,} partial={partially_suppressed:,} suppressed={fully_suppressed:,}")

    return row_count, fully_available, partially_suppressed, fully_suppressed, skipped_bad_row


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CLIENT_OUT_DIR, exist_ok=True)

    # (test_type, year, district_code_or_"STATE") -> { "content|grade|subgroup|entity": record }
    chunks = defaultdict(dict)
    meta = {
        "EOC": {"years": set(), "grades": set(), "subgroups": set(), "contentAreasByYear": {}},
        "EOG": {"years": set(), "grades": set(), "subgroups": set(), "contentAreasByYear": {}},
    }

    totals = {}
    for test_type in ("EOC", "EOG"):
        print(f"\n=== Processing {test_type} ===")
        totals[test_type] = process_test_type(test_type, chunks, meta)

    # Merge each (test_type, year)'s STATE chunk into every matching district
    # chunk, so the front-end gets a state benchmark without a second fetch.
    state_chunks = {(tt, yr): recs for (tt, yr, key), recs in chunks.items() if key == "STATE"}
    district_keys = [k for k in chunks if k[2] != "STATE"]

    print(f"\nWriting {len(district_keys)} district x year x test-type files to {OUT_DIR} ...")
    written = 0
    for test_type, year, dist_cd in district_keys:
        records = dict(chunks[(test_type, year, dist_cd)])
        records.update(state_chunks.get((test_type, year), {}))
        fname = f"{dist_cd}__{test_type}_{year}.json"
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(records, f, separators=(",", ":"))
        with open(os.path.join(CLIENT_OUT_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(records, f, separators=(",", ":"))
        written += 1

    # Serialize meta (sets -> sorted lists).
    meta_out = {}
    for test_type, m in meta.items():
        meta_out[test_type] = {
            "years": sorted(m["years"]),
            "grades": sorted(m["grades"]),
            "subgroups": sorted(m["subgroups"]),
            "contentAreasByYear": {yr: sorted(areas) for yr, areas in m["contentAreasByYear"].items()},
        }
    meta_out["generatedAt"] = datetime.now().isoformat()

    for out_dir in (OUT_DIR, CLIENT_OUT_DIR):
        with open(os.path.join(out_dir, "_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta_out, f, indent=2, sort_keys=True)

    print("\n--- Build Summary ---")
    for test_type, (rows, full, partial, suppressed, skipped) in totals.items():
        print(f"{test_type}: {rows:,} rows read | {full:,} fully reported | {partial:,} partially suppressed (some level TFS, percents kept) | {suppressed:,} fully suppressed (n itself TFS) | {skipped:,} skipped (missing key fields)")
    print(f"District x year x test-type files written: {written}")
    all_out_files = [fn for fn in os.listdir(OUT_DIR) if fn.endswith(".json")]
    total_bytes = sum(os.path.getsize(os.path.join(OUT_DIR, fn)) for fn in all_out_files)
    sizes = sorted((os.path.getsize(os.path.join(OUT_DIR, fn)) for fn in all_out_files if fn != "_meta.json"), reverse=True)
    print(f"Total output size: {total_bytes / 1_000_000:.1f} MB across {len(all_out_files)} files")
    print(f"Largest chunk: {sizes[0] / 1_000:.0f} KB | Median chunk: {sizes[len(sizes)//2] / 1_000:.0f} KB")
    print(f"Output: {OUT_DIR}")
    print(f"Client copy: {CLIENT_OUT_DIR}")


if __name__ == "__main__":
    main()
