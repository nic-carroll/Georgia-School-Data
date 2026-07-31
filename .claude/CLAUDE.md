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

# Real per-school enrollment totals + ethnicity/gender %, for schoolprofile.html's
# demographics table -- 3-year trend (2022-23/2023-24/2024-25, the current
# Enrollment_by_Grade/Enrollment_by_Subgroup_Metrics file-naming era), mirroring
# the page's 3-year Milestones score chart. Parses the enrollment/ category,
# which nothing else in the pipeline touches (see Architecture Quirks re:
# fabricated demographic fields elsewhere). Re-run after check_gosa_updates.py
# pulls a newer year and update YEAR_FILES at the top of the script (add the
# new year, drop the oldest to keep it at 3).
python3 server/scripts/build_school_profile_enrollment.py
# → server/data/gosa/enrollment_profile/enrollment_profile.json (gitignored, ~1.4MB)
# → client/data/enrollment/enrollment_profile.json (same file, copied for the browser to fetch on demand)
```

## Architecture Quirks — Read This First
- **The site is four static, single-file HTML pages, not an SPA**: `client/index.html` (the drilldown dashboard), `client/regression.html` (demographic/achievement regression modeling), `client/schoolprofile.html` (single-school profile: enrollment, ethnicity/gender, 3-year Milestones trend, peer comparison), and `client/slides.html` (Slide Deck Builder — see below), linked by a shared `.page-nav` tab bar in each file's `<header>`. None is a Vite/React SPA despite the React dependencies in `client/package.json` and the `client/src/brands/` directory — all four are served as plain static HTML via `python3 -m http.server`. The `src/` directory contains aspirational React scaffolding that is **not currently wired up** to any of them. `.page-nav`'s link list is hand-copy-pasted across all 4 files (same pattern as `switchTheme()`) — adding/removing/reordering a tab means editing all 4, there's no single source of truth for it.
- **`client/slides.html` (Slide Deck Builder) lets a user assemble a branded presentation deck out of frozen snapshots of the other three pages' real data**, present it full-screen in the browser (`Element.requestFullscreen()`), or export a real, editable `.pptx`. It duplicates each of the other three pages' selection funnels internally (`dd*`/`reg*`/`prof*`-prefixed ids and globals) rather than importing shared code, per this repo's established no-shared-JS-module convention — the tradeoff is that a future UX refinement to, say, `index.html`'s dropdown-narrowing logic does **not** automatically propagate to `slides.html`'s copy; keeping them in sync is a manual, deliberate follow-up, not automatic. Each slide is a **frozen snapshot** (`{id, type, data}`, deep-cloned at "Add to Deck" time) — this is the one deliberate exception to the rest of this app's "always show live/fresh data" philosophy: a deck must keep rendering identically even after `regression_analysis.py`/`build_milestones_dashboard_data.py` reruns and regenerates the underlying JSON, so slides never hold a live reference back into `DD_*`/`REG_*`/`PROF_*` funnel state. Decks persist in `localStorage` (`slideDeckBuilder.decks.v1`), with JSON export/import for portability — no backend involved.
- **`client/vendor/pptxgen.bundle.js` is a manually-downloaded, vendored copy of pptxgenjs 3.12.0's browser UMD bundle** (from `unpkg.com/pptxgenjs@3.12.0/dist/pptxgen.bundle.js`, ~478KB), loaded via a plain `<script>` tag in `slides.html`, exposing the global `PptxGenJS`. This is the **only** third-party JS dependency anywhere in `client/` — everything else is hand-written vanilla JS — because real `.pptx` generation has no pure-browser-API equivalent. It is deliberately **not** an npm package: it never appears in `client/package.json`, and there's no build step to resolve a bare `import 'pptxgenjs'` in a plain `<script>`-tag page. Most slide types export as native, editable PowerPoint text/table/chart shapes; the one exception is the regression scatter chart, which pptxgenjs has no good native chart type for (its scatter/line/bar charts share one X-axis across series, which doesn't fit an irregular cloud of up to ~2,500 independently-positioned, 3-categorically-colored points) — that one chart (not its stats table) is rasterized client-side (SVG → `<canvas>` → PNG) from the same SVG-building function the live preview uses, and embedded as a `slide.addImage()`.
- **`georgia_comprehensive_db.json`'s per-school demographic/outcome fields are FABRICATED — do not use them.** `ecoDisadvPct`, `gmasProficiency`, `gmasMath/Sci/Alg/Bio`, `gradRate`, `attendanceRate`, `fesrRating`, `ppeDollars`, `actComposite`, `apPassRate`, `teacherExpYears`, and the `*Pct` race/ethnicity breakdowns in `build_comprehensive_gosa_db.py` are generated with `random.uniform()` (a manufactured negative-correlation formula against a randomized `eco` value), not parsed from any real GOSA file — only district/school `code`/`name`/`grades` (from the real Attendance CSV) are real. This means `georgia_master_data.js`, which is a direct dump of that db, has always carried fake numbers in those fields; they're just not displayed anywhere in the UI today (verified). `regression.html`/`regression_analysis.py` and `schoolprofile.html`/`build_school_profile_enrollment.py` deliberately do NOT use this file for X/Y or demographic values — they recompute real ED%/achievement/enrollment straight from the Attendance, Milestones, and Enrollment CSVs instead. If a future feature wants a school's economic-disadvantage %, achievement rate, or enrollment/ethnicity/gender breakdown, pull it from the real source CSVs (like `regression_analysis.py` and `build_school_profile_enrollment.py` do), never from these fields. Fixing `build_comprehensive_gosa_db.py` itself (so the fake fields become real, or get removed) is still open — see Recurring Mistakes Ledger.
- **`schoolprofile.html`'s enrollment/ethnicity/gender data is real, parsed by `build_school_profile_enrollment.py` from `server/data/gosa/enrollment/Enrollment_by_Grade_*.csv` (real per-grade `ENROLLMENT_COUNT`, summed for a school's total) and `Enrollment_by_Subgroup_Metrics_*.csv` (real `ENROLL_PCT_ASIAN/NATIVE/BLACK/HISPANIC/MULTIRACIAL/WHITE/MALE/FEMALE`)** — the `enrollment/` category folder nothing else in the pipeline had ever parsed before this. Output is `client/data/enrollment/enrollment_profile.json`, keyed by school `code` then by year (`{"<code>": {"2022-23": {...}, "2023-24": {...}, "2024-25": {...}}}`) — the 3 years available in the current file-naming era, rendered as a 3-column table (one row per category) rather than a chart, since this is compared-across-years categorical data. A suppressed (`"TFS"`) percentage becomes `null`, never estimated; if any grade row feeding a school's total enrollment was suppressed, `enrollmentPartial: true` flags that year's sum as real-but-incomplete rather than presenting it as exact. GOSA publishes race/gender **percentages only, never raw counts** — the table's "~N (X%)" figures compute N client-side (real % × real total enrollment) purely for display; the pipeline output itself never stores a fabricated count, only the real percentage and the real total.
- **`schoolprofile.html`'s 3-year test-score chart and peer comparison (District/Statewide toggle + peer table) reuse `client/data/regression/<TestType>_<content-area-slug>_<year>_<grade>.json` directly — no new pipeline output for scores.** Those files (built by `regression_analysis.py` for `regression.html`) already contain every real school's % Met+Exceeded plus its `level` (Elementary/Middle/High) and `districtCode` per year, so fetching the same combo for up to 3 years gives both the selected school's own trend and every same-level peer's score in one payload. Course names change across years (e.g. "Algebra I" → "Algebra: Concepts and Connections" in 2023-24) — the chart deliberately does NOT try to map renamed courses across years; a year missing the exact content-area name just renders as "No data" for that bar.
- **No dropdown on `index.html` or `schoolprofile.html` ever offers a combination the current selection has zero real data for — this is derived from real `data/milestones/` chunk keys at runtime, not a separate precomputed "coverage" file.** On `index.html`, `ensureChunkLoaded()` fetches `data/milestones/<districtCode>__<testType>_<year>.json` as soon as District+TestType+Year are all known (earlier than before — it used to wait until all 7 selectors were filled), and `parseChunkCoverage()` derives real Content Area/Grade/Subgroup options straight from that chunk's own keys (`"<CONTENT_AREA>|<GRADE>|<SUBGROUP>|<ENTITY>"`); the School dropdown is re-filtered at each step via `refreshSchoolOptions()`, and a previously-selected school that becomes invalid after a stricter upstream change is cleared with a note rather than left stale. `STATE`-entity-only rows don't count as "this district has it" — only `DISTRICT` and real school entities do. On `schoolprofile.html`, `loadSchoolCoverage()` does the equivalent for a single selected school: it fetches every real milestones chunk for that school's district (≤10 files: 2 test types × 5 years) once per school selection, and records exactly which (testType, contentArea, grade) combos that school has a real **"All Students"** value for (scoped to that one subgroup since that's the only one `regression_analysis.py`'s output — and therefore this page's score chart — ever reads). This replaced an earlier, looser rule that only checked whether the school *served* a grade, not whether it *had a reported score* there.
- **`regression.html`'s "Highlight My District" control (7) is additive/visual-only, distinct from the existing "County/District" hard-filter dropdown (6).** Filtering (6) removes non-matching schools from the chart entirely; highlighting (7) draws an amber ring (`--highlight-district`, the categorical palette's 4th slot) around a chosen district's dots while every other school — statewide or whatever's currently filtered — stays visible, so "my county vs. everyone" can be compared directly. It composes with every other control (Level filter, School highlight, Percentile bands) since it only changes how matching points are drawn in `renderChart()`, never which points are included.
- **`georgia_master_data.js` (3.6 MB)** is loaded via a `<script>` tag and sets `window.GEORGIA_GOSA_MASTER`. The client reads districts/schools from this global. There is no API call to `/api/gosa/districts` at runtime — the Express API exists but the frontend doesn't depend on it.
- **Python scripts are the real data pipeline**, not Node.js. All CSV parsing, OLS regression, school extraction, and data bundling happens in `server/scripts/*.py` using only Python stdlib (no pip dependencies). Output JSONs land in `server/data/gosa/`.
- **Brand theming uses `data-brand` attribute on `<html>`**, not the React `BrandProvider`. The HTML file defines CSS custom properties inline under `:root[data-brand="columbia-county"]` and `:root[data-brand="georgia-southern"]`. A `<select>` calls `switchTheme()` to swap the attribute.
- **The real brand token set is `--brand-primary/secondary/accent/bg/surface/text-primary/text-secondary/border/font`** — nothing else. [styles.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/styles.md) and [branding.md](file:///Users/ncarroll/Claude/.claude/rules/frontend/branding.md) were rewritten 2026-07-28 to match this after drifting into documenting tokens (`--brand-primary-hover`, `--radius-lg`, `--brand-font-family`...) that were never actually added to `index.html`. If a future edit needs a token that doesn't exist yet, add it to **both** `:root[data-brand=...]` blocks and update those docs — don't invent a parallel naming scheme.
- **Repo now has a GitHub remote**: `https://github.com/nic-carroll/Georgia-School-Data`. Raw CSV/XLS/XLSX under `server/data/gosa/` (~1.6GB) are gitignored and stay local-only by design — only the compiled JSON databases, `manifest.json`, and `latest_update_report.json` are tracked. A cloud routine ("Weekly GOSA downloadable-data check") runs `check_gosa_updates.py` every Tuesday 16:00 UTC against a fresh clone and pushes those two JSON files back if anything new was found; it does **not** sync the raw data files to your machine — run `check_gosa_updates.py` locally (or `git pull` then rerun it) to actually fetch new files onto disk.
- **The Milestones drilldown (Test Type/Content Area/Grade/Subgroup/Year on the front page) is fetch-on-demand, not pre-bundled.** `index.html` calls `fetch('data/milestones/<districtCode>__<testType>_<year>.json')` per selection instead of loading one big blob — even scoped to 5 years the dataset is ~450MB (see below), too large to bundle like `georgia_master_data.js`. This still works with `python3 -m http.server` and no Express server (static file fetch, not an API call), so it doesn't violate "offline-first" in spirit — it just means `client/data/milestones/` must exist locally (run `build_milestones_dashboard_data.py`) or those selections will correctly show "no data available" rather than a fake chart. Content Area/Grade options are populated from `data/milestones/_meta.json`, not hardcoded — GA's Milestones course names actually changed over the years (e.g. "Algebra I" → "Algebra: Concepts and Connections" in 2023-24), so a hardcoded list would silently offer dead-end selections for older years.
- **Milestones data is scoped to the 5 most recent school years (2020-21 → 2024-25)**, not the full 10 years GOSA publishes (2014-15 →) — a deliberate product decision (`KEEP_YEARS` in `build_milestones_dashboard_data.py`) made to fit GitHub Pages' 1GB published-site limit once `client/data/milestones/` needed to be pushed for the live demo. The full 10-year pipeline logic still exists, just filtered; widen `KEEP_YEARS` if the size constraint ever goes away.
- **Live demo**: `client/` (including `client/data/milestones/`, `client/data/regression/`, `client/data/enrollment/`, and `client/vendor/pptxgen.bundle.js`) is pushed to GitHub and served via GitHub Pages at `https://nic-carroll.github.io/Georgia-School-Data/client/` (drilldown), `.../client/regression.html` (regression), `.../client/schoolprofile.html` (school profile), and `.../client/slides.html` (slide deck builder) — the URL includes `/client/` because Pages serves from the repo root and there's no build step that flattens it. `client/data/milestones/`, `client/data/regression/`, `client/data/enrollment/`, and `client/vendor/pptxgen.bundle.js` are the exceptions to the "raw/derived data stays local" pattern elsewhere in this file — they're committed specifically so Pages has something to serve. After any push, force a rebuild via `POST /repos/nic-carroll/Georgia-School-Data/pages/builds` (GitHub's legacy Pages builder does not reliably auto-trigger on push) and poll `GET .../pages/builds/latest` until `status: "built"` before assuming the live site reflects the new commit.
- **`regression.html`'s school-level classification (Elementary/Middle/High, used for scatter-plot color) is derived from the real `GRADES_SERVED_DESC` field** in the Attendance CSV, not a lookup table: "High" if the school serves any of grades 09-12, else "Middle" if it serves any of 06-08, else "Elementary" (`classify_level()` in `regression_analysis.py`). A combined school (e.g. K-12) is classified by the highest band it serves — a simplification, consistent with how GOSA/CCRPI commonly bands combined schools.
- **`regression.html`'s Grade Level, School Level, and County/District controls are hard filters (they remove non-matching dots), not highlights** — picking "High" hides every elementary/middle school outright, and picking a district shows only that district. The one exception is the School control: selecting a school (which cascades from a chosen district) draws it as a distinct red highlight *within* whatever's currently filtered, it doesn't filter down to just that one dot. The regression trend line and the "Regression Model Summary" stats table are always the full statewide fit for that Test Type/Content Area/Year/Grade — they never recompute for the filtered subset, so the filtered dots can be visually compared against a fixed state-level reference. Grade Level only has real options for EOG (03-08, from the `*_by_GRADE` files, computed independently per grade — not derived from the "ALL" rollup); EOC stays "ALL" only, same reasoning as `classify_level()`'s note above.
- **The "Show Top % by Relative Performance" control ranks by residual (actual − the statewide line's prediction), computed client-side in `renderChart()`, not precomputed by the pipeline.** It narrows WITHIN whatever District/Level/Grade already filtered (so District=X + Top 10% means the top 10% of X's own schools, not the statewide top decile) and draws a second, fainter dashed line parallel to the main trend line at that percentile's residual cutoff — the main trend line itself never moves. There's no "Bottom %" option (only "Top"), by explicit user direction.
- **`regression_analysis.py` output filenames include the grade**: `<test_type>_<content_area_slug>_<year>_<grade>.json` where grade is `ALL` or `03`-`08`. If you're constructing a fetch URL by hand, don't forget the trailing grade segment — `EOG_mathematics_2024-25.json` (no grade) doesn't exist, only `EOG_mathematics_2024-25_ALL.json`, `..._05.json`, etc.
- **GOSA suppresses small-n cells as the literal string `"TFS"`** (Too Few Students) — sometimes just the total `NUM_TESTED_CNT`, sometimes just one achievement level's count while still publishing that level's percent. The pipeline keeps every real value and only nulls out what's actually suppressed (see `build_milestones_dashboard_data.py` docstring) — never back-compute a suppressed count from other fields, that defeats the suppression.

## Do Not Refactor
- `client/index.html` — Do not split into React components. The user wants a single-file, zero-build dashboard.
- `server/scripts/*.py` — These use only Python stdlib intentionally. Do not add pip dependencies (pandas, requests, etc.).
- `client/georgia_master_data.js` — Auto-generated by `bundle_client_data.py`. Never hand-edit; re-run the bundler.
- `server/data/gosa/*.json`, `server/data/gosa/milestones_dashboard/*.json`, `server/data/gosa/regression/*.json`, and `server/data/gosa/enrollment_profile/*.json` — Auto-generated outputs. Never hand-edit.
- `client/vendor/pptxgen.bundle.js` — Manually vendored (not npm-installed; never add `pptxgenjs` to `client/package.json`'s dependencies, there's no build step to resolve it). To update its version, manually re-download the same unpkg URL with a new version pin and replace the file — don't invent a package-manager-driven update path.

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

## Choosing Chart Types for GOSA Data
Before adding any new chart, match the visualization to the actual shape of the data — don't default to a bar chart or a pie chart out of habit. Load the `dataviz` skill for palette/contrast/legend mechanics; use this list for which chart type fits which of this repo's real data shapes:
- **Two continuous variables, looking for a relationship** (e.g. % Econ. Disadvantaged vs. % Met+Exceeded) → scatter plot + regression line, per `regression.html`. Don't collapse this into a bar chart of averages — that hides the school-to-school spread the scatter is the whole point of showing.
- **A metric across school years** (e.g. `schoolprofile.html`'s 3-year Milestones trend) → line chart, not a bar per year — the trajectory (improving/declining) is the signal, not any single year's value in isolation.
- **A metric broken out by category** (subgroup, content area, ethnicity/gender in `schoolprofile.html`'s enrollment card) → grouped or stacked bar, not a pie/donut — GOSA breakdowns commonly have 5-8+ categories and pies stop being readable past ~4-5 slices.
- **Many entities compared at once** (235 districts, 2,301 schools) → a filterable/sortable table, like `index.html`'s drilldown, not a giant bar chart — past a couple dozen bars, a chart becomes unreadable and a table with search/sort serves district leaders better.
- **A single school's standing among peers** (`schoolprofile.html`'s peer comparison) → the school highlighted within the full scatter/table of its peers (as already done, red dot / highlighted row), not a separate isolated "gauge" widget — keeping it in the same visual as its peers is what makes the comparison legible.
- School-level color coding (Elementary/Middle/High) always uses the same 3 fixed hex values (`--level-elementary/middle/high` in `regression.html`) regardless of brand theme — chart data-identity colors are deliberately brand-independent, don't substitute `--brand-*` tokens for them.

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
    ├─ regression_analysis.py (real, Attendance ED% + Milestones achievement)
    │       ▼
    │  client/data/regression/*.json ── fetched on demand by client/regression.html
    │       and by client/schoolprofile.html (3-year score trend + peer comparison,
    │       reuses these files directly -- no separate pipeline output)
    │
    └─ build_school_profile_enrollment.py (real, Enrollment_by_Grade +
       Enrollment_by_Subgroup_Metrics CSVs, 3 years)
            ▼
       client/data/enrollment/enrollment_profile.json ── fetched on demand by
       client/schoolprofile.html (total enrollment + ethnicity/gender %)
```
Run `python3 server/scripts/check_gosa_updates.py` and check its printed "Coverage by category" output (or `server/data/gosa/latest_update_report.json`) before assuming a category's data is complete — some years are permanently unreachable (Cloudflare-blocked legacy URLs, tracked with a 30-day retry cooldown), which the report distinguishes from genuine gaps.
