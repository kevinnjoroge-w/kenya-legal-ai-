"""
Kenya Legal AI — Bills Scraper
===============================
Scrapes National Assembly and Senate Bills from kenyalaw.org/kl.
Coverage: 2013–2024 (new bicameral era) + Bill Tracker 2007–2012.

URL pattern: http://kenyalaw.org/kl/index.php?id=<page_id>
Saves to:    data/raw/kenya_law/bills/{chamber}/{year}/{slug}/
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "http://kenyalaw.org"

# Sitemap-derived page IDs for bill index pages
# From the visible sitemap structure, bills live under the National Assembly / Senate sections
NATIONAL_ASSEMBLY_BILLS_YEARS = list(range(2024, 2012, -1))
SENATE_BILLS_YEARS = list(range(2024, 2012, -1))

# Bill Tracker legacy (2007-2012) uses different pages
BILL_TRACKER_YEARS = list(range(2012, 2006, -1))


@dataclass
class BillMetadata:
    """Metadata for a Parliamentary Bill."""
    title: str
    number: str
    year: str
    chamber: str   # "national_assembly" | "senate" | "tracker"
    stage: str     # e.g. "First Reading", "Assented to", etc.
    url: str
    source_file: Optional[str] = None
    attachments: List[dict] = field(default_factory=list)


class BillsScraper:
    """Scraper for Kenya Parliamentary Bills from kenyalaw.org/kl."""

    INDEX_URLS = {
        "national_assembly": "http://kenyalaw.org/kl/index.php?id=12024",
        "senate": "http://kenyalaw.org/kl/index.php?id=12025",
        "tracker_legacy": "http://kenyalaw.org/kl/index.php?id=12026",
    }

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "bills"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "bills_checkpoint.json"
        self.checkpoint = self._load_checkpoint()
        self.semaphore = asyncio.Semaphore(2)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text())
            except Exception:
                pass
        return {"completed": [], "total_bills": 0}

    def _save_checkpoint(self):
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=15))
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(
            timeout=30, headers=self.headers, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _parse_year_index(self, html: str, base_year: str) -> List[dict]:
        """Parse a chamber's year-level index page to find bill links."""
        soup = BeautifulSoup(html, "lxml")
        bills = []

        # Pattern: table rows or list items with bill links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            # Bills usually have patterns like "National Assembly Bill No. X of YYYY" or bold + link
            if not text or len(text) < 5:
                continue
            # Filter: ignore navigation/category links, keep document links
            if any(kw in href for kw in ["pid=", "id="]) or href.endswith(".pdf"):
                full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
                bills.append({"title": text, "url": full_url})

        return bills

    def _parse_bill_page(self, html: str, url: str, chamber: str, year: str) -> tuple:
        """Extract bill metadata and text from a single bill page."""
        soup = BeautifulSoup(html, "lxml")

        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown Bill"

        # Bill number e.g. "Bill No. 12 of 2024"
        number = ""
        num_match = re.search(r"Bill\s+No\.?\s*(\d+)\s+of\s+(\d{4})", title, re.I)
        if num_match:
            number = f"{num_match.group(1)}/{num_match.group(2)}"

        # Stage from breadcrumbs or metadata
        stage = ""
        for tag in soup.find_all(["span", "td", "li"]):
            text = tag.get_text(strip=True)
            if any(s in text for s in ["First Reading", "Second Reading", "Third Reading", "Assented", "Withdrawn", "Passed"]):
                stage = text[:80]
                break

        # Attachment links (PDFs)
        attachments = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf") or "/source" in href or "download" in href.lower():
                attachments.append({
                    "name": a.get_text(strip=True) or "Bill PDF",
                    "url": urljoin(BASE_URL, href) if not href.startswith("http") else href,
                })

        # Body text
        content_div = soup.select_one(".document-content, .akn-body, #content, .content-area")
        text = content_div.get_text(separator="\n", strip=True) if content_div else ""

        metadata = BillMetadata(
            title=title,
            number=number,
            year=year,
            chamber=chamber,
            stage=stage,
            url=url,
            attachments=attachments,
        )
        return metadata, text

    async def scrape_bill(self, bill_info: dict, chamber: str, year: str) -> Optional[dict]:
        """Scrape a single bill page."""
        async with self.semaphore:
            url = bill_info["url"]
            try:
                html = await self._fetch(url)
                metadata, text = self._parse_bill_page(html, url, chamber, year)

                safe_title = re.sub(r"[^\w\-]", "_", metadata.title)[:80]
                bill_dir = self.output_dir / chamber / year / safe_title
                bill_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = bill_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    # Try to download first PDF attachment
                    for att in metadata.attachments:
                        try:
                            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                                r = await client.get(att["url"])
                                r.raise_for_status()
                                pdf_path = bill_dir / "bill.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                                att["local_path"] = str(pdf_path)
                                break
                        except Exception as e:
                            logger.warning(f"PDF download failed for {att['url']}: {e}")

                meta_path = bill_dir / "metadata.json"
                meta_path.write_text(
                    json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
                )
                logger.info(f"Scraped bill: {metadata.title[:60]}")
                return {"metadata": asdict(metadata), "path": str(bill_dir)}

            except Exception as e:
                logger.error(f"Failed to scrape bill {url}: {e}")
                return None

    async def _scrape_chamber_year(self, chamber: str, year: int, year_url: str) -> int:
        """Scrape all bills from a chamber for a single year."""
        key = f"{chamber}_{year}"
        if key in self.checkpoint.get("completed", []):
            logger.info(f"Skipping {key} (already done)")
            return 0

        try:
            html = await self._fetch(year_url)
            bills = self._parse_year_index(html, str(year))
            logger.info(f"{chamber} {year}: found {len(bills)} bills")

            count = 0
            for bill in bills:
                result = await self.scrape_bill(bill, chamber, str(year))
                if result:
                    count += 1
                await asyncio.sleep(2)

            self.checkpoint.setdefault("completed", []).append(key)
            self.checkpoint["total_bills"] = self.checkpoint.get("total_bills", 0) + count
            self._save_checkpoint()
            return count

        except Exception as e:
            logger.error(f"Error scraping {chamber} {year}: {e}")
            return 0

    async def run_bulk_ingestion(self, limit_years: Optional[int] = None):
        """Scrape all bills from both chambers and bill tracker."""
        # National Assembly Bills
        for year in NATIONAL_ASSEMBLY_BILLS_YEARS[:limit_years]:
            year_url = f"http://kenyalaw.org/kl/index.php?id=national-assembly-bills-{year}"
            await self._scrape_chamber_year("national_assembly", year, year_url)
            await asyncio.sleep(3)

        # Senate Bills
        for year in SENATE_BILLS_YEARS[:limit_years]:
            year_url = f"http://kenyalaw.org/kl/index.php?id=senate-bills-{year}"
            await self._scrape_chamber_year("senate", year, year_url)
            await asyncio.sleep(3)

        # Bill Tracker (legacy)
        for year in BILL_TRACKER_YEARS[:limit_years]:
            year_url = f"http://kenyalaw.org/kl/index.php?id=bill-tracker-{year}"
            await self._scrape_chamber_year("tracker", year, year_url)
            await asyncio.sleep(3)

        logger.info(f"Bills ingestion complete. Total: {self.checkpoint.get('total_bills', 0)}")


async def run_bills_ingestion(limit_years: Optional[int] = None):
    """Entry point for mass_ingest.py."""
    scraper = BillsScraper()
    await scraper.run_bulk_ingestion(limit_years=limit_years)
    logger.info("Bills ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test: 1 year per chamber
    asyncio.run(run_bills_ingestion(limit_years=1))
