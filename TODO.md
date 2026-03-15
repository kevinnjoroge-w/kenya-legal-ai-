# Kenya Law Extensive Scraping — Full Sitemap Coverage
## Goal: Feed model 1963 (Independence)-2024 data across all dockets.

## ✅ Phase 1: Legal Notices Scraper
- [x] `legal_notices_scraper.py` — sitemap crawl 2003–2024 + historical

## ✅ Phase 2: Full Sitemap Coverage (NEW)
- [x] `bills_scraper.py` — National Assembly + Senate Bills 2007–2024
- [x] `practice_notes_scraper.py` — Practice Notes/Directions 1961–2022
- [x] `tribunals_scraper.py` — 15 tribunal decision collections (full)
- [x] `hansard_scraper.py` — Parliament Hansard Archive (NA + Senate)
- [x] `county_legislation_scraper.py` — 9 counties × Acts + Bills + LNs
- [x] `treaties_scraper.py` — Kenya Treaties Database (Article 2(6))
- [x] `kenya_gazette_scraper.py` — Kenya Gazette Online Archive (1963+)
- [x] `repealed_statutes_scraper.py` — Historical Repealed Statutes
- [x] `elections_scraper.py` — Election Petitions 2013, 2017, 2022

## ✅ Phase 3: Integration
- [x] `mass_ingest.py` updated — 17-step full-coverage orchestrator

## Phase 4: Processing & Embedding
- [ ] Run `mass_ingest.py` (full run — ~100k+ docs expected)
- [ ] Monitor Qdrant indexing
- [ ] Test timeline queries ('post-independence land laws', etc.)

## Previously Existing (still active)
- [x] `kenya_law_scraper.py` — cases/gazettes (new.kenyalaw.org)
- [x] `bulk_judgment_scraper.py` — all courts 1963–2025
- [x] `bulk_gazette_scraper.py` — gazettes by year
- [x] `legislation_scraper.py` — Acts/Laws of Kenya DB
- [x] `eac_ingestor.py` — EAC treaties
- [x] `judiciary_scraper.py` — judiciary.go.ke docs
- [x] `laws_africa_client.py` — Laws.Africa API

**Est. Dataset: 100k–200k chunks (1963–2024 full timeline coverage)**
Updated: 2026-03-15
