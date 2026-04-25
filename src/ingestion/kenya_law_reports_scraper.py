"""
Kenya Legal AI — Kenya Law Reports Scraper
===========================================
Scrapes Kenya Law Reports (official law reports) covering East Africa
Law Reports, Kenya Law Reports, and historical judgments.

Source: https://kenyalawreports.or.ke/
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

logger = logging.getLogger(__name__)

BASE_URL = "https://kenyalawreports.or.ke"


class KenyaLawReportsScraper:
    """
    Scraper for Kenya Law Reports (EARLR, KLR, historical reports).
    """

    def __init__(self):
        self.settings = get_settings()
        self.raw_data_dir = Path(self.settings.raw_data_dir) / "kenya_law_reports"
        self.reports_dir = self.raw_data_dir / "reports"
        self.metadata_dir = Path(self.settings.metadata_dir)
        
        for d in [self.reports_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_page(self, url: str) -> str:
        """Fetch a page with retry."""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def search_reports(
        self,
        year: Optional[int] = None,
        query: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for law reports.
        
        Args:
            year: Specific year to search
            query: Search query term
        
        Returns:
            List of report metadata
        """
        try:
            logger.info("Fetching Kenya Law Reports index...")
            
            # Fetch main page
            html = await self._fetch_page(BASE_URL)
            soup = BeautifulSoup(html, "html.parser")
            
            reports = []
            
            # Look for report listings (structure may vary)
            # Try to find links to reports
            for link in soup.find_all("a", href=re.compile(r"/(report|judgment|case|volume)", re.I)):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not title or not href:
                    continue
                
                # Build absolute URL
                if href.startswith("http"):
                    report_url = href
                else:
                    report_url = BASE_URL + (href if href.startswith("/") else "/" + href)
                
                # Try to extract year
                year_match = re.search(r"\b(19|20)\d{2}\b", title)
                report_year = int(year_match.group()) if year_match else None
                
                # Filter by year if specified
                if year and report_year and report_year != year:
                    continue
                
                reports.append({
                    "title": title,
                    "url": report_url,
                    "year": report_year,
                    "source": "kenyalawreports",
                })
            
            logger.info(f"Found {len(reports)} law reports")
            return reports
            
        except Exception as e:
            logger.error(f"Error searching Kenya Law Reports: {e}")
            return []

    async def fetch_report_content(self, report_url: str) -> Optional[str]:
        """
        Fetch the full content of a law report.
        
        Args:
            report_url: URL of the report
        
        Returns:
            Report content or None
        """
        try:
            html = await self._fetch_page(report_url)
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            
            # Get main content
            content = soup.get_text(separator="\n", strip=True)
            return content
            
        except Exception as e:
            logger.error(f"Error fetching report content: {e}")
            return None

    async def save_report(self, report: Dict, content: Optional[str] = None) -> bool:
        """Save report metadata and content."""
        try:
            # Create safe filename
            safe_title = re.sub(r"[^a-z0-9]+", "_", report.get("title", "report").lower())
            safe_title = safe_title.strip("_")[:50]
            
            if not safe_title:
                safe_title = "report"
            
            # Save metadata
            metadata_file = self.reports_dir / f"{safe_title}_metadata.json"
            metadata_file.write_text(json.dumps(report, indent=2))
            
            # Save content if provided
            if content:
                content_file = self.reports_dir / f"{safe_title}_content.txt"
                content_file.write_text(content)
            
            logger.info(f"Saved report: {safe_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False

    async def ingest_all(self, limit: int = 100):
        """
        Ingest Kenya Law Reports.
        
        Args:
            limit: Maximum number of reports to fetch
        """
        logger.info("=== Starting Kenya Law Reports Ingestion ===")
        
        reports = await self.search_reports()
        
        for i, report in enumerate(reports[:limit]):
            logger.info(f"Processing report {i+1}/{min(limit, len(reports))}: {report.get('title')}")
            
            # Fetch content
            content = await self.fetch_report_content(report.get("url"))
            
            # Save report
            await self.save_report(report, content)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"=== Kenya Law Reports Ingestion Complete ({min(limit, len(reports))} reports) ===")


async def run_kenya_law_reports_ingestion(limit: int = 100):
    """Run Kenya Law Reports ingestion."""
    scraper = KenyaLawReportsScraper()
    await scraper.ingest_all(limit)


if __name__ == "__main__":
    asyncio.run(run_kenya_law_reports_ingestion())
