
import asyncio
import logging
from src.ingestion.smart_http_client import get_http_client

async def test_client():
    logging.basicConfig(level=logging.INFO)
    client = get_http_client()
    
    # Test a few URLs
    urls = [
        "https://www.google.com",
        "https://new.kenyalaw.org/judgments/",
        "https://judiciary.go.ke/downloads/",
    ]
    
    for url in urls:
        print(f"Fetching {url}...")
        response = await client.fetch(url)
        if response:
            print(f"Success! Status: {response.status_code}, Length: {len(response.text)}")
        else:
            print(f"Failed to fetch {url}")

    stats = client.get_stats()
    print(f"Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(test_client())
