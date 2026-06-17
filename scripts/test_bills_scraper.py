
import asyncio
import logging
from src.ingestion.bills_scraper import run_bills_ingestion

logging.basicConfig(level=logging.INFO)

async def test_bills():
    # Test 1 year of National Assembly bills
    await run_bills_ingestion(limit_years=1)

if __name__ == "__main__":
    asyncio.run(test_bills())
