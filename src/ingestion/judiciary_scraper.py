"""
Kenya Legal AI — Judiciary Scraper
====================================
Scrapes practice directions, administrative orders, and reports from judiciary.go.ke.
Handles WordPress Download Manager (WPDM) based document retrieval.
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://judiciary.go.ke"
DOWNLOADS_URL = f"{BASE_URL}/downloads/"

@dataclass
class JudiciaryDocument:
    """Metadata for a judiciary document."""
    title: str
    category: str
    date: str
    url: str
    download_url: Optional[str] = None
    source_file: Optional[str] = None

class JudiciaryScraper:
    """Scraper for judiciary.go.ke resources."""

    def __init__(self):
        settings = get_settings()
        self.raw_data_dir = Path(settings.raw_data_dir) / "judiciary"
        self.docs_dir = self.raw_data_dir / "documents"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = Path(settings.metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _fetch_page(self, url: str) -> str:
        """Fetch a page with retry logic."""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def scrape_category(self, category_slug: str, max_pages: int = 5) -> List[JudiciaryDocument]:
        """Scrape documents from a specific category."""
        url = f"{BASE_URL}/download-category/{category_slug}/"
        logger.info(f"Scraping judiciary category: {category_slug}")
        
        documents = []
        try:
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "lxml")
            
            # Category pages use h3.mkd-post-title a or .package-title a
            for item in soup.select("h3.mkd-post-title a, .package-title a, .wpdm-download-link"):
                title_tag = item if item.name == "a" else item.find("a")
                if title_tag and title_tag.get("href"):
                    if "/download/" in title_tag["href"] or "/download-category/" not in title_tag["href"]:
                        doc_url = title_tag["href"]
                        title = title_tag.get_text(strip=True)
                        
                        if title and doc_url:
                            documents.append(JudiciaryDocument(
                                title=title,
                                category=category_slug,
                                date="",
                                url=doc_url
                            ))
            
            logger.info(f"Found {len(documents)} documents in category {category_slug}")
            
        except Exception as e:
            logger.error(f"Failed to scrape category {category_slug}: {e}")
            
        return documents

    async def fetch_document_details(self, doc: JudiciaryDocument) -> bool:
        """Fetch single document details and identify the direct download link."""
        try:
            html = await self._fetch_page(doc.url)
            soup = BeautifulSoup(html, "lxml")
            
            # Metadata might be in a table or list
            info_table = soup.select_one(".wpdm-metadata, .package-info")
            if info_table:
                # Try to find date
                date_match = re.search(r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})", info_table.get_text())
                if date_match:
                    doc.date = date_match.group(1)

            # Find download button
            download_btn = soup.select_one(".wpdm-download-link, a.btn-primary[href*='/download/']")
            if download_btn:
                doc.download_url = download_btn["href"]
                return True
                
        except Exception as e:
            logger.error(f"Failed to fetch details for {doc.url}: {e}")
            
        return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def download_file(self, url: str, save_path: Path) -> bool:
        """Download the file (usually PDF)."""
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                save_path.write_bytes(response.content)
                return True
        return False

    async def process_document(self, doc: JudiciaryDocument):
        """Full flow for one document."""
        if not doc.download_url:
            await self.fetch_document_details(doc)
            
        if doc.download_url:
            safe_name = re.sub(r"[^\w\-]", "_", doc.title)[:100]
            doc_dir = self.docs_dir / safe_name
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # We assume it's a PDF for now, but should check content-type
            file_path = doc_dir / "document.pdf"
            if await self.download_file(doc.download_url, file_path):
                doc.source_file = str(file_path)
                # Save metadata
                (doc_dir / "metadata.json").write_text(json.dumps(asdict(doc), indent=2))
                logger.info(f"Downloaded: {doc.title}")
                return True
        return False

async def run_judiciary_ingestion():
    scraper = JudiciaryScraper()
    categories = [
        "hc-practice-directions", 
        "cj-speeches", 
        "speeches",
        "administrative-circulars" # Try common variants
    ]
    
    all_docs = []
    for cat in categories:
        docs = await scraper.scrape_category(cat)
        for doc in docs:
            if await scraper.process_document(doc):
                all_docs.append(asdict(doc))
                
    # Save index
    index_path = scraper.metadata_dir / "judiciary_docs_index.json"
    index_path.write_text(json.dumps(all_docs, indent=2))
    logger.info(f"Judiciary ingestion complete. Total documents: {len(all_docs)}")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_judiciary_ingestion())
