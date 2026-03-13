"""
Kenya Legal AI — Comprehensive Legislation Scraper
=================================================
Scrapes all primary and subsidiary legislation from new.kenyalaw.org/legislation/all.
Supports alphabetical crawling, metadata extraction, and content saving.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

LEGISLATION_INDEX_URL = "https://new.kenyalaw.org/legislation/all"
BASE_URL = "https://new.kenyalaw.org"

@dataclass
class LegislationMetadata:
    """Metadata for an Act of Parliament or S.I."""
    title: str
    number: str
    year: str
    category: str  # Primary or Subsidiary
    status: str    # Current, Repealed, etc.
    url: str
    source_file: Optional[str] = None

class LegislationScraper:
    """Systemic scraper for the entire Laws of Kenya database."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "legislation"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = Path(settings.metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
    async def _fetch_page(self, url: str) -> str:
        """Fetch page with browser-mimicking headers and retry logic."""
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers=self.headers) as client:
            response = await client.get(url)
            if response.status_code == 403:
                logger.error(f"403 Forbidden on {url}. Rate limited or anti-bot triggered.")
                raise Exception("Rate limited")
            response.raise_for_status()
            return response.text

    async def get_all_acts_links(self) -> List[dict]:
        """Scrape the main index for all legislation links."""
        logger.info(f"Fetching legislation index from {LEGISLATION_INDEX_URL}...")
        html = await self._fetch_page(LEGISLATION_INDEX_URL)
        soup = BeautifulSoup(html, "lxml")
        
        acts = []
        # Modern Kenya Law uses a list structure for legislation
        # Based on browser inspection: .legislation-list-item or similar
        items = soup.select(".legislation-list-item") or soup.select(".legislation-item")
        
        if not items:
            # Fallback to general link search if class names differ
            logger.warning("Specific CSS selectors failed. Falling back to general link search.")
            items = soup.find_all("a", href=re.compile(r"/legislation/\d+"))

        for item in items:
            link_tag = item if item.name == "a" else item.find("a")
            if not link_tag:
                continue
                
            title = link_tag.get_text(strip=True)
            url = urljoin(BASE_URL, link_tag["href"])
            
            # Basic category heuristic
            category = "Primary"
            if "Legal Notice" in title or "S.I." in title:
                category = "Subsidiary"
                
            acts.append({
                "title": title,
                "url": url,
                "category": category
            })
            
        logger.info(f"Found {len(acts)} legislation items in index.")
        return acts

    async def scrape_act_content(self, act_info: dict) -> Optional[dict]:
        """Fetch and parse the full text of a single Act."""
        url = act_info["url"]
        try:
            html_content = await self._fetch_page(url)
            soup = BeautifulSoup(html_content, "lxml")
            
            # Extract basic metadata from the page
            # Usually found in a .metadata or .legislation-header div
            header = soup.select_one(".legislation-header")
            act_number = ""
            if header:
                nums = re.findall(r"No\.\s*(\d+)\s*of\s*(\d{4})", header.get_text())
                if nums:
                    act_number = f"{nums[0][0]}/{nums[0][1]}"

            # Get the main text content
            # Kenya Law often uses .akn-body for the actual legal provisions
            content_div = soup.select_one(".akn-body") or soup.select_one(".document-content")
            if not content_div:
                logger.warning(f"No content div found for: {url}")
                return None
                
            full_text = content_div.get_text(separator="\n", strip=True)
            
            if len(full_text) < 500:
                logger.warning(f"Extracted content too short for: {url}")
                # Sometimes it's a link to a PDF
                pdf_link = soup.select_one('a[href$=".pdf"]')
                if pdf_link:
                    logger.info(f"Found PDF link instead: {pdf_link['href']}")
                    # Download logic can go here if needed
                return None

            metadata = LegislationMetadata(
                title=act_info["title"],
                number=act_number,
                year=act_number.split("/")[-1] if "/" in act_number else "",
                category=act_info["category"],
                status="Current", # Default
                url=url
            )

            # Save to disk
            safe_title = re.sub(r"[^\w\-]", "_", metadata.title)[:100]
            act_dir = self.output_dir / safe_title
            act_dir.mkdir(parents=True, exist_ok=True)
            
            text_file = act_dir / "content.txt"
            text_file.write_text(full_text, encoding="utf-8")
            
            meta_file = act_dir / "metadata.json"
            meta_file.write_text(json.dumps(asdict(metadata), indent=2))
            
            metadata.source_file = str(text_file)
            return asdict(metadata)

        except Exception as e:
            logger.error(f"Failed to scrape Act {url}: {e}")
            return None

    async def run_bulk_ingestion(self, limit: Optional[int] = None):
        """Scrape all legislation in a loop with respectful delays."""
        acts = await self.get_all_acts_links()
        
        if limit:
            acts = acts[:limit]
            
        results = []
        for i, act in enumerate(acts):
            logger.info(f"[{i+1}/{len(acts)}] Scramping: {act['title']}...")
            result = await self.scrape_act_content(act)
            if result:
                results.append(result)
            
            # Progressive checkpointing
            if (i + 1) % 20 == 0:
                self._save_index(results)
                
            await asyncio.sleep(2) # Respect the server
            
        self._save_index(results)
        logger.info(f"Bulk legislation scrape complete. Total: {len(results)}")
        return results

    def _save_index(self, results: List[dict]):
        """Save the list of successfully scraped acts."""
        index_path = self.metadata_dir / "scraped_legislation_index.json"
        index_path.write_text(json.dumps(results, indent=2))

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    scraper = LegislationScraper()
    # Test with 5 acts
    asyncio.run(scraper.run_bulk_ingestion(limit=5))
