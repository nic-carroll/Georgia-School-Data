# CLAUDE.md — Institutional Memory for GOSA Analytics Workspace

## Essential Commands
```bash
# Frontend dashboard (static HTML served via Python; no Vite build needed for current index.html)
python3 -m http.server 5173 --directory client       # → http://localhost:5173

# Backend Express API (GOSA districts/schools/multiyear endpoints)
cd server && node src/index.js                        # → http://localhost:5000

# Re-bundle all 235 GA districts & 2,301 schools into client-side JS
python3 server/scripts/bundle_client_data.py          # → client/georgia_master_data.js (3.6 MB)

# Re-parse GOSA CSVs into comprehensive JSON databases
python3 server/scripts/build_comprehensive_gosa_db.py # → server/data/gosa/georgia_comprehensive_db.json
python3 server/scripts/extract_georgia_schools.py     # → server/data/gosa/georgia_schools_master.json
python3 server/scripts/parse_gosa_multiyear.py        # → server/data/gosa/gosa_multiyear_database.json

# Check GOSA portal for new/updated dataset files (scrapes goews.georgia.gov)
python3 server/scripts/check_gosa_updates.py          # Updates manifest.json & latest_update_report.json

# Regression analysis (OLS: real % Econ. Disadvantaged, from Attendance data, →
# real Milestones % Met+Exceeded), per Test Type x Content Area x school year x
# Grade (EOG only; EOC is "ALL" only), across every real GA school with both
# figures on record. Powers regression.html.
python3 server/scripts/regression_analysis.py
# → server/data/gosa/regression/<TestType>_<content-area-slug>_<year>_<grade>.json (gitignored)
# → client/data/regression/ (same files, copied for the browser to fetch on demand, ~16MB)

# Build the Milestones (EOC/EOG) drilldown data behind the front page's live stats.
# Parses ~4.8M rows across 10 school years (2014-15 to 2024-25, skipping the
# COVID-cancelled 2019-20 year); takes 60-90s. Re-run after check_gosa_updates.py
# pulls a new year's EOC/EOG files.
python3 server/scripts/build_milestones_dashboard_data.py
# → server/data/gosa/milestones_dashboard/<district>__<TestType>_<year>.json (~450MB, gitignored, scoped to last 5 years)
# → client/data/milestones/ (same files, copied for the browser to fetch on demand)
# → both dirs also get a small _meta.json (real years/content-areas-per-year/grades/subgroups)
```

## Architecture Quirks — Read This First
- **The site is two static, single-file HTML pages, not an SPA**: `client/index.html` (the drilldown dashboard) and `client/regression.html` (demographic/achievement regression modeling), linked by a shared `.page-nav` tab bar in each file's `<header>`. Neither is a Vite/React SPA despite the React dependencies in `client/package.json` and the `client/src/brands/` directory — both are served as plain static HTML via `python3 -m http.server`. The `src/` directory contains aspirational React scaffolding that is **not currently wired up** to either page.
- **`georgia_comprehensive_db.json`'s per-school demographic/outcome fields are FABRICATED — do not use them.** `ecoDisadvPct`, `gmasProficiency`, `gmasMath/Sci/Alg/Bio`, `gradRate`, `attendanceRate`, `fesrRating`, `ppeDollars`, `actComposite`, `apPassRate`, `teacherExpYears`, and the `*Pct` race/ethnicity breakdowns in `build_comprehensive_gosa_db.py` are generated with `random.uniform()` (a manufactured negative-correlation formula against a randomized `eco` value), not parsed from any real GOSA file — only district/school `code`/`name`/`grades` (from the real Attendance CSV) are real. This means `georgia_master_data.js`, which is a direct dump of that db, has always carried fake numbers in those fields; they're just not displayed anywhere in the UI today (verified). `regression.html`/`regression_analysis.py` deliberately do NOT use this file for X/Y values — they recompute real ED%/achievement straight from the Attendance and Milestones CSVs instead. If a future feature wants a school's economic-disadvantage % or achievement rate, pull it from the real Milestones/Attendance data (like `regression_analysis.py` does), never from these fields. Fixing `build_comprehensive_gosa_db.py` itself (so the fake fields become real, or get removed) is still open — see Recurring Mistakes Ledger.
- **`georgia_master_data.js` (3.6 MB)** is loaded via a `<script>` tag and sets `window.GEORGIA_GOSA_MASTER`. The client reads districts/schools from this global. There is no API call to `/api/gosa/districts` at runtime — the Express API exists but the frontend doesn't depend on it.
- **Python scripts are the real data pipeline**, not Node.js. All CSV parsing, OLS regression, school extraction, and data bundling happens in `server/scripts/*.py` using only Python stdlib (no pip dependencies). Output JSONs land in `server/data/gosa/`.
- **Brand theming uses `data-brand` attribute on `<html>`**, not the React `BrandProvider`. The HTML file defines CSS custom properties inline under `:root[data-brand="columbia-county"]` and `:root[data-brand="georgia-southern"]`. A `<select>` calls `switchTheme()` to swap the attribute.
- **The real brand token set is `--brand-primary/secondary/accent/bg/surface/text-primary/text-secondary/border/font`** — nothing else. [styles.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/styles.md) and [branding.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/branding.md) were rewritten 2026-07-28 to match this after drifting into documenting tokens (`--brand-primary-hover`, `--radius-lg`, `--brand-font-family`...) that were never actually added to `index.html`. If a future edit needs a token that doesn't exist yet, add it to **both** `:root[data-brand=...]` blocks and update those docs — don't invent a parallel naming scheme.
- **Repo now has a GitHub remote**: `https://github.com/nic-carroll/Georgia-School-Data`. Raw CSV/XLS/XLSX under `server/data/gosa/` (~1.6GB) are gitignored and stay local-only by design — only the compiled JSON databases, `manifest.json`, and `latest_update_report.json` are tracked. A cloud routine ("Weekly GOSA downloadable-data check") runs `check_gosa_updates.py` every Tuesday 16:00 UTC against a fresh clone and pushes those two JSON files back if anything new was found; it does **not** sync the raw data files to your machine — run `check_gosa_updates.py` locally (or `git pull` then rerun it) to actually fetch new files onto disk.
- **The Milestones drilldown (Test Type/Content Area/Grade/Subgroup/Year on the front page) is fetch-on-demand, not pre-bundled.** `index.html` calls `fetch('data/milestones/<districtCode>__<testType>_<year>.json')` per selection instead of loading one big blob — even scoped to 5 years the dataset is ~450MB (see below), too large to bundle like `georgia_master_data.js`. This still works with `python3 -m http.server` and no Express server (static file fetch, not an API call), so it doesn't violate "offline-first" in spirit — it just means `client/data/milestones/` must exist locally (run `build_milestones_dashboard_data.py`) or those selections will correctly show "no data available" rather than a fake chart. Content Area/Grade options are populated from `data/milestones/_meta.json`, not hardcoded — GA's Milestones course names actually changed over the years (e.g. "Algebra I" → "Algebra: Concepts and Connections" in 2023-24), so a hardcoded list would silently offer dead-end selections for older years.
- **Milestones data is scoped to the 5 most recent school years (2020-21 → 2024-25)**, not the full 10 years GOSA publishes (2014-15 →) — a deliberate product decision (`KEEP_YEARS` in `build_milestones_dashboard_data.py`) made to fit GitHub Pages' 1GB published-site limit once `client/data/milestones/` needed to be pushed for the live demo. The full 10-year pipeline logic still exists, just filtered; widen `KEEP_YEARS` if the size constraint ever goes away.
- **Live demo**: `client/` (including `client/data/milestones/` and `client/data/regression/`) is pushed to GitHub and served via GitHub Pages at `https://nic-carroll.github.io/Georgia-School-Data/client/` (drilldown) and `.../client/regression.html` (regression) — the URL includes `/client/` because Pages serves from the repo root and there's no build step that flattens it. `client/data/milestones/` and `client/data/regression/` are the exceptions to the "raw/derived data stays local" pattern elsewhere in this file — they're committed specifically so Pages has something to serve. After any push, force a rebuild via `POST /repos/nic-carroll/Georgia-School-Data/pages/builds` (GitHub's legacy Pages builder does not reliably auto-trigger on push) and poll `GET .../pages/builds/latest` until `status: "built"` before assuming the live site reflects the new commit.
- **`regression.html`'s school-level classification (Elementary/Middle/High, used for scatter-plot color) is derived from the real `GRADES_SERVED_DESC` field** in the Attendance CSV, not a lookup table: "High" if the school serves any of grades 09-12, else "Middle" if it serves any of 06-08, else "Elementary" (`classify_level()` in `regression_analysis.py`). A combined school (e.g. K-12) is classified by the highest band it serves — a simplification, consistent with how GOSA/CCRPI commonly bands combined schools.
- **`regression.html`'s Grade Level, School Level, and County/District controls are hard filters (they remove non-matching dots), not highlights** — picking "High" hides every elementary/middle school outright, and picking a district shows only that district. The one exception is the School control: selecting a school (which cascades from a chosen district) draws it as a distinct red highlight *within* whatever's currently filtered, it doesn't filter down to just that one dot. The regression trend line and the "Regression Model Summary" stats table are always the full statewide fit for that Test Type/Content Area/Year/Grade — they never recompute for the filtered subset, so the filtered dots can be visually compared against a fixed state-level reference. Grade Level only has real options for EOG (03-08, from the `*_by_GRADE` files, computed independently per grade — not derived from the "ALL" rollup); EOC stays "ALL" only, same reasoning as `classify_level()`'s note above.
- **`regression_analysis.py` output filenames include the grade**: `<test_type>_<content_area_slug>_<year>_<grade>.json` where grade is `ALL` or `03`-`08`. If you're constructing a fetch URL by hand, don't forget the trailing grade segment — `EOG_mathematics_2024-25.json` (no grade) doesn't exist, only `EOG_mathematics_2024-25_ALL.json`, `..._05.json`, etc.
- **GOSA suppresses small-n cells as the literal string `"TFS"`** (Too Few Students) — sometimes just the total `NUM_TESTED_CNT`, sometimes just one achievement level's count while still publishing that level's percent. The pipeline keeps every real value and only nulls out what's actually suppressed (see `build_milestones_dashboard_data.py` docstring) — never back-compute a suppressed count from other fields, that defeats the suppression.

## Do Not Refactor
- `client/index.html` — Do not split into React components. The user wants a single-file, zero-build dashboard.
- `server/scripts/*.py` — These use only Python stdlib intentionally. Do not add pip dependencies (pandas, requests, etc.).
- `client/georgia_master_data.js` — Auto-generated by `bundle_client_data.py`. Never hand-edit; re-run the bundler.
- `server/data/gosa/*.json`, `server/data/gosa/milestones_dashboard/*.json`, and `server/data/gosa/regression/*.json` — Auto-generated outputs. Never hand-edit.

## Security & Compliance Constraints
- **K-12 student data**: All GOSA datasets are publicly available aggregate data (no PII). However, treat school-level metrics as sensitive in any export or sharing context.
- **No hardcoded secrets**: Any future API keys (Gemini, Firebase, etc.) must go in `.env` files, never in source.
- **GOSA scraper ethics**: `check_gosa_updates.py` uses a standard browser User-Agent and respectful timeouts. Do not increase request frequency or parallelize scraping.
- **Deeper security rules**: Read [security.md](file:///Users/ncarroll/Claude/.claude/rules/security.md) only when modifying backend API auth, CORS, or adding new endpoints.

## Recurring Mistakes Ledger
<!-- Add entries here as errors recur. Format: [DATE] WHAT WENT WRONG → FIX -->
- **Overwriting index.html entirely** instead of making targeted edits. The file is 500+ lines. Use `replace_file_content` or `multi_replace_file_content` with exact line ranges, never `write_to_file` with `Overwrite: true` unless intentionally rebuilding.
- **Assuming Vite/React is active.** The `client/package.json` has React deps but the live app is `index.html` loaded via Python HTTP server. Don't run `npm run dev` in `client/` expecting it to serve the dashboard.
- **Generating fake school data** when real data exists. All 235 districts and 2,301 schools are in `georgia_comprehensive_db.json` — but only their code/name/grades are real; see the `[2026-07-29]` entry below before trusting any other field in that file.
- **Creating duplicate data files.** Before creating any new JSON in `server/data/gosa/`, check if the data already exists in `georgia_comprehensive_db.json`, `georgia_schools_master.json`, or `gosa_multiyear_database.json`.
- **[2026-07-28] Bare substring matching in `categorize_filename()`** miscategorized 4 postsecondary-outcomes files into `act_scores/` because `'ACT' in filename.upper()` matched inside `"...Redacted.xlsx"`. Fixed by anchoring to `filename.startswith(...)` for short/common substrings (`ACT`, `SAT`). When adding new filename-based category rules, check whether the substring could appear inside an unrelated word before using a bare `in` check.
- **[2026-07-29] `build_comprehensive_gosa_db.py` fabricates per-school demographic/outcome data with `random.uniform()`** (see Architecture Quirks above) — discovered while building `regression.html`, which needed real per-school ED%/achievement and would have silently plotted fake correlations if it had used `georgia_master_data.js`'s existing fields instead of recomputing from the real Attendance/Milestones CSVs. This is the same mistake the "Generating fake school data" ledger entry below already warns about, just undetected in this one script since its output wasn't displayed anywhere yet. **Still unfixed**: `build_comprehensive_gosa_db.py` itself. Before building anything new against `georgia_comprehensive_db.json`/`georgia_master_data.js`, check whether the specific field you need is one of the fabricated ones listed in Architecture Quirks — if so, derive it fresh from the real category CSVs instead (Attendance for ED%/grade-span, Milestones for achievement, etc.), the way `regression_analysis.py` does.

## Engineering Principles
1. **Readability over cleverness.** This tool is for school district leaders, not engineers. Code comments explaining "why" are more valuable than clever abstractions.
2. **Audit trail for data.** Every Python script must print what it parsed, how many records, and where it wrote output. The `check_gosa_updates.py` manifest pattern is the model.
3. **Offline-first client.** The dashboard must work without a running Express server. All critical data is pre-bundled in `georgia_master_data.js`.
4. **One feature at a time.** Per user direction: keep the UI focused. Don't add tabs/views/sections/filler copy ("Welcome to the dashboard!", "Data coming soon") the user hasn't asked for.
5. **Match existing patterns, don't invent new ones.** New UI must reuse the real `--brand-*` tokens and existing classes (`.viz-card`, `.selector-card`, `.table-card`, etc. — see [styles.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/styles.md) "Real Component Classes") rather than introducing new hex codes, inline `style="..."` attributes, or a new class naming convention for something that already has one.

## Progressive Disclosure — Domain-Specific References
Read these files **only** when working on the specified domain:
- **Multi-brand theming or new organization**: Read [branding.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/branding.md) — contains exact hex codes for Columbia County (#00025D, #D9232E) and Georgia Southern (#001344, #B9832D).
- **CSS tokens, glassmorphism, micro-animations**: Read [styles.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/styles.md).
- **React component patterns** (if migrating to SPA): Read [react.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/react.md).
- **Backend API security, CORS, auth**: Read [security.md](file:///Users/ncarroll/Claude/.claude/rules/security.md).
- **Test harness setup**: Read [testing.md](file:///Users/ncarroll/Claude/.claude/rules/testing.md).

## Data Pipeline Topology
```
GOSA Portal (goews.georgia.gov)
    │ check_gosa_updates.py (scrape → categorize → CSVs; tracks manifest.json + latest_update_report.json)
    ▼
server/data/gosa/<category>/*.csv  (25 category folders, ~400 raw files, gitignored/local-only)
    │
    ├─ extract_georgia_schools.py ─┐
    ├─ build_comprehensive_gosa_db.py (district/school code+name+grades real;      │
    │                                  demographic/outcome fields FABRICATED,       │
    │                                  see Architecture Quirks — do not consume)     │
    ├─ parse_gosa_multiyear.py ─────┘
    │       ▼
    │  server/data/gosa/*.json (compiled databases — git-tracked)
    │       │ bundle_client_data.py
    │       ▼
    │  client/georgia_master_data.js (window.GEORGIA_GOSA_MASTER)
    │       │ <script src="georgia_master_data.js">
    │       ▼
    │  client/index.html + client/regression.html (district/school directory only)
    │
    ├─ build_milestones_dashboard_data.py (real, Attendance+Milestones CSVs)
    │       ▼
    │  client/data/milestones/*.json ── fetched on demand by client/index.html
    │
    └─ regression_analysis.py (real, Attendance ED% + Milestones achievement)
            ▼
       client/data/regression/*.json ── fetched on demand by client/regression.html
```
Run `python3 server/scripts/check_gosa_updates.py` and check its printed "Coverage by category" output (or `server/data/gosa/latest_update_report.json`) before assuming a category's data is complete — some years are permanently unreachable (Cloudflare-blocked legacy URLs, tracked with a 30-day retry cooldown), which the report distinguishes from genuine gaps.
