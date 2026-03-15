"""
Kenya Legal AI — Legal Notices Scraper (1963-Current)
=====================================================
Scrapes complete Legal Notices sitemap from kenyalaw.org/kl.
Historical coverage: Independence (1963) to present.
Structure: Year → Month → LN listings/PDFs/text.

Saves to: data/raw/kenya_law/legal_notices/{year}/{month}/{ln_num}/
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin, parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings
# Direct import for standalone testing
import httpx
from pathlib import Path
class DummyKenyaLawScraper:
    async def _download_pdf(self, url: Path, path: Path):
        # Stub for PDF - log only
        print(f'Stub PDF download: {url} -> {path}')
        path.write_text('PDF stub content')

KenyaLawScraper = DummyKenyaLawScraper

logger = logging.getLogger(__name__)

LEGAL_NOTICES_BASE = "http://kenyalaw.org/kl/index.php?id=12003"
BASE_URL = "http://kenyalaw.org"

@dataclass
class LNMetadata:
    """Legal Notice metadata."""
    number: str  # e.g., "168"
    year: str
    month: str
    title: str
    date: str
    url: str
    source_file: Optional[str] = None

class LegalNoticesScraper:
    """Full historical Legal Notices scraper with timeline coverage."""

    def __init__(self, checkpoint_file: str = "data/metadata/legal_notices_checkpoint.json"):
        settings = get_settings()
        self.raw_dir = Path(settings.raw_data_dir) / "kenya_law" / "legal_notices"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / checkpoint_file
        
        self.scraper = KenyaLawScraper()  # Reuse PDF download
        self.semaphore = asyncio.Semaphore(2)  # Conservative concurrency
        self.checkpoint = self._load_checkpoint()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text())
            except:
                pass
        return {"current_year": 2024, "current_month": None, "total_lns": 0}

    def _save_checkpoint(self):
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=10))
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30, headers=self.headers, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _parse_year_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        years = []
        # Pattern from sitemap: <a href with year like 'Legal Notices 2024'>
        for a in soup.find_all("a", string=re.compile(r"Legal Notices \d{4}")):
            href = a.get("href")
            if href:
                year_match = re.search(r"(\d{4})", a.get_text())
                if year_match:
                    years.append({"year": year_match.group(1), "url": urljoin(BASE_URL, href)})
        return years

    def _parse_month_links(self, html: str, year: str) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        months = []
        # e.g., 'November 2024 (LNs 168-180)'
        for a in soup.find_all("a"):
            text = a.get_text(strip=True)
            if re.search(rf"{year}.*LNs?\s*\d+", text):
                href = a.get("href")
                if href:
                    months.append({
                        "month": text.split(year)[0].strip(),
                        "range": re.search(r"LNs?\s*(\d+-\d+|\d+)", text),
                        "url": urljoin(BASE_URL, href)
                    })
        return months

    async def _parse_ln_links(self, month_url: str) -> List[dict]:
        html = await self._fetch(month_url)
        soup = BeautifulSoup(html, "lxml")
        lns = []
        # LN links: patterns like 'LN 168/2024 - Title'
        for tr in soup.find_all("tr"):
            a = tr.find("a")
            if a:
                text = a.get_text(strip=True)
                ln_match = re.search(r"LN\s*(\d+)(?:/(\d{4}))?", text)
                if ln_match:
                    lns.append({
                        "number": ln_match.group(1),
                        "year": ln_match.group(2) or "2024",
                        "title": text,
                        "url": urljoin(BASE_URL, a["href"])
                    })
        return lns

    async def scrape_ln(self, ln_info: dict, year: str, month: str) -> Optional[dict]:
        """Scrape single LN: metadata + content/PDF."""
        async with self.semaphore:
            try:
                html = await self._fetch(ln_info["url"])
                soup = BeautifulSoup(html, "lxml")
                
                # Extract metadata
                title = soup.find("h1") or soup.find("title")
                title = title.get_text(strip=True) if title else ln_info["title"]
                date_match = re.search(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", html)
                date = date_match.group() if date_match else ""
                
                metadata = LNMetadata(
                    number=ln_info["number"],
                    year=year,
                    month=month,
                    title=title,
                    date=date,
                    url=ln_info["url"]
                )
                
                # Content: prefer text, fallback PDF
                content_div = soup.select_one(".document-content, .akn-body, #content")
                content_text = content_div.get_text(separator="\\n", strip=True) if content_div else ""
                
                # Dir structure
                safe_month = re.sub(r"[^\\w]", "_", month)
                safe_num = f"LN_{metadata.number}_{year}"
                ln_dir = self.raw_dir / year / safe_month / safe_num
                ln_dir.mkdir(parents=True, exist_ok=True)
                
                # Save text if substantial
                if len(content_text) > 200:
                    text_path = ln_dir / "content.txt"
                    text_path.write_text(content_text)
                    metadata.source_file = str(text_path)
                else:
                    # PDF download (common for LNs)
                    pdf_link = soup.select_one('a[href$="/source"], a[href$=".pdf"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        pdf_path = ln_dir / "ln.pdf"
                        await self.scraper._download_pdf(pdf_url, pdf_path)
                        metadata.source_file = str(pdf_path)
                
                # Metadata JSON
                meta_path = ln_dir / "metadata.json"
                meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
                
                logger.info(f"Scraped {safe_num}: {title[:50]}...")
                return {"metadata": asdict(metadata), "path": str(ln_dir)}
                
            except Exception as e:
                logger.error(f"Failed {ln_info['url']}: {e}")
                return None

    async def run_bulk_ingestion(self, start_year: int = 2024, end_year: int = 1963, limit_months: Optional[int] = None):
        """Full historical scrape with resume."""
        year = self.checkpoint.get("current_year", start_year)
        
        # Main sitemap
        if year == start_year:
            sitemap_html = await self._fetch(LEGAL_NOTICES_BASE)
            year_infos = self._parse_year_links(sitemap_html)
        else:
            year_infos = [{"year": str(year), "url": f"http://kenyalaw.org/kl/index.php?id={year}"}]  # Resume
            
        for year_info in year_infos:
            y = year_info["year"]
            if int(y) < end_year:
                break
                
            logger.info(f"--- Year {y} ---")
            year_html = await self._fetch(year_info["url"])
            months = self._parse_month_links(year_html, y)
            
            month_idx = 0
            for month_info in months:
                m = month_info["month"]
                logger.info(f"  Month: {m}")
                
                lns = await self._parse_ln_links(month_info["url"])
                count = 0
                for ln_info in lns:
                    result = await self.scrape_ln(ln_info, y, m)
                    if result:
                        self.checkpoint["total_lns"] = self.checkpoint.get("total_lns", 0) + 1
                        count += 1
                    await asyncio.sleep(3)  # Respectful
                
                logger.info(f"  Scraped {count}/{len(lns)} LNs")
                month_idx += 1
                if limit_months and month_idx >= limit_months:
                    break
                
                self._save_checkpoint()
            
            self.checkpoint["current_year"] = str(int(y) - 1)
            self._save_checkpoint()
            await asyncio.sleep(5)
        
        logger.info(f"Complete! Total LNs: {self.checkpoint.get('total_lns', 0)}")

async def run_legal_notices_ingestion(limit_year: Optional[int] = None):
    """Entry point for mass_ingest.py."""
    scraper = LegalNoticesScraper()
    end_year = 1963 if not limit_year else max(1963, limit_year - 10)
    await scraper.run_bulk_ingestion(end_year=end_year)
    logger.info("Legal Notices ingestion finished.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_legal_notices_ingestion())
