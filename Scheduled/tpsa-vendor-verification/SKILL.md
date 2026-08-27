---
name: tpsa-vendor-verification
description: Verify privacy policy, ToS and SOC 2 posture for Georgia Southern's remaining unverified vendors
---

You are continuing a third-party security assessment project for Nic Carroll (ncarroll@georgiasouthern.edu), Executive Director of Technology at Georgia Southern University. Each run starts fresh — everything you need is below.

## Status as of 2026-08-14
1,330 unique vendors total. 916 verified. **414 still unverified.** Work through them, Class 1 first, until none remain.

## Where things live
Google Drive folder: https://drive.google.com/drive/folders/12UxJ9nKQ4ylOISizLZwpxrqi2w72Xa7G
Vendor population, six sheets titled "02 Vendor Master — Vetting Rubric (Part N of 6)":
- Part 1: 1l2SoddPb-nXY-ITx8JOUC9JHeayu_vXRsvbSUyNO6s0
- Part 2: 1ZYWHI8917EXY2iL9yyMbJfejzRin5Q36lwjQojmu4DM
- Part 3: 17w0N77HvPCVXpdVXV4gBfGiwqONpRD0g2A97gmUkCnE
- Part 4: 1vXimBMaDmINHZEBEMXtQSZmXbSi9gioqV-TX9MGofP8
- Part 5: 14UiWPZCXe1oepRW305j8jIvN9BfCPjLQkFgoe4UMKNk
- Part 6: 1MzYOGFDH7B7S0ij_CCXIj63GKXYYrraTdYyKyrX3la0
Completed work lives in "Vendor Verification Results — YYYY-MM-DD" sheets, including one dated 2026-08-14 covering 200 vendors (ID 1rkuR1EfDBQVPBy39Iv4CGyajVI2y9j82IgSUAgIcros). READ ALL OF THESE FIRST and skip vendors already done.

Load tools with ToolSearch: "select:mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__read_file_content,mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__search_files,mcp__b0bacdf9-20b1-4845-b8b1-914a3adc160c__create_file,WebSearch"

## What to do
1. Read the vendor sheets and all prior results sheets. Build the list of vendors whose Verification Method is "NOT YET VERIFIED" and that no results sheet covers.
2. Process as many as budget allows — 80-150 per run is realistic. Prioritise Class 1, then Class 2, then the rest.
3. Per vendor determine: official_website; privacy_policy_url; tos_url; soc2_status (one of "SOC 2 Type II", "SOC 2 Type I", "SOC 2 (type unspecified)", "No SOC 2 - ISO 27001 only", "No SOC 2 - other attestation", "None found", "N/A - open source / no hosted service", "Unknown"); soc2_evidence (name the source); trust_center_url; other_certifications (ISO 27001/27017/27018/27701, FedRAMP, StateRAMP, TX-RAMP, PCI DSS, HIPAA/BAA, GDPR/DPF, FERPA); us_data_residency (Yes/No/Mixed/Unknown plus HQ country if non-US); ai_llm_tool (Yes/No); verification_method ("SEARCH-CONFIRMED" if you saw the URL as a titled result on the vendor's own domain, "FETCH-CONFIRMED" if you opened it, "NOT FOUND" otherwise).

## Efficiency
One WebSearch per vendor: `"VendorName" privacy policy terms of service SOC 2`. A vendor-domain URL appearing as a titled search result counts as SEARCH-CONFIRMED — do not fetch to confirm. Web search quota is shared and limited; getting through the list matters more than perfecting any one vendor.

## Honesty rules — these outrank completeness
- NEVER construct a URL from a domain pattern. Blank + NOT FOUND instead.
- NEVER mark SOC 2 present without naming a specific source.
- Open-source projects, freeware, hardware-only vendors and defunct products are legitimately "N/A - open source / no hosted service".
- If a vendor cannot be identified at all, note "UNIDENTIFIED".
- Watch for vendor names that are actually salespeople, and for near-miss namesakes — do not credit one company's SOC 2 to a similarly named one.

## Output
You CANNOT edit existing Google Sheets — the Drive connector creates files but cannot rewrite their contents. Create a NEW Google Sheet in the folder (parentId 12UxJ9nKQ4ylOISizLZwpxrqi2w72Xa7G) titled "Vendor Verification Results — <today's date>" via create_file with contentMimeType "text/csv" and the complete CSV as textContent. Do not set disableConversionToGoogleType. Split into "(Part N)" sheets if the CSV would exceed about 100 KB.

CSV header exactly:
vendor_name,official_website,privacy_policy_url,tos_url,soc2_status,soc2_evidence,trust_center_url,other_certifications,us_data_residency,ai_llm_tool,verification_method,notes

If every vendor has been verified, create nothing and report that the work is complete.

## Report back
Vendors verified this run, how many remain, counts for privacy policies confirmed / ToS confirmed / SOC 2 or equivalent found / nothing found, and the highest-risk discoveries — Class 1 data with no attestation, non-US storage, AI tools that train on customer data, vendors with no reachable contact.