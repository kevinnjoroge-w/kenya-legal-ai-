
import asyncio
import logging
from src.ingestion.laws_africa_client import LawsAfricaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_la():
    client = LawsAfricaClient()
    logger.info(f"Using base URL: {client.base_url}")
    try:
        # Just try to list works, first page
        works = await client.list_works(page=1, page_size=5)
        logger.info(f"Successfully fetched {len(works.get('results', []))} works.")
        for work in works.get('results', []):
            logger.info(f" - {work.get('title')} ({work.get('frbr_uri')})")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_la())
