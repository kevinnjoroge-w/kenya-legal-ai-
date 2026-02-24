"""
Kenya Legal AI — EAC & International Treaty Ingestor
=====================================================
Scrapes and downloads East African Community (EAC) treaties, protocols,
and African Union (AU) instruments ratified by Kenya.

Constitutional basis: Article 2(6) — "Any treaty or convention ratified
by Kenya shall form part of the law of Kenya under this Constitution."
"""

import logging
import os
from pathlib import Path
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class EACIngestor:
    """
    Ingestor for East African Community (EAC) and regional legal instruments.
    """

    # Primary sources for EAC treaties and protocols
    EAC_TREATY_URL = "https://www.eac.int/treaty"
    EAC_PROTOCOLS_URL = "https://www.eac.int/protocols"

    def __init__(self):
        self.settings = get_settings()
        self.raw_dir = Path(self.settings.raw_data_dir) / "treaties" / "eac"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_eac_treaties(self) -> List[Dict]:
        """
        Fetch the main EAC Treaty and related fundamental documents.
        """
        logger.info(f"Fetching EAC treaties from {self.EAC_TREATY_URL}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.EAC_TREATY_URL)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        # Look for PDF links to treaties
        # Note: Site structure may vary, usually documents are in <a> tags within a list
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if ".pdf" in href.lower() and ("treaty" in text.lower() or "establishment" in text.lower()):
                full_url = href if href.startswith('http') else f"https://www.eac.int{href}"
                filename = os.path.basename(full_url)
                
                # Download file
                download_path = self.raw_dir / filename
                if not download_path.exists():
                    logger.info(f"Downloading EAC Treaty document: {text}")
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        doc_resp = await client.get(full_url)
                        doc_resp.raise_for_status()
                        with open(download_path, 'wb') as f:
                            f.write(doc_resp.content)
                
                results.append({
                    "title": text or filename,
                    "url": full_url,
                    "local_path": str(download_path),
                    "document_type": "treaty",
                    "source": "EAC"
                })
                
        return results

    async def ingest_all(self) -> List[Dict]:
        """
        Run the full ingestion process for EAC and regional instruments.
        """
        logger.info("Starting EAC and Treaty ingestion...")
        all_docs = []
        
        try:
            treaties = await self.fetch_eac_treaties()
            all_docs.extend(treaties)
            logger.info(f"Successfully ingested {len(treaties)} EAC treaty documents.")
        except Exception as e:
            logger.error(f"Failed to ingest EAC treaties: {e}")
            
        return all_docs

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    ingestor = EACIngestor()
    asyncio.run(ingestor.ingest_all())
