"""
Kenya Legal AI — KRA Tax Laws Scraper
=====================================
Scrapes Kenya Revenue Authority (KRA) tax legislation, regulations,
and circulars from https://kra.go.ke/

Covers: Income Tax Act, VAT Act, Excise Duty Act, Tax Procedures Act,
and associated legal notices and circulars.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
import re

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings
from src.ingestion.browser_fetcher import BrowserUseFetcher

logger = logging.getLogger(__name__)

BASE_URL = "https://kra.go.ke"


class KRATaxLawsScraper:
    """
    Scraper for Kenya Revenue Authority tax laws, regulations, and circulars.
    """

    def __init__(self):
        self.settings = get_settings()
        self.raw_data_dir = Path(self.settings.raw_data_dir) / "kra_tax_laws"
        self.acts_dir = self.raw_data_dir / "acts"
        self.regulations_dir = self.raw_data_dir / "regulations"
        self.circulars_dir = self.raw_data_dir / "circulars"
        self.metadata_dir = Path(self.settings.metadata_dir)
        self.browser_fetcher = BrowserUseFetcher()
        
        for d in [self.acts_dir, self.regulations_dir, self.circulars_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)

    async def _fetch_page(self, url: str) -> str:
        """Fetch a page with httpx, fallback to browser if 403 or error."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            ) as client:
                response = await client.get(url)
                if response.status_code == 403:
                    logger.info(f"403 from httpx on {url}, using browser fallback...")
                    return await self.browser_fetcher.fetch_html(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.warning(f"httpx fetch failed on {url}: {e}, trying browser fallback...")
            return await self.browser_fetcher.fetch_html(url)

    async def _fetch_pdf_or_text(self, url: str) -> Optional[str]:
        """Fetch PDF or text content from URL."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                
                if "pdf" in content_type:
                    # For PDFs, we'd need a PDF library
                    # For now, just save the filename and URL
                    return f"[PDF Document] {url}"
                else:
                    return response.text
        except Exception as e:
            logger.warning(f"Could not fetch {url}: {e}")
            return None

    async def search_tax_acts(self) -> List[Dict]:
        """
        Search for Kenya tax acts (Income Tax Act, VAT Act, etc.).
        
        Returns:
            List of tax act metadata
        """
        try:
            logger.info("Fetching KRA tax acts...")
            
            # Define major tax acts in Kenya
            tax_acts = [
                {
                    "title": "Income Tax Act (Cap. 470)",
                    "url": f"{BASE_URL}/individual-and-corporate-income-tax",
                    "type": "act",
                },
                {
                    "title": "Value Added Tax (VAT) Act (No. 35 of 2013)",
                    "url": f"{BASE_URL}/value-added-tax-vat",
                    "type": "act",
                },
                {
                    "title": "Excise Duty Act (No. 23 of 2015)",
                    "url": f"{BASE_URL}/excise-duty",
                    "type": "act",
                },
                {
                    "title": "Tax Procedures Act (No. 30 of 2015)",
                    "url": f"{BASE_URL}/tax-procedures-act",
                    "type": "act",
                },
                {
                    "title": "Betting, Lotteries and Gaming Act",
                    "url": f"{BASE_URL}/betting-lotteries-and-gaming-act",
                    "type": "act",
                },
                {
                    "title": "Business Registration Act",
                    "url": f"{BASE_URL}/business-registration-act",
                    "type": "act",
                },
            ]
            
            return tax_acts
            
        except Exception as e:
            logger.error(f"Error searching tax acts: {e}")
            return []

    async def fetch_tax_act_content(self, url: str) -> Optional[str]:
        """
        Fetch full content of a tax act.
        
        Args:
            url: URL of the tax act page
        
        Returns:
            Content or None
        """
        try:
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            # Extract main content
            content = soup.get_text(separator="\n", strip=True)
            return content
            
        except Exception as e:
            logger.error(f"Error fetching act content: {e}")
            return None

    async def search_regulations_and_rules(self) -> List[Dict]:
        """Fetch KRA regulations and rules."""
        try:
            logger.info("Fetching KRA regulations...")
            
            url = f"{BASE_URL}/tax-legislation"
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            regulations = []
            
            # Look for regulation links
            for link in soup.find_all("a", href=re.compile(r"(regulation|rule|statutory)", re.I)):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not title or not href:
                    continue
                
                # Build absolute URL
                if href.startswith("http"):
                    reg_url = href
                else:
                    reg_url = BASE_URL + (href if href.startswith("/") else "/" + href)
                
                regulations.append({
                    "title": title,
                    "url": reg_url,
                    "type": "regulation",
                    "source": "kra",
                })
            
            logger.info(f"Found {len(regulations)} regulations")
            return regulations
            
        except Exception as e:
            logger.error(f"Error searching regulations: {e}")
            return []

    async def search_tax_circulars(self) -> List[Dict]:
        """
        Fetch KRA tax circulars and practice notes.
        
        Returns:
            List of circular metadata
        """
        try:
            logger.info("Fetching KRA tax circulars...")
            
            url = f"{BASE_URL}/tax-circulars"
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            circulars = []
            
            # Look for circular links
            for link in soup.find_all("a", href=re.compile(r"(circular|notice|guidance)", re.I)):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not title or not href:
                    continue
                
                if href.startswith("http"):
                    circ_url = href
                else:
                    circ_url = BASE_URL + (href if href.startswith("/") else "/" + href)
                
                # Try to extract date
                date_match = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", title)
                date = date_match.group() if date_match else None
                
                circulars.append({
                    "title": title,
                    "url": circ_url,
                    "date": date,
                    "type": "circular",
                    "source": "kra",
                })
            
            logger.info(f"Found {len(circulars)} circulars")
            return circulars
            
        except Exception as e:
            logger.error(f"Error searching circulars: {e}")
            return []

    async def save_tax_document(self, doc: Dict, content: Optional[str] = None) -> bool:
        """Save tax document metadata and content."""
        try:
            # Create safe filename
            safe_title = re.sub(r"[^a-z0-9]+", "_", doc.get("title", "document").lower())
            safe_title = safe_title.strip("_")[:50]
            
            if not safe_title:
                safe_title = "document"
            
            # Determine which directory to use
            doc_type = doc.get("type", "act").lower()
            if "circular" in doc_type or "notice" in doc_type:
                target_dir = self.circulars_dir
            elif "regulation" in doc_type or "rule" in doc_type:
                target_dir = self.regulations_dir
            else:
                target_dir = self.acts_dir
            
            # Save metadata
            metadata_file = target_dir / f"{safe_title}_metadata.json"
            metadata_file.write_text(json.dumps(doc, indent=2))
            
            # Save content if provided
            if content:
                content_file = target_dir / f"{safe_title}_content.txt"
                content_file.write_text(content)
            
            logger.info(f"Saved {doc_type}: {safe_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False

    async def ingest_all(self, limit: int = 50):
        """
        Ingest all KRA tax laws, regulations, and circulars.
        
        Args:
            limit: Maximum documents to fetch
        """
        logger.info("=== Starting KRA Tax Laws Ingestion ===")
        
        count = 0
        
        # Ingest tax acts
        acts = await self.search_tax_acts()
        for act in acts[:limit]:
            if count >= limit:
                break
            
            logger.info(f"Processing act: {act.get('title')}")
            content = await self.fetch_tax_act_content(act.get("url"))
            await self.save_tax_document(act, content)
            count += 1
            await asyncio.sleep(0.5)
        
        # Ingest regulations
        regulations = await self.search_regulations_and_rules()
        for reg in regulations[:limit - count]:
            if count >= limit:
                break
            
            logger.info(f"Processing regulation: {reg.get('title')}")
            content = await self.fetch_tax_act_content(reg.get("url"))
            await self.save_tax_document(reg, content)
            count += 1
            await asyncio.sleep(0.5)
        
        # Ingest circulars
        circulars = await self.search_tax_circulars()
        for circ in circulars[:limit - count]:
            if count >= limit:
                break
            
            logger.info(f"Processing circular: {circ.get('title')}")
            content = await self.fetch_tax_act_content(circ.get("url"))
            await self.save_tax_document(circ, content)
            count += 1
            await asyncio.sleep(0.5)
        
        logger.info(f"=== KRA Tax Laws Ingestion Complete ({count} documents) ===")


async def run_kra_ingestion(limit: int = 50):
    """Run KRA tax laws ingestion."""
    scraper = KRATaxLawsScraper()
    await scraper.ingest_all(limit)


if __name__ == "__main__":
    asyncio.run(run_kra_ingestion())
