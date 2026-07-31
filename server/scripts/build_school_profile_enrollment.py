#!/usr/bin/env python3
"""
GOSA School Profile Enrollment & Demographics Builder

Parses real, per-school total enrollment and ethnicity/gender percentages for
the School Profile page (schoolprofile.html)'s 3-year demographics table
(mirrors the page's 3-year Milestones score chart). This data has never been
parsed before -- build_comprehensive_gosa_db.py never reads
server/data/gosa/enrollment/ at all, which is why georgia_comprehensive_db.json's
studentCount/*Pct fields are random.uniform()/random.randint() fabrications
(see CLAUDE.md). This script reads the real source CSVs instead.

Sources, for each of the 3 school years GOSA has published in the current
"Enrollment_by_Grade"/"Enrollment_by_Subgroup_Metrics" file-naming era
(2022-23, 2023-24, 2024-25 -- older years use a differently-named/shaped
"Enrollment_by_Subgroups_Programs" file and are intentionally not parsed here):
  - enrollment/Enrollment_by_Grade_<year>_*.csv: real ENROLLMENT_COUNT per
    school x grade x ENROLLMENT_PERIOD (the file has both a "Fall" and a
    "Spring" count per grade -- only Fall, GOSA's official enrollment
    snapshot, is summed across GRADE_LEVEL rows for a school's real total;
    including Spring too would double-count).
  - enrollment/Enrollment_by_Subgroup_Metrics_<year>_*.csv: real
    ENROLL_PCT_ASIAN/NATIVE/BLACK/HISPANIC/MULTIRACIAL/WHITE/MALE/FEMALE per
    school.

GOSA suppresses small-n cells as the literal string "TFS" (Too Few Students).
Suppressed percentages become null (never estimated). If any grade-level row
feeding a school's total enrollment was suppressed, the summed total is a
real but incomplete sum -- flagged via enrollmentPartial rather than presented
as exact, same suppression-honesty rule as the rest of this pipeline. GOSA
does not publish raw per-race/gender counts, only percentages -- the client
computes an approximate count (percentage x real total enrollment) for
display and labels it as an estimate; this script only ever writes real
published percentages and real total-enrollment sums, never a fabricated count.

Produces:
  server/data/gosa/enrollment_profile/enrollment_profile.json
  client/data/enrollment/enrollment_profile.json (same file, copied for the
    browser to fetch on demand)

Shape: {"<districtCode>-<instnNumber>": {"<year>": {totalEnrollment,
enrollmentPartial, pctAsian, pctNative, pctBlack, pctHispanic,
pctMultiracial, pctWhite, pctMale, pctFemale}, ...}, ...}
"""

import os
import csv
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "gosa"))
ENROLLMENT_DIR = os.path.join(DATA_DIR, "enrollment")
OUT_DIR = os.path.join(DATA_DIR, "enrollment_profile")
CLIENT_OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "client", "data", "enrollment"))

SUPPRESSED_CODE = "TFS"

# The 3 years available in the current file-naming era. Add a 4th entry here
# (and drop the oldest, to keep the table at 3 years) after a future
# check_gosa_updates.py run lands a newer year -- same convention as
# regression_analysis.py's YEAR_TO_ATTENDANCE_FILE.
YEAR_FILES = {
    "2022-23": {
        "grade": "Enrollment_by_Grade_2022-23_2023-12-15_18_54_53.csv",
        "subgroup": "Enrollment_by_Subgroup_Metrics_2022-23_2023-12-15_18_54_53.csv",
    },
    "2023-24": {
        "grade": "Enrollment_by_Grade_2023-24_2025-01-14_16_45_56.csv",
        "subgroup": "Enrollment_by_Subgroup_Metrics_2023-24_2025-02-26_10_34_25.csv",
    },
    "2024-25": {
        "grade": "Enrollment_by_Grade_2024-25_2026-02-19_00_31_56.csv",
        "subgroup": "Enrollment_by_Subgroup_Metrics_2024-25_2026-02-19_00_31_56.csv",
    },
}


def parse_num(v):
    if v is None:
        return None
    v = v.strip()
    if v == "" or v == SUPPRESSED_CODE:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_total_enrollment(grade_file):
    """{(dist_cd, instn): {"totalEnrollment": int, "enrollmentPartial": bool}}

    The file has BOTH a "Fall" and a "Spring" ENROLLMENT_PERIOD row per
    school x grade -- summing both would double the real total (caught via
    a real school: naive summing gave Greenbrier High School 3,868 students,
    exactly its 1,939 Fall + 1,929 Spring). Fall is GOSA's official
    October-count enrollment snapshot (the figure used for FTE/state
    funding and generally cited as "school enrollment"), so only Fall rows
    are summed; Spring rows are skipped entirely.
    """
    path = os.path.join(ENROLLMENT_DIR, grade_file)
    totals = {}
    partial = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("DETAIL_LVL_DESC") or "").strip() != "School":
                continue
            if (row.get("ENROLLMENT_PERIOD") or "").strip() != "Fall":
                continue
            dist_cd = (row.get("SCHOOL_DSTRCT_CD") or "").strip()
            instn = (row.get("INSTN_NUMBER") or "").strip()
            if not dist_cd or not instn:
                continue
            key = (dist_cd, instn)
            count = parse_num(row.get("ENROLLMENT_COUNT"))
            if count is None:
                partial[key] = True
                continue
            totals[key] = totals.get(key, 0) + count
            partial.setdefault(key, False)

    return {
        key: {"totalEnrollment": int(round(total)), "enrollmentPartial": partial.get(key, False)}
        for key, total in totals.items()
    }


def load_demographics(subgroup_file):
    """{(dist_cd, instn): {pctAsian, pctNative, pctBlack, pctHispanic,
    pctMultiracial, pctWhite, pctMale, pctFemale}}"""
    path = os.path.join(ENROLLMENT_DIR, subgroup_file)
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("DETAIL_LVL_DESC") or "").strip() != "School":
                continue
            dist_cd = (row.get("SCHOOL_DSTRCT_CD") or "").strip()
            instn = (row.get("INSTN_NUMBER") or "").strip()
            if not dist_cd or not instn:
                continue
            out[(dist_cd, instn)] = {
                "pctAsian": parse_num(row.get("ENROLL_PCT_ASIAN")),
                "pctNative": parse_num(row.get("ENROLL_PCT_NATIVE")),
                "pctBlack": parse_num(row.get("ENROLL_PCT_BLACK")),
                "pctHispanic": parse_num(row.get("ENROLL_PCT_HISPANIC")),
                "pctMultiracial": parse_num(row.get("ENROLL_PCT_MULTIRACIAL")),
                "pctWhite": parse_num(row.get("ENROLL_PCT_WHITE")),
                "pctMale": parse_num(row.get("ENROLL_PCT_MALE")),
                "pctFemale": parse_num(row.get("ENROLL_PCT_FEMALE")),
            }
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CLIENT_OUT_DIR, exist_ok=True)

    out = {}
    for year, files in sorted(YEAR_FILES.items()):
        print(f"Parsing real enrollment data for {year}...")
        print(f"  Grade-level file: {files['grade']}")
        totals = load_total_enrollment(files["grade"])
        print(f"  {len(totals):,} schools with a real total-enrollment sum ({sum(1 for v in totals.values() if v['enrollmentPartial']):,} partial due to suppressed grade rows)")

        print(f"  Subgroup-metrics file: {files['subgroup']}")
        demographics = load_demographics(files["subgroup"])
        print(f"  {len(demographics):,} schools with real ethnicity/gender percentages on record")

        all_keys = set(totals.keys()) | set(demographics.keys())
        for key in all_keys:
            dist_cd, instn = key
            record = {}
            record.update(totals.get(key, {"totalEnrollment": None, "enrollmentPartial": False}))
            record.update(demographics.get(key, {
                "pctAsian": None, "pctNative": None, "pctBlack": None, "pctHispanic": None,
                "pctMultiracial": None, "pctWhite": None, "pctMale": None, "pctFemale": None,
            }))
            out.setdefault(f"{dist_cd}-{instn}", {})[year] = record

    for out_dir in (OUT_DIR, CLIENT_OUT_DIR):
        out_path = os.path.join(out_dir, "enrollment_profile.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, separators=(",", ":"), sort_keys=True)
        size_kb = os.path.getsize(out_path) / 1024
        print(f"Wrote {len(out):,} school records ({len(YEAR_FILES)} years each) to {out_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
