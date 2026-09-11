# Phase 2 - Official source and rights discovery

Observed from the current NHTSA Standing General Order page on 2026-09-11:

`https://www.nhtsa.gov/laws-regulations/standing-general-order-crash-reporting`

## Current source-of-truth files

The page currently links the third-amended-SGO ADS, Level 2 ADAS, Other/Unknown CSVs, a current Data Element Definitions & Log PDF, and an Archive section for data before June 16, 2025. The concrete links captured from that live page are recorded in `state/source_catalog.json`, and the static file URLs were independently checked from the project host before pilot download.

The page states that the 2025 amendment was issued April 24, 2025 and took effect June 16, 2025. Files from that release onward reflect the third-amended data fields; prior-version data belong in the archive. The current page observed on 2026-09-11 says the current CSVs cover data from June 16, 2025 through July 15, 2026. Local HTTP metadata showed the current ADS CSV and dictionary were last modified August 27, 2026, while the ADAS and Other CSVs were last modified August 17, 2026.

## Reporting regime and update semantics

The third amended order supersedes the April 5, 2023 second amended order effective June 16, 2025. NHTSA explains that the third amendment changes report timing and scope, reduces duplicate reporting obligations, removes scheduled no-new-information update requirements, and streamlines fields. NHTSA says incident CSVs are updated monthly.

The data page also states that each report has an NHTSA-generated **Report ID**; updates keep that Report ID and receive a new sequential **Report Version**. The page says its charts use values from the latest report when multiple versions exist. **Report Submission Date is the first submission month/year, not a revision timestamp**, so release logic must not use it as the latest-version selector.

NHTSA also supplies **Same Incident ID** and **Same Vehicle ID** to help users link reports/incidents, but warns that missing or incorrect source values can make those IDs unavailable, inaccurate, or different between versions. Therefore the release preserves these identifiers and never invents a crash-level merge key.

## Limitations that must travel with the dataset

- ADS and Level 2 ADAS have different reportability criteria.
- Reporting entities differ in telemetry, crash awareness, vehicle populations, operating locations, mileage, and other exposure factors.
- Initial reports can be incomplete or unverified and may later be updated.
- The same crash can still have multiple reports.
- The summary data are not normalized by vehicles, miles traveled, ODD exposure, or another denominator; raw manufacturer/operator counts are not crash rates and must not be presented as safety rankings.

## Public-data / redaction / redistribution gate

NHTSA explicitly states that the incident-report CSVs are publicly available. The public files include submitted incident information except material that is or may lead to disclosure of personally identifiable information and information claimed as confidential business information. NHTSA notes that the last six VIN characters are withheld, incident dates are reduced to month/year, and CBI/PII redactions are represented in the data.

This gives a strong basis to redistribute a derived, source-attributed table made solely from the files NHTSA intentionally publishes. However, because some narrative/content originates with reporting entities rather than being authored by the federal government, this project does **not** make a blanket CC0/public-domain claim. Kaggle metadata will use license `other` and describe the basis as redistribution of NHTSA's publicly released, already-redacted SGO CSV data with source attribution and limitations preserved.

**Rights gate: PASS for the NHTSA-published public CSV fields as released.** No unredacted, private, credential-gated, or separately scraped incident information may enter the release.
