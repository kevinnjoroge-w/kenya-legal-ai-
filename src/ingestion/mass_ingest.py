"""
Kenya Legal AI — Mass Ingest Orchestrator
==========================================
Coordinates scraping from multiple legal sources.
"""

import asyncio
import logging
from src.ingestion.kenya_law_scraper import KenyaLawScraper
from src.ingestion.judiciary_scraper import JudiciaryScraper
from src.ingestion.laws_africa_client import LawsAfricaClient
from src.ingestion.eac_ingestor import EACIngestor
from src.ingestion.lsk_scraper import LSKScraper
from src.ingestion.cipit_scraper import CIPITScraper
from src.processing.document_processor import process_all_documents
from src.embedding.embedding_service import EmbeddingService
from src.processing.document_processor import LegalDocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_mass_ingestion():
    # 0. Constitution of Kenya (always ingest first, highest priority)
    logger.info("--- Starting Constitution of Kenya Ingestion ---")
    la_client = LawsAfricaClient()
    try:
        await la_client.download_constitution()
    except Exception as e:
        logger.error(f"Constitution ingestion failed: {e}")

    # 1. Laws.Africa Ingestion (All Primary Legislation)
    logger.info("--- Starting Laws.Africa Full Statutory Ingestion ---")
    try:
        # Fetch all metadata
        works = await la_client.fetch_all_kenya_legislation()
        # Filter for primary legislation (Acts) to avoid downloading thousands of old Gazette PDFs initially
        acts = [w for w in works if w.get("kind") == "act" or "constitution" in w.get("frbr_uri", "")]
        
        logger.info(f"Identified {len(acts)} Acts of Parliament to download.")
        
        count = 0
        for work in acts:
            frbr_uri = work.get("frbr_uri", "")
            if not frbr_uri:
                continue
                
            # Check if already exists to save time/quota
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
                
        logger.info(f"Laws.Africa ingestion done. Downloaded {count} new works.")
    except Exception as e:
        logger.error(f"Laws.Africa ingestion failed: {e}")

    # 2. Judiciary Ingestion (Practice Directions & Administrative Orders)
    logger.info("--- Starting Judiciary Ingestion ---")
    j_scraper = JudiciaryScraper()
    j_categories = ["hc-practice-directions", "cj-speeches", "administrative-circulars"]
    for cat in j_categories:
        try:
            docs = await j_scraper.scrape_category(cat)
            for doc in docs[:10]: # Limit to top 10 most relevant
                await j_scraper.process_document(doc)
        except Exception as e:
            logger.warning(f"Judiciary category {cat} failed: {e}")

    # 3. LSK & CIPIT (Specialized cases)
    logger.info("--- Starting Secondary Ingestions (LSK/CIPIT) ---")
    for scraper_class in [LSKScraper, CIPITScraper]:
        try:
            s = scraper_class()
            await s.ingest_all()
        except Exception as e:
            logger.warning(f"{scraper_class.__name__} failed: {e}")

    # 4. KenyaLaw Bulk Scraping (with backoff & checkpoints)
    logger.info("--- Starting KenyaLaw Bulk Scraping ---")
    try:
        from src.ingestion.bulk_judgment_scraper import BulkJudgmentScraper
        bjs = BulkJudgmentScraper()
        await bjs.run_bulk_scrape() # Run full scrape, checkpointing handles resumption
        
        from src.ingestion.legislation_scraper import LegislationScraper
        ls = LegislationScraper()
        await ls.run_bulk_ingestion(limit=10)
        
        from src.ingestion.bulk_gazette_scraper import BulkGazetteScraper
        bgs = BulkGazetteScraper()
        await bgs.run_bulk_scrape(start_year=2024, end_year=2023)
    except Exception as e:
        logger.warning(f"KenyaLaw bulk scraping encountered an issue: {e}")
    # 4. Document Processing (Streaming to Disk)
    logger.info("--- Processing All Documents (Streaming) ---")
    process_all_documents()

    # 5. Indexing (Streaming to Vector DB)
    logger.info("--- Indexing New Content (Streaming to Qdrant) ---")
    from src.embedding.embedding_service import index_all_processed_documents
    index_all_processed_documents()

if __name__ == "__main__":
    asyncio.run(run_mass_ingestion())
