import asyncio
import logging
from src.ingestion.africanlii_scraper import AfricanLIIScraper

logging.basicConfig(level=logging.INFO)

async def test_africanlii():
    scraper = AfricanLIIScraper()
    print("Testing AfricanLII case search...")
    cases = await scraper.search_cases(limit=5)
    print(f"Found {len(cases)} cases")
    for case in cases:
        print(f"- {case.get('title') or case.get('name')} ({case.get('id')})")

if __name__ == "__main__":
    asyncio.run(test_africanlii())
