# CareerPilot AI — Automated Ingestion Architecture & Scope Plan

## 1. Executive Summary

Phase 6 introduces automated and structured opportunity ingestion into CareerPilot AI to ensure a steady, high-quality flow of internship and fresher job listings without manual data entry fatigue.

To maintain architectural integrity, reliable data quality, legal compliance, and operational resilience, the ingestion system is divided into clear milestones with strict boundary guarantees.

---

## 2. Ingestion Strategy & Architectural Scope Decisions

### Decision: BeautifulSoup-Based Website Scraping is Intentionally Deferred (Not Implemented)

**Status:** Deferred / Not Implemented in current project scope.

#### Core Rationale:
1. **Authorized API-Based Path (JSearch)**: Phase 6.1 successfully established an authorized, rate-limited, and schema-bounded API ingestion integration through RapidAPI JSearch.
2. **Authorized Structured Feeds (RSS/Atom)**: Phase 6.3 establishes approved RSS ingestion (e.g., We Work Remotely, RemoteOK, organization feeds), which deliver clean XML structures with declared schemas.
3. **Fragility of Ad-Hoc HTML Parsers**: Website scraping without authorized APIs relies on fragile CSS selectors and custom DOM structures that break whenever third-party websites redesign their layouts.
4. **Legal & Scraping-Permission Uncertainty**: Scraping arbitrary job boards poses terms-of-service compliance risks and potential IP blocking.
5. **No Heavy Headless Browsers**: Playwright and Selenium introduce immense memory footprints, slow execution, and complex container dependencies unsuitable for serverless/lightweight backend environments.
6. **Admin Fallback Uploads (Planned Phase 6.4)**: For job sources lacking direct APIs or RSS feeds, safe file-based fallback uploads (CSV/JSON) with admin validation provide a far more reliable alternative than brittle web scrapers.

#### Reconsideration Criteria:
BeautifulSoup or web-based scraping will only be reconsidered if:
- A specific job provider explicitly permits automated HTML crawling in their Terms of Service and `robots.txt`.
- There is a compelling technical need that cannot be satisfied via authorized APIs, RSS feeds, or structured fallback uploads.

---

## 3. Phase 6 Milestone Breakdown

| Sub-Phase | Focus | Key Deliverables | Status |
|-----------|-------|------------------|--------|
| **6.1** | Authorized API Ingestion | RapidAPI JSearch search-v2 integration, preview & import schemas, savepoint transactions, canonical skill matching, external ID sanitization. | **Complete** |
| **6.2** | Discovery, Matching & Apply Workflow | Admin publish safeguards, employment-type conflict gating, student discovery filters, safe external URL navigation, applicant matching data isolation. | **Complete** |
| **6.3** | Authorized RSS Ingestion | Structured RSS 2.0 & Atom feed parsing (stdlib XML), SSRF protection, shared normalization, cross-source deduplication, admin review dialogs. | **Complete** |
| **6.4** | Scheduled Refresh, Expiry & Fallback Uploads | Automated background synchronization, past-deadline auto-expiration, CSV/JSON bulk upload fallback for manual partnerships. | **Planned** |

> **Note on Phase 6 Completion:** Phase 6 is not considered complete until all remaining required capabilities across Phase 6.4 (Scheduled Refresh, Expiration & Fallback Uploads) are implemented, tested, and documented, or the documented scope decision has been formally approved.

---

## 4. Ingestion Invariants & Safeguards

1. **Strict Draft Status**: Every imported opportunity must be saved with `status="Draft"`. No external job is ever published silently to students.
2. **Publication Guards**:
   - Application URL must be a valid `http://` or `https://` link.
   - Classification conflicts (e.g. title says "Intern" but provider categorizes as "Full-Time") must be resolved before publishing as an Internship.
3. **Canonical Skill Mapping**: Extracted skill strings are normalized and mapped exclusively against the database's active `skills` catalog. Unmapped terms are preserved for admin review.
4. **Cross-Source Deduplication**: Deduplication checks both provider external IDs and cross-source indicators (e.g., matching application URLs or title/employer pairs) to prevent duplicate listings.
5. **Transactional Savepoints**: Batch imports use nested transactions (`db.begin_nested()`) so single-item conflicts never cause the entire import operation to abort.
6. **Network & SSRF Safety**: Outgoing feed requests enforce strict URL validation, timeout bounds, and private subnet / loopback IP blocking.
