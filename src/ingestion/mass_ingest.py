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

    # 1. Judiciary Ingestion
    logger.info("--- Starting Judiciary Ingestion ---")
    j_scraper = JudiciaryScraper()
    j_categories = ["hc-practice-directions", "cj-speeches", "speeches"]
    for cat in j_categories:
        docs = await j_scraper.scrape_category(cat)
        # Process top 10 from each category
        for doc in docs[:10]:
            await j_scraper.process_document(doc)

    # 1.5. EAC & International Treaties (Art 2(6) CoK)
    logger.info("--- Starting EAC and Treaty Ingestion ---")
    eac_ingestor = EACIngestor()
    try:
        await eac_ingestor.ingest_all()
    except Exception as e:
        logger.error(f"EAC ingestion failed: {e}")

    # 2. Kenya Law (Bulk Scrape: Judgments & Gazettes)
    logger.info("--- Starting Kenya Law Bulk Ingestion ---")
    kl_scraper = KenyaLawScraper()
    years = range(2024, 2027) # Focus on recent gazettes
    
    for year in years:
        logger.info(f"Processing year {year} gazettes")
        gazettes = await kl_scraper.scrape_gazettes(year=year)
        for g in gazettes[:20]: # Top 20 gazettes per year
            await kl_scraper.scrape_document_full(g)

    # 2.5. Mass Judgment Ingestion (New Bulk Scraper)
    from src.ingestion.bulk_judgment_scraper import BulkJudgmentScraper
    logger.info("--- Starting Mass Judgment Ingestion ---")
    bulk_scraper = BulkJudgmentScraper()
    # Starting a full-scale ingestion run (500 pages per category)
    # The checkpoint system allows this to be resumed in future runs.
    await bulk_scraper.run_bulk_scrape(limit_pages=500)

    # 2.6. Law Society of Kenya (LSK) Ingestion
    logger.info("--- Starting LSK Ingestion ---")
    lsk_scraper = LSKScraper()
    try:
        await lsk_scraper.ingest_all()
    except Exception as e:
        logger.error(f"LSK Ingestion failed: {e}")

    # 2.7. CIPIT Data Protection Case Law Ingestion
    logger.info("--- Starting CIPIT Ingestion ---")
    cipit_scraper = CIPITScraper()
    try:
        await cipit_scraper.ingest_all()
    except Exception as e:
        logger.error(f"CIPIT Ingestion failed: {e}")

    # 3. Laws.Africa Ingestion (bulk legislation)
    logger.info("--- Starting Laws.Africa Bulk Ingestion ---")
    # NOTE: la_client was already created above for the Constitution.
    try:
        # Fetch all metadata but only download top 50 works for context.
        # The Constitution is skipped here because it was already ingested in step 0.
        works = await la_client.fetch_all_kenya_legislation()
        skipped = 0
        for work in works[:50]:
            frbr_uri = work.get("frbr_uri", "")
            if frbr_uri == LawsAfricaClient.CONSTITUTION_FRBR_URI:
                skipped += 1
                continue  # already downloaded in step 0
            await la_client.download_work(frbr_uri)
        logger.info(f"Bulk Laws.Africa ingestion done. Skipped {skipped} already-ingested work(s).")
    except Exception as e:
        logger.error(f"Laws.Africa ingestion failed: {e}")

    # 4. Document Processing
    logger.info("--- Processing All Documents ---")
    process_all_documents()

    # 4. Indexing
    logger.info("--- Indexing New Content ---")
    processor = LegalDocumentProcessor()
    # We load the all_documents.jsonl that was just created
    from src.config.settings import get_settings
    from src.processing.document_processor import DocumentChunk
    import json
    from pathlib import Path

    settings = get_settings()
    processed_file = Path(settings.processed_data_dir) / "all_documents.jsonl"
    
    if processed_file.exists():
        chunks = []
        with open(processed_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                chunks.append(DocumentChunk(**data))
        
        logger.info(f"Loaded {len(chunks)} chunks for indexing.")
        embedding_service = EmbeddingService()
        embedding_service.index_chunks(chunks)
        logger.info("Indexing complete.")
    else:
        logger.warning("No processed documents found to index.")

if __name__ == "__main__":
    asyncio.run(run_mass_ingestion())
