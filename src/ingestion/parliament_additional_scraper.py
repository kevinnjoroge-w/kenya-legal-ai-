"""
Kenya Legal AI — Parliament Additional Documents Scraper
=========================================================
Scrapes Parliament of Kenya (parliament.go.ke) for additional legislative
documents beyond Hansard, including Order Papers, Votes & Proceedings,
Committee Reports, and Standing Orders.

Source: https://www.parliament.go.ke/
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings
from src.ingestion.browser_fetcher import BrowserUseFetcher

logger = logging.getLogger(__name__)

BASE_URL = "https://www.parliament.go.ke"


class ParliamentAdditionalDocumentsScraper:
    """
    Scraper for Parliament of Kenya additional documents:
    Order Papers, Votes & Proceedings, Committee Reports, Standing Orders.
    """

    def __init__(self):
        self.settings = get_settings()
        self.raw_data_dir = Path(self.settings.raw_data_dir) / "parliament_additional"
        self.order_papers_dir = self.raw_data_dir / "order_papers"
        self.votes_proceedings_dir = self.raw_data_dir / "votes_proceedings"
        self.committee_reports_dir = self.raw_data_dir / "committee_reports"
        self.standing_orders_dir = self.raw_data_dir / "standing_orders"
        self.metadata_dir = Path(self.settings.metadata_dir)
        self.browser_fetcher = BrowserUseFetcher()
        
        for d in [
            self.order_papers_dir,
            self.votes_proceedings_dir,
            self.committee_reports_dir,
            self.standing_orders_dir,
            self.metadata_dir,
        ]:
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

    async def fetch_order_papers(self, house: str = "national_assembly") -> List[Dict]:
        """
        Fetch Order Papers (parliamentary agenda).
        
        Args:
            house: 'national_assembly' or 'senate'
        
        Returns:
            List of order paper metadata
        """
        try:
            logger.info(f"Fetching Order Papers for {house}...")
            
            # National Assembly Order Papers
            if house == "national_assembly":
                url = f"{BASE_URL}/the-national-assembly/house-business/order-paper"
            else:
                url = f"{BASE_URL}/the-senate/orderpapers"
            
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            papers = []
            
            # Look for PDF or document links
            for link in soup.find_all("a", href=re.compile(r"\.pdf|order.*paper", re.I)):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not title or not href:
                    continue
                
                # Build absolute URL
                paper_url = urljoin(BASE_URL, href)
                
                # Extract date
                date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})", title)
                date = date_match.group() if date_match else None
                
                papers.append({
                    "title": title,
                    "url": paper_url,
                    "date": date,
                    "house": house,
                    "document_type": "order_paper",
                    "source": "parliament",
                })
            
            logger.info(f"Found {len(papers)} order papers for {house}")
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching order papers: {e}")
            return []

    async def fetch_votes_and_proceedings(self, house: str = "national_assembly") -> List[Dict]:
        """
        Fetch Votes & Proceedings (daily record of parliament).
        
        Args:
            house: 'national_assembly' or 'senate'
        
        Returns:
            List of votes & proceedings metadata
        """
        try:
            logger.info(f"Fetching Votes & Proceedings for {house}...")
            
            if house == "national_assembly":
                url = f"{BASE_URL}/the-national-assembly/house-business/votes-proceeding"
            else:
                url = f"{BASE_URL}/the-senate/votes-proceeding"
            
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            proceedings = []
            
            # Look for document links
            for link in soup.find_all("a", href=re.compile(r"\.pdf|proceeding|votes", re.I)):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not title or not href or len(title) < 5:
                    continue
                
                proc_url = urljoin(BASE_URL, href)
                
                # Extract date
                date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})", title)
                date = date_match.group() if date_match else None
                
                proceedings.append({
                    "title": title,
                    "url": proc_url,
                    "date": date,
                    "house": house,
                    "document_type": "votes_and_proceedings",
                    "source": "parliament",
                })
            
            logger.info(f"Found {len(proceedings)} votes & proceedings for {house}")
            return proceedings
            
        except Exception as e:
            logger.error(f"Error fetching votes and proceedings: {e}")
            return []

    async def fetch_committee_reports(self) -> List[Dict]:
        """
        Fetch Parliamentary Committee Reports.
        
        Returns:
            List of committee report metadata
        """
        try:
            logger.info("Fetching Committee Reports...")
            
            # National Assembly Committees
            na_url = f"{BASE_URL}/the-national-assembly/committees"
            senate_url = f"{BASE_URL}/the-senate/committees"
            
            reports = []
            
            for house, url in [("national_assembly", na_url), ("senate", senate_url)]:
                html = await self._fetch_page(url)
                soup = BeautifulSoup(html, "html.parser")
                
                # Look for committee links
                for link in soup.find_all("a", href=re.compile(r"committee", re.I)):
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    
                    if not title or not href or "committee" not in href.lower():
                        continue
                    
                    committee_url = urljoin(BASE_URL, href)
                    
                    reports.append({
                        "title": title,
                        "url": committee_url,
                        "house": house,
                        "document_type": "committee_report",
                        "source": "parliament",
                    })
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            logger.info(f"Found {len(reports)} committee report links")
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching committee reports: {e}")
            return []

    async def fetch_standing_orders(self) -> List[Dict]:
        """
        Fetch Standing Orders (parliamentary rules).
        
        Returns:
            List of standing orders metadata
        """
        try:
            logger.info("Fetching Standing Orders...")
            
            orders = [
                {
                    "title": "National Assembly Standing Orders",
                    "url": f"{BASE_URL}/the-national-assembly/standing-orders",
                    "house": "national_assembly",
                },
                {
                    "title": "Senate Standing Orders",
                    "url": f"{BASE_URL}/the-senate/standing-orders",
                    "house": "senate",
                },
            ]
            
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching standing orders: {e}")
            return []

    async def fetch_document_content(self, url: str) -> Optional[str]:
        """
        Fetch document content.
        
        Args:
            url: Document URL
        
        Returns:
            Document content or None
        """
        try:
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            content = soup.get_text(separator="\n", strip=True)
            return content if content else None
            
        except Exception as e:
            logger.warning(f"Could not fetch content from {url}: {e}")
            return None

    async def save_document(self, doc: Dict, content: Optional[str] = None) -> bool:
        """Save parliament document metadata and content."""
        try:
            # Create safe filename
            safe_title = re.sub(r"[^a-z0-9]+", "_", doc.get("title", "document").lower())
            safe_title = safe_title.strip("_")[:50]
            
            if not safe_title:
                safe_title = "document"
            
            # Determine which directory to use
            doc_type = doc.get("document_type", "").lower()
            if "order" in doc_type:
                target_dir = self.order_papers_dir
            elif "votes" in doc_type or "proceeding" in doc_type:
                target_dir = self.votes_proceedings_dir
            elif "committee" in doc_type:
                target_dir = self.committee_reports_dir
            elif "standing" in doc_type:
                target_dir = self.standing_orders_dir
            else:
                target_dir = self.raw_data_dir
            
            # Save metadata
            metadata_file = target_dir / f"{safe_title}_metadata.json"
            metadata_file.write_text(json.dumps(doc, indent=2))
            
            # Save content if provided
            if content:
                content_file = target_dir / f"{safe_title}_content.txt"
                content_file.write_text(content)
            
            logger.info(f"Saved document: {safe_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False

    async def ingest_all(self, limit: int = 100):
        """
        Ingest all Parliament additional documents.
        
        Args:
            limit: Maximum documents per category
        """
        logger.info("=== Starting Parliament Additional Documents Ingestion ===")
        
        # Ingest Order Papers (both houses)
        for house in ["national_assembly", "senate"]:
            papers = await self.fetch_order_papers(house)
            for paper in papers[:limit]:
                content = await self.fetch_document_content(paper.get("url"))
                await self.save_document(paper, content)
                await asyncio.sleep(0.3)
        
        # Ingest Votes & Proceedings (both houses)
        for house in ["national_assembly", "senate"]:
            proceedings = await self.fetch_votes_and_proceedings(house)
            for proc in proceedings[:limit]:
                content = await self.fetch_document_content(proc.get("url"))
                await self.save_document(proc, content)
                await asyncio.sleep(0.3)
        
        # Ingest Committee Reports
        committees = await self.fetch_committee_reports()
        for committee in committees[:limit]:
            content = await self.fetch_document_content(committee.get("url"))
            await self.save_document(committee, content)
            await asyncio.sleep(0.3)
        
        # Ingest Standing Orders
        orders = await self.fetch_standing_orders()
        for order in orders:
            content = await self.fetch_document_content(order.get("url"))
            await self.save_document(order, content)
            await asyncio.sleep(0.5)
        
        logger.info("=== Parliament Additional Documents Ingestion Complete ===")


async def run_parliament_additional_ingestion(limit: int = 100):
    """Run Parliament additional documents ingestion."""
    scraper = ParliamentAdditionalDocumentsScraper()
    await scraper.ingest_all(limit)


if __name__ == "__main__":
    asyncio.run(run_parliament_additional_ingestion())
