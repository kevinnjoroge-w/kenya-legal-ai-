"""
Kenya Legal AI — Law Society of Kenya (LSK) Scraper
===================================================
Scrapes and downloads public documents, guidelines, and reports from the
Law Society of Kenya (LSK) website.
"""

import logging
import os
import asyncio
from pathlib import Path
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class LSKScraper:
    """
    Scraper for Law Society of Kenya (LSK) documents and guidelines.
    """

    LSK_BASE_URL = "https://lsk.or.ke"
    LSK_DOWNLOADS_URL = "https://lsk.or.ke/downloads/"

    def __init__(self):
        self.settings = get_settings()
        self.raw_dir = Path(self.settings.raw_data_dir) / "lsk"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        # Limit concurrent downloads
        self.semaphore = asyncio.Semaphore(5)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch a page with retries"""
        response = await client.get(url)
        response.raise_for_status()
        return response.text

    async def download_file(self, client: httpx.AsyncClient, url: str, title: str) -> Dict:
        """Download a file with concurrency limit and retries"""
        filename = os.path.basename(url)
        # Handle cases where url might not have a clear filename
        if not filename or "?" in filename:
            # Fallback to a sanitized title
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            filename = f"{safe_title.replace(' ', '_')}.pdf"
            
        download_path = self.raw_dir / filename
        
        async with self.semaphore:
            if not download_path.exists():
                logger.info(f"Downloading LSK document: {title}")
                try:
                    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
                    async def _do_download():
                        doc_resp = await client.get(url)
                        doc_resp.raise_for_status()
                        with open(download_path, 'wb') as f:
                            f.write(doc_resp.content)
                    
                    await _do_download()
                except Exception as e:
                    logger.error(f"Failed to download {url}: {e}")
                    return None
            else:
                logger.debug(f"File already exists: {filename}")

        return {
            "title": title or filename,
            "url": url,
            "local_path": str(download_path),
            "document_type": "lsk_document",
            "source": "Law Society of Kenya"
        }

    async def scrape_downloads_page(self) -> List[Dict]:
        """
        Scrape the main downloads page for PDFs.
        """
        logger.info(f"Scraping LSK downloads from {self.LSK_DOWNLOADS_URL}")
        results = []
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            html = await self.fetch_page(client, self.LSK_DOWNLOADS_URL)
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all links to PDFs
            tasks = []
            
            # The structure from the previous view_content_chunk showed headers followed by 'View / Download' links.
            # We can find all links ending in .pdf
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                if ".pdf" in href.lower():
                    full_url = href if href.startswith('http') else f"{self.LSK_BASE_URL.rstrip('/')}/{href.lstrip('/')}"
                    
                    # Try to find a better title if the link text is just "View / Download"
                    title = text
                    if title.lower() in ("view / download", "download", "here"):
                        # Look at the previous heading or element
                        prev_elem = link.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong'])
                        if prev_elem:
                            title = prev_elem.get_text(strip=True)
                        else:
                            title = os.path.basename(full_url)
                            
                    tasks.append(self.download_file(client, full_url, title))
            
            # Wait for all downloads to finish
            downloaded = await asyncio.gather(*tasks)
            results.extend([doc for doc in downloaded if doc is not None])
            
        return results

    async def ingest_all(self) -> List[Dict]:
        """
        Run the full ingestion process for LSK documents.
        """
        logger.info("Starting LSK ingestion...")
        all_docs = []
        
        try:
            downloads = await self.scrape_downloads_page()
            all_docs.extend(downloads)
            logger.info(f"Successfully ingested {len(downloads)} LSK documents.")
        except Exception as e:
            logger.error(f"Failed to ingest LSK documents: {e}")
            
        return all_docs

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = LSKScraper()
    asyncio.run(scraper.ingest_all())
