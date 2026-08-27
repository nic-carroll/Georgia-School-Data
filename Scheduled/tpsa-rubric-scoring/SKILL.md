---
name: tpsa-rubric-scoring
description: Score Georgia Southern's verified third-party vendors against the 34-question vetting rubric, Class 1 first
---

You are continuing a third-party security assessment project for Nic Carroll (ncarroll@georgiasouthern.edu), Executive Director of Technology at Georgia Southern University. Each run starts fresh — everything you need is below.

## Status as of 2026-08-14
All 43 live-pipeline vendors are FULLY SCORED. Your job now is to extend rubric scoring to the wider vendor population, highest-sensitivity first.

## Goal
Score vendors against a 34-question privacy/security vetting rubric (1EdTech TrustEd Apps, extended with a USG IT Handbook rubric area). Prioritise Class 1 data vendors, then Class 2. Only score vendors that already have a confirmed privacy policy or ToS URL — if a vendor has never been verified, skip it; the other scheduled task handles verification.

## Where things live
Google Drive folder: https://drive.google.com/drive/folders/12UxJ9nKQ4ylOISizLZwpxrqi2w72Xa7G
- "08 Rubric Definitions — Questions and MEETS Expectations" — sheet ID 1Sl8KaJmjmGDtzfPa8ZUrkYZT71bRpWMw0r9MkE0ns4w — the 34 questions and their MEETS conditions. READ THIS FIRST.
- "02 Vendor Master — Vetting Rubric (Part 1..6 of 6)" — the vendor population, with Data Class and Verification Method columns.
- "01 Status Tracker MASTER — Vetting Rubric FULLY SCORED (2026-08-14)" — sheet ID 1uxWxopDmjmaiNjfIwKeztIrePq2f32nysOKKCEfGAdc — a worked example of a completed row.
- Any prior "Rubric Scoring Results — YYYY-MM-DD" sheets hold completed work. READ THESE FIRST and skip vendors already scored.

Load tools with ToolSearch: "select:mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__read_file_content,mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__search_files,mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__create_file,WebSearch"

## What to do
1. Read sheet 08 for the rubric. Read the vendor master parts and any prior results sheets.
2. Build the list of Class 1 then Class 2 vendors that have a confirmed policy URL and are not yet scored.
3. Score as many as your budget allows — 10-15 vendors is realistic. For each, READ its privacy policy, terms of service, and trust/security page. Budget 3-5 page reads per vendor.

## Scoring values — use exactly one
`Meets` | `Partially` | `Unmet` | `N/A` | `Unknown`
- `Unknown` when the documents do not address it. NEVER default to `Unmet`.
- USGQ6, USGQ7, USGQ8, USGQ13 are Georgia Southern internal controls — always `N/A`, note "GS internal control".
- Never record a URL you did not actually see.

Also capture: GDPR / FERPA / COPPA / Approved-under-13 / Accessibility Statement (Yes/No/Unknown), HECVAT (Received / Public HECVAT available / Requested - pending / Not available / Unknown), SOC 2 Type II (Yes / Type I only / Equivalent (ISO 27001 / trust center) / No / Unknown), and the real policy URLs.

Rollups per area: `Unmet` if any question is Unmet; else `Partially` if any is Partially or Unknown; else `Meets`; ignore N/A. CERTIFIED = `Meets` only if all five rollups are `Meets`.

NOTE ON CALIBRATION: DCQ5 (60-day-or-less retention) and USGQ1/USGQ2 (US-only processing and storage) knock out nearly every commercial vendor. This is expected. Score them honestly and let the area rollups carry the signal — do not soften a score to avoid an Unmet.

## Output
You CANNOT edit existing Google Sheets — the Drive connector creates files but cannot rewrite their contents. Create a NEW Google Sheet in the folder (parentId 12UxJ9nKQ4ylOISizLZwpxrqi2w72Xa7G) titled "Rubric Scoring Results — <today's date>", via create_file with contentMimeType "text/csv" and the complete CSV as textContent. Do not set disableConversionToGoogleType. Split into "(Part N)" sheets if the CSV would exceed about 100 KB.

CSV header exactly:
vendor_name,privacy_policy_url,tos_url,accessibility_statement_url,trust_center_url,GDPR,FERPA,COPPA,Under13Approved,AccessibilityStatement,HECVAT,SOC2TypeII,GENQ1,DCQ1,DCQ2,DCQ3,DCQ4,DCQ5,DC_notes,SECQ1,SECQ2,SECQ3,SECQ4,SECQ5,SEC_notes,SHRQ1,SHRQ2,SHRQ3,SHRQ4,SHRQ5,SHR_notes,ADVQ1,ADVQ2,ADVQ3,ADVQ4,ADVQ5,ADV_notes,USGQ1,USGQ2,USGQ3,USGQ4,USGQ5,USGQ6,USGQ7,USGQ8,USGQ9,USGQ10,USGQ11,USGQ12,USGQ13,USG_notes,ROLLUP_DATA_COLLECTION,ROLLUP_SECURITY,ROLLUP_THIRD_PARTY,ROLLUP_ADVERTISING,ROLLUP_USG,CERTIFIED,overall_notes

Notes under 200 characters. Quote fields containing commas.

## Report back
Vendors scored this run, how many remain in the Class 1/Class 2 queue, any vendor failing a hard USG requirement (USGQ1, USGQ2, USGQ4, USGQ9, USGQ10, USGQ11 marked Unmet), and any actively concerning terms — training on customer data by default, selling personal information, or non-US data storage.