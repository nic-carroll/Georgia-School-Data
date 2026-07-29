#!/usr/bin/env python3
"""
GOSA Socioeconomic vs. Achievement Regression Analysis

Computes real Ordinary Least Squares (OLS) linear regression between each
school's % Economically Disadvantaged (STUDENT_COUNT_ED / STUDENT_COUNT_ALL,
from the real Attendance dataset) and its Milestones (EOC/EOG) achievement
rate (% Met + Exceeded, "All Students" subgroup), for every Test Type x
Content Area x school year x Grade in KEEP_YEARS, across every real Georgia
school that has both figures on record -- not a hardcoded sample. EOG gets a
real per-grade dimension (03-08, from the *_by_GRADE files) in addition to
the "ALL" grades rollup; EOC stays "ALL" only (a course's real grade
breakdown is whichever grades happen to take it, not a standard cohort).

Also classifies each school as elementary/middle/high from its real
GRADES_SERVED_DESC (Attendance dataset) for chart color-coding: "High" if it
serves any of grades 09-12, else "Middle" if it serves any of 06-08, else
"Elementary". A combined school (e.g. K-12) is classified by the highest
band it serves, same convention GOSA/CCRPI commonly uses for banded schools.

Produces:
  1. server/data/gosa/regression/<test_type>_<content_area_slug>_<year>_<grade>.json
     Per Test Type x Content Area x Year x Grade ("ALL" or "03".."08"): every
     school with both an ED% and an achievement rate for that combo, plus the
     real OLS fit (slope, intercept, r, r-squared) over exactly those points.
     Copied to client/data/regression/ for the browser to fetch on demand.
  2. server/data/gosa/regression/_meta.json
     Which years/content areas/grades actually exist per test type (same
     rationale as build_milestones_dashboard_data.py's _meta.json). Copied
     alongside.

This intentionally replaces an earlier version of this script that used a
hardcoded 17-school sample with invented scores -- see git history if that's
ever needed for reference, but it should not be revived; it wasn't real data.
"""

import os
import csv
import json
import math
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "gosa"))
EOC_DIR = os.path.join(DATA_DIR, "milestones_eoc")
EOG_DIR = os.path.join(DATA_DIR, "milestones_eog")
ATTENDANCE_DIR = os.path.join(DATA_DIR, "attendance")
OUT_DIR = os.path.join(DATA_DIR, "regression")
CLIENT_OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "client", "data", "regression"))

SUPPRESSED_CODE = "TFS"

# Same 5 school years as build_milestones_dashboard_data.py, mapped to the
# one Attendance file that reports each (verified against LONG_SCHOOL_YEAR,
# not filename -- attendance file-naming eras are as inconsistent as the
# Milestones ones).
YEAR_TO_ATTENDANCE_FILE = {
    "2020-21": "Attendance_2021_Dec062021.csv",
    "2021-22": "Attendance_2022_Dec072022.csv",
    "2022-23": "Attendance_2022-23_2023-12-15_18_55_15.csv",
    "2023-24": "Attendance_2023-24_2025-06-17_15_16_08.csv",
    "2024-25": "Attendance_2024-25_2026-02-19_00_32_26.csv",
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


def classify_level(grades_served):
    grades = set(g.strip() for g in grades_served.split(","))
    if grades & {"09", "10", "11", "12"}:
        return "High"
    if grades & {"06", "07", "08"}:
        return "Middle"
    return "Elementary"


def load_school_info(year):
    """{(dist_cd, instn_num): {name, districtName, level, edPct}} for one year,
    School-level rows only (DETAIL_LVL_DESC == 'School')."""
    path = os.path.join(ATTENDANCE_DIR, YEAR_TO_ATTENDANCE_FILE[year])
    info = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("DETAIL_LVL_DESC") or "").strip() != "School":
                continue
            dist_cd = (row.get("SCHOOL_DSTRCT_CD") or "").strip()
            instn = (row.get("INSTN_NUMBER") or "").strip()
            if not dist_cd or not instn:
                continue
            all_cnt = parse_num(row.get("STUDENT_COUNT_ALL"))
            ed_cnt = parse_num(row.get("STUDENT_COUNT_ED"))
            if all_cnt is None or ed_cnt is None or all_cnt <= 0:
                continue
            info[(dist_cd, instn)] = {
                "name": (row.get("INSTN_NAME") or "").strip(),
                "districtName": (row.get("SCHOOL_DSTRCT_NM") or "").strip(),
                "level": classify_level(row.get("GRADES_SERVED_DESC") or ""),
                "edPct": round(ed_cnt / all_cnt * 100, 1),
            }
    return info


def source_files(test_type, by_grade):
    """by_grade=False: plain (all-grades) files. by_grade=True: the
    *_by_GRADE/*_By_Grad variants, which report the same underlying test
    results broken out by the student's actual grade (03-08) instead of
    rolled up. EOC has by-grade files too, but a course's grade breakdown
    reflects whichever grades happen to take that course, not a standard
    cohort like EOG's -- consistent with index.html's existing drilldown,
    only EOG gets a real per-grade dimension here; EOC stays "ALL" only."""
    d = EOC_DIR if test_type == "EOC" else EOG_DIR
    files = []
    for fn in sorted(os.listdir(d)):
        up = fn.upper()
        if not fn.endswith(".csv") or "LEXILE" in up or up.startswith("EOCT") or up.startswith("GAA2"):
            continue
        is_by_grade = "BY_GRADE" in up or "BY_GRAD" in up
        if is_by_grade != by_grade:
            continue
        if not up.startswith(test_type):
            continue
        files.append(os.path.join(d, fn))
    return files


def load_achievement(test_type, keep_years):
    """{year: {content_area: {grade: {(dist_cd, instn): met_pct}}}}, School-level
    only (INSTN_NUMBER != 'ALL'), "All Students" subgroup. grade is "ALL" for
    the all-grades rollup, or "03".."08" for EOG's real per-grade files."""
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    def consume(path, force_all_grade):
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                year = (row.get("LONG_SCHOOL_YEAR") or "").strip()
                if year not in keep_years:
                    continue
                if (row.get("SUBGROUP_NAME") or "").strip() != "All Students":
                    continue
                raw_grade = (row.get("ACDMC_LVL") or "").strip()
                if force_all_grade:
                    if raw_grade and raw_grade != "ALL GRADES":
                        continue  # a stray by-grade row inside a plain file -- skip, don't double count
                    grade = "ALL"
                else:
                    if not raw_grade or raw_grade == "ALL GRADES":
                        continue  # this is the by-grade file; a row without a real grade isn't useful here
                    grade = raw_grade
                dist_cd = (row.get("SCHOOL_DISTRCT_CD") or "").strip()
                instn = (row.get("INSTN_NUMBER") or "").strip()
                if not dist_cd or not instn or dist_cd == "ALL" or instn == "ALL":
                    continue  # school-level only -- state/district rollups aren't a "school"
                content_area = (row.get("TEST_CMPNT_TYP_NM") or "").strip()
                if not content_area:
                    continue
                l3p = parse_num(row.get("PROFICIENT_PCT"))
                l4p = parse_num(row.get("DISTINGUISHED_PCT"))
                if l3p is None or l4p is None:
                    continue
                out[year][content_area][grade][(dist_cd, instn)] = round(l3p + l4p, 1)

    for path in source_files(test_type, by_grade=False):
        consume(path, force_all_grade=True)
    if test_type == "EOG":
        for path in source_files(test_type, by_grade=True):
            consume(path, force_all_grade=False)

    return out


def ols(points):
    """points: list of (x, y). Returns slope, intercept, r, r_squared."""
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)
    sum_y2 = sum(p[1] ** 2 for p in points)

    denom_slope = n * sum_x2 - sum_x ** 2
    slope = (n * sum_xy - sum_x * sum_y) / denom_slope if denom_slope else 0
    intercept = (sum_y - slope * sum_x) / n

    denom_r = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
    r = (n * sum_xy - sum_x * sum_y) / denom_r if denom_r else 0
    return slope, intercept, r, r ** 2


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CLIENT_OUT_DIR, exist_ok=True)

    keep_years = set(YEAR_TO_ATTENDANCE_FILE.keys())

    print("Loading real per-school ED% and grade-span classification from Attendance data...")
    school_info_by_year = {yr: load_school_info(yr) for yr in keep_years}
    for yr, info in school_info_by_year.items():
        print(f"  {yr}: {len(info):,} schools with ED% on record")

    meta = {"EOC": {"years": [], "contentAreasByYear": {}, "gradesByContentAreaYear": {}},
            "EOG": {"years": [], "contentAreasByYear": {}, "gradesByContentAreaYear": {}}}
    combo_count = 0
    total_points = 0

    for test_type in ("EOC", "EOG"):
        print(f"\n=== {test_type} ===")
        achievement = load_achievement(test_type, keep_years)
        years_with_data = sorted(achievement.keys())
        meta[test_type]["years"] = years_with_data

        for year in years_with_data:
            content_areas = sorted(achievement[year].keys())
            meta[test_type]["contentAreasByYear"][year] = content_areas
            school_info = school_info_by_year[year]

            for content_area in content_areas:
                grades = sorted(achievement[year][content_area].keys())
                usable_grades = []
                slug = content_area.lower().replace(" ", "-").replace(":", "").replace("/", "-")

                for grade in grades:
                    points = []
                    for (dist_cd, instn), met_pct in achievement[year][content_area][grade].items():
                        info = school_info.get((dist_cd, instn))
                        if not info:
                            continue  # no real ED%/level for this school this year -- skip, don't guess
                        points.append({
                            "code": f"{dist_cd}-{instn}",
                            "name": info["name"],
                            "districtCode": dist_cd,
                            "districtName": info["districtName"],
                            "level": info["level"],
                            "x": info["edPct"],
                            "y": met_pct,
                        })

                    if len(points) < 5:
                        print(f"  {year} / {content_area} / grade {grade}: only {len(points)} schools with both figures -- skipped (too few for a regression)")
                        continue

                    slope, intercept, r, r_squared = ols([(p["x"], p["y"]) for p in points])
                    out_record = {
                        "testType": test_type,
                        "contentArea": content_area,
                        "year": year,
                        "grade": grade,
                        "ols": {
                            "slope": round(slope, 3),
                            "intercept": round(intercept, 2),
                            "r": round(r, 3),
                            "rSquared": round(r_squared, 3),
                            "n": len(points),
                            "equation": f"% Met+Exceeded = {round(intercept, 1)} + ({round(slope, 3)} × % Econ. Disadvantaged)",
                        },
                        "points": points,
                    }

                    fname = f"{test_type}_{slug}_{year}_{grade}.json"
                    for out_dir in (OUT_DIR, CLIENT_OUT_DIR):
                        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
                            json.dump(out_record, f, separators=(",", ":"))

                    usable_grades.append(grade)
                    combo_count += 1
                    total_points += len(points)
                    print(f"  {year} / {content_area} / grade {grade}: {len(points):,} schools, r={r:.3f}, r²={r_squared:.3f}")

                meta[test_type]["gradesByContentAreaYear"].setdefault(year, {})[content_area] = usable_grades

    meta["generatedAt"] = "generated-by-regression_analysis.py"
    for out_dir in (OUT_DIR, CLIENT_OUT_DIR):
        with open(os.path.join(out_dir, "_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, sort_keys=True)

    print(f"\n--- Summary ---")
    print(f"Combinations written: {combo_count}")
    print(f"Total (school x combo) data points: {total_points:,}")
    print(f"Output: {OUT_DIR}")
    print(f"Client copy: {CLIENT_OUT_DIR}")


if __name__ == "__main__":
    main()
