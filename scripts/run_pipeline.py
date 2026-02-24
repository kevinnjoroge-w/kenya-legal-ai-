"""
Kenya Legal AI — Data Pipeline Runner
=======================================
Orchestrates the full data pipeline:
1. Ingest data from Laws.Africa and Kenya Law
2. Process and chunk documents
3. Generate embeddings and index into Qdrant

Usage:
    python -m scripts.run_pipeline --step all
    python -m scripts.run_pipeline --step ingest
    python -m scripts.run_pipeline --step process
    python -m scripts.run_pipeline --step index
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.laws_africa_client import run_ingestion as ingest_laws_africa
from src.ingestion.kenya_law_scraper import run_case_scraping
from src.processing.document_processor import process_all_documents
from src.embedding.embedding_service import index_all_processed_documents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

BANNER = """
╔═══════════════════════════════════════════════════════╗
║           Kenya Legal AI — Data Pipeline              ║
║         Constitution • Acts • Judgments • More         ║
╚═══════════════════════════════════════════════════════╝
"""


async def step_ingest():
    """Step 1: Ingest raw data from sources."""
    logger.info("=" * 60)
    logger.info("STEP 1: DATA INGESTION")
    logger.info("=" * 60)

    # Ingest legislation from Laws.Africa
    logger.info("Ingesting legislation from Laws.Africa API...")
    try:
        await ingest_laws_africa()
    except Exception as e:
        logger.error(f"Laws.Africa ingestion failed: {e}")
        logger.error("Make sure LAWS_AFRICA_API_KEY is set in .env")

    # Scrape case law from Kenya Law
    logger.info("Scraping case law from Kenya Law...")
    try:
        await run_case_scraping(max_pages=3)
    except Exception as e:
        logger.error(f"Kenya Law scraping failed: {e}")


def step_process():
    """Step 2: Process and chunk raw documents."""
    logger.info("=" * 60)
    logger.info("STEP 2: DOCUMENT PROCESSING")
    logger.info("=" * 60)

    chunks = process_all_documents()
    logger.info(f"Processing complete. Total chunks: {len(chunks)}")


def step_index():
    """Step 3: Generate embeddings and index into vector DB."""
    logger.info("=" * 60)
    logger.info("STEP 3: EMBEDDING & INDEXING")
    logger.info("=" * 60)

    index_all_processed_documents()
    logger.info("Indexing complete!")


async def run_all():
    """Run the full pipeline."""
    await step_ingest()
    step_process()
    step_index()


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="Kenya Legal AI — Data Pipeline Runner"
    )
    parser.add_argument(
        "--step",
        choices=["all", "ingest", "process", "index"],
        default="all",
        help="Pipeline step to run (default: all)",
    )
    args = parser.parse_args()

    if args.step == "all":
        asyncio.run(run_all())
    elif args.step == "ingest":
        asyncio.run(step_ingest())
    elif args.step == "process":
        step_process()
    elif args.step == "index":
        step_index()

    logger.info("Pipeline finished!")


if __name__ == "__main__":
    main()
