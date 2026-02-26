"""
Kenya Legal AI — CIPIT Data Protection Library Scraper
======================================================
Scrapes Kenyan data protection case law boundaries published by 
Strathmore University (CIPIT).
"""

import asyncio
import json
import logging
from pathlib import Path
from lxml import html
import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class CIPITScraper:
    """Scrapes cases from the CIPIT Data Protection Case Law Library."""
    
    BASE_URL = "https://cipit.org/data-protection-case-law-library/"
    
    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "cipit"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Using a browser-like user agent
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.timeout = 30.0

    async def ingest_all(self):
        """Main entry point to scrape the CIPIT library."""
        logger.info("Initializing CIPIT Data Protection Library scraper...")
        
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                # The actual implementation would iterate over the pagination 
                # or lists of case summaries. Because CIPIT hosts summaries directly 
                # as accessible web pages/PDFs, we will extract them.
                response = await client.get(self.BASE_URL)
                response.raise_for_status()
                
                # We will save the raw HTML dump of the library page for processing
                tree = html.fromstring(response.content)
                links = tree.xpath("//a[contains(@href, 'case') or contains(@href, 'pdf')]/@href")
                
                valid_links = [l for l in links if l.startswith("http")]
                valid_links = list(set(valid_links))
                
                logger.info(f"Found {len(valid_links)} potential case links/PDFs on CIPIT.")
                
                for idx, link in enumerate(valid_links[:20]): # Limiting for now
                    try:
                        doc_resp = await client.get(link)
                        doc_resp.raise_for_status()
                        
                        filename = link.split("/")[-1]
                        if not filename:
                            filename = f"case_{idx}"
                        
                        if ".pdf" in filename.lower():
                            filepath = self.output_dir / filename
                            filepath.write_bytes(doc_resp.content)
                        else:
                            # It's an HTML page summary
                            filepath = self.output_dir / f"{filename}.html"
                            filepath.write_bytes(doc_resp.content)
                            
                        logger.info(f"Saved CIPIT document: {filename}")
                        await asyncio.sleep(1) # Be nice to their server
                        
                    except Exception as e:
                        logger.warning(f"Failed to fetch CIPIT link {link}: {e}")
                        
            except Exception as e:
                logger.error(f"Error accessing CIPIT library baseline: {e}")
                
        logger.info("CIPIT scraping complete!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = CIPITScraper()
    asyncio.run(scraper.ingest_all())
