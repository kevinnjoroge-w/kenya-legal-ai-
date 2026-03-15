"""
Kenya Legal AI — Mass Ingest Orchestrator
==========================================
Coordinates scraping from all legal sources.
Full sitemap coverage of kenyalaw.org + supplementary sources.
"""

import asyncio
import logging
from src.ingestion.kenya_law_scraper import KenyaLawScraper
from src.ingestion.judiciary_scraper import JudiciaryScraper
from src.ingestion.laws_africa_client import LawsAfricaClient
from src.ingestion.eac_ingestor import EACIngestor
from src.ingestion.lsk_scraper import LSKScraper
from src.ingestion.cipit_scraper import CIPITScraper

# New scrapers — full sitemap coverage
from src.ingestion.bills_scraper import run_bills_ingestion
from src.ingestion.practice_notes_scraper import run_practice_notes_ingestion
from src.ingestion.tribunals_scraper import run_tribunals_ingestion
from src.ingestion.hansard_scraper import run_hansard_ingestion
from src.ingestion.county_legislation_scraper import run_county_legislation_ingestion
from src.ingestion.treaties_scraper import run_treaties_ingestion
from src.ingestion.kenya_gazette_scraper import run_kenya_gazette_ingestion
from src.ingestion.repealed_statutes_scraper import run_repealed_statutes_ingestion
from src.ingestion.elections_scraper import run_elections_ingestion

from src.processing.document_processor import process_all_documents
from src.embedding.embedding_service import EmbeddingService
from src.processing.document_processor import LegalDocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_mass_ingestion():
    # ─────────────────────────────────────────────────────────────────
    # 0. Constitution of Kenya (highest priority — always first)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [0] Constitution of Kenya ===")
    la_client = LawsAfricaClient()
    try:
        await la_client.download_constitution()
    except Exception as e:
        logger.error(f"Constitution ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 1. Laws.Africa — All Primary Legislation (Acts)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [1] Laws.Africa Full Statutory Ingestion ===")
    try:
        works = await la_client.fetch_all_kenya_legislation()
        acts = [w for w in works if w.get("kind") == "act" or "constitution" in w.get("frbr_uri", "")]
        logger.info(f"Identified {len(acts)} Acts of Parliament to download.")
        count = 0
        for work in acts:
            frbr_uri = work.get("frbr_uri", "")
            if not frbr_uri:
                continue
            safe_name = frbr_uri.strip("/").replace("/", "_")
            if (la_client.raw_data_dir / safe_name / "content.html").exists():
                continue
            try:
                await la_client.download_work(frbr_uri)
                count += 1
                if count % 10 == 0:
                    logger.info(f"Downloaded {count}/{len(acts)} acts...")
            except Exception as e:
                logger.error(f"Failed to download {frbr_uri}: {e}")
        logger.info(f"Laws.Africa done. Downloaded {count} new works.")
    except Exception as e:
        logger.error(f"Laws.Africa ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 2. Repealed Statutes (historical — before current legislation)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [2] Repealed Statutes ===")
    try:
        await run_repealed_statutes_ingestion()
    except Exception as e:
        logger.error(f"Repealed Statutes ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 3. Parliamentary Bills (National Assembly + Senate, 2007–2024)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [3] Parliamentary Bills ===")
    try:
        await run_bills_ingestion()
    except Exception as e:
        logger.error(f"Bills ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 4. Legal Notices (2003–2024 + historical)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [4] Legal Notices ===")
    try:
        from src.ingestion.legal_notices_scraper import run_legal_notices_ingestion
        await run_legal_notices_ingestion()
    except Exception as e:
        logger.error(f"Legal Notices ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 5. Kenya Gazette Online Archive (historical, kenyalaw.org/kl)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [5] Kenya Gazette Archive ===")
    try:
        await run_kenya_gazette_ingestion()
    except Exception as e:
        logger.error(f"Kenya Gazette Archive ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 6. Bulk Judgments + New Portal Gazettes (new.kenyalaw.org)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [6] Bulk Judgments + Portal Gazettes ===")
    try:
        from src.ingestion.bulk_judgment_scraper import BulkJudgmentScraper
        bjs = BulkJudgmentScraper()
        await bjs.run_bulk_scrape()

        from src.ingestion.legislation_scraper import LegislationScraper
        ls = LegislationScraper()
        await ls.run_bulk_ingestion(limit=10)

        from src.ingestion.bulk_gazette_scraper import BulkGazetteScraper
        bgs = BulkGazetteScraper()
        await bgs.run_bulk_scrape(start_year=2024, end_year=1963)
    except Exception as e:
        logger.warning(f"KenyaLaw bulk scraping issue: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 7. Practice Notes & Directions (1961–2022)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [7] Practice Notes & Directions ===")
    try:
        await run_practice_notes_ingestion()
    except Exception as e:
        logger.error(f"Practice Notes ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 8. Tribunal Decisions (15 tribunals)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [8] Tribunal Decisions ===")
    try:
        await run_tribunals_ingestion()
    except Exception as e:
        logger.error(f"Tribunals ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 9. Hansard — Parliamentary Debates
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [9] Hansard Debates ===")
    try:
        await run_hansard_ingestion()
    except Exception as e:
        logger.error(f"Hansard ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 10. Treaties Database
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [10] Treaties Database ===")
    try:
        await run_treaties_ingestion()
    except Exception as e:
        logger.error(f"Treaties ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 11. County Legislation (9 counties × Acts + Bills + LNs)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [11] County Legislation ===")
    try:
        await run_county_legislation_ingestion()
    except Exception as e:
        logger.error(f"County Legislation ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 12. EAC Legislation (Acts, Legal Notices, Bills)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [12] EAC Legislation ===")
    try:
        eac = EACIngestor()
        await eac.ingest_all()
    except Exception as e:
        logger.warning(f"EAC ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 13. Judiciary (Practice Directions, Speeches)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [13] Judiciary Documents ===")
    j_scraper = JudiciaryScraper()
    j_categories = ["hc-practice-directions", "cj-speeches", "administrative-circulars"]
    for cat in j_categories:
        try:
            docs = await j_scraper.scrape_category(cat)
            for doc in docs[:10]:
                await j_scraper.process_document(doc)
        except Exception as e:
            logger.warning(f"Judiciary category {cat} failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 14. Election Petitions (2013, 2017, 2022)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [14] Election Petitions ===")
    try:
        await run_elections_ingestion()
    except Exception as e:
        logger.error(f"Elections ingestion failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 15. LSK & CIPIT (Specialized cases and IP law)
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [15] LSK & CIPIT ===")
    for scraper_class in [LSKScraper, CIPITScraper]:
        try:
            s = scraper_class()
            await s.ingest_all()
        except Exception as e:
            logger.warning(f"{scraper_class.__name__} failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # 16. Document Processing → Embedding → Indexing
    # ─────────────────────────────────────────────────────────────────
    logger.info("=== [16] Processing All Documents ===")
    process_all_documents()

    logger.info("=== [17] Indexing to Qdrant ===")
    from src.embedding.embedding_service import index_all_processed_documents
    index_all_processed_documents()

    logger.info("=== Mass ingestion COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(run_mass_ingestion())
