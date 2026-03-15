"""
Kenya Legal AI — Hansard Scraper
==================================
Scrapes parliamentary debate records (Hansard) from the Kenya Law
Hansard Archive at kenyalaw.org/kl.

Coverage: National Assembly and Senate debates (all years available).
Saves to: data/raw/kenya_law/hansard/{house}/{year}/
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin, urlencode

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "http://kenyalaw.org"
HANSARD_SEARCH_URL = "http://kenyalaw.org/kl/index.php?id=506"

HOUSES = [
    {"name": "National Assembly", "slug": "national_assembly", "code": "na"},
    {"name": "Senate", "slug": "senate", "code": "se"},
]

START_YEAR = 1963
END_YEAR = 2024


@dataclass
class HansardRecord:
    """Metadata for a Hansard debate."""
    house: str
    house_slug: str
    date: str
    year: str
    title: str
    url: str
    source_file: Optional[str] = None


class HansardScraper:
    """Scraper for Kenya Parliament Hansard Archive."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "hansard"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "hansard_checkpoint.json"
        self.checkpoint = self._load_checkpoint()
        self.semaphore = asyncio.Semaphore(2)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text())
            except Exception:
                pass
        return {"completed": [], "total": 0}

    def _save_checkpoint(self):
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=15))
    async def _fetch(self, url: str, params: Optional[dict] = None) -> str:
        if params:
            url = f"{url}?{urlencode(params)}"
        async with httpx.AsyncClient(
            timeout=30, headers=self.headers, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _parse_hansard_index(self, html: str) -> List[dict]:
        """Parse Hansard search/index results for individual debate links."""
        soup = BeautifulSoup(html, "lxml")
        records = []

        # Common structure: table with date + title + download link
        for tr in soup.find_all("tr"):
            a = tr.find("a", href=True)
            if not a:
                continue
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 3:
                continue

            # Look for date in row
            cells = tr.find_all("td")
            date_text = ""
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                date_m = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2}", cell_text)
                if date_m:
                    date_text = date_m.group()
                    break
            year_m = re.search(r"\d{4}", date_text or text)
            year = year_m.group() if year_m else "unknown"

            records.append({
                "title": text,
                "url": urljoin(BASE_URL, href) if not href.startswith("http") else href,
                "date": date_text,
                "year": year,
            })

        # Also look for links in a list format
        if not records:
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if ("hansard" in href.lower() or "debate" in href.lower()) and text:
                    year_m = re.search(r"\d{4}", text)
                    records.append({
                        "title": text,
                        "url": urljoin(BASE_URL, href) if not href.startswith("http") else href,
                        "date": "",
                        "year": year_m.group() if year_m else "unknown",
                    })

        return records

    async def scrape_debate(self, record: dict, house: dict) -> Optional[dict]:
        """Scrape a single Hansard debate."""
        async with self.semaphore:
            url = record["url"]
            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title_tag = soup.find("h1") or soup.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else record["title"]

                content_div = soup.select_one(".document-content, .akn-body, #content, .field-item")
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = HansardRecord(
                    house=house["name"],
                    house_slug=house["slug"],
                    date=record.get("date", ""),
                    year=record.get("year", "unknown"),
                    title=title,
                    url=url,
                )

                safe_title = re.sub(r"[^\w\-]", "_", title)[:80]
                year = record.get("year", "unknown")
                doc_dir = self.output_dir / house["slug"] / year / safe_title
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 200:
                    txt_path = doc_dir / "debate.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    # Try PDF download
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="download"], a[href*="/source"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "debate.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF download failed {pdf_url}: {e}")

                meta_path = doc_dir / "metadata.json"
                meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
                logger.info(f"Scraped Hansard: [{house['slug']}] {title[:50]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed debate {url}: {e}")
                return None

    async def scrape_year(self, house: dict, year: int, limit: Optional[int] = None) -> int:
        """Scrape all debates for a house in a given year."""
        key = f"{house['slug']}_{year}"
        if key in self.checkpoint.get("completed", []):
            return 0

        try:
            # Kenya Law Hansard search: filter by year and house
            params = {"tx_llkhanssard_pi1[year]": str(year), "tx_llkhanssard_pi1[house]": house["code"]}
            html = await self._fetch(HANSARD_SEARCH_URL, params=params)
            records = self._parse_hansard_index(html)
            if limit:
                records = records[:limit]

            logger.info(f"  {house['name']} {year}: {len(records)} debates")
            count = 0
            for rec in records:
                result = await self.scrape_debate(rec, house)
                if result:
                    count += 1
                await asyncio.sleep(2)

            self.checkpoint.setdefault("completed", []).append(key)
            self.checkpoint["total"] = self.checkpoint.get("total", 0) + count
            self._save_checkpoint()
            return count

        except Exception as e:
            logger.error(f"Error scraping Hansard {house['slug']} {year}: {e}")
            return 0

    async def run_bulk_ingestion(
        self,
        start_year: int = END_YEAR,
        end_year: int = START_YEAR,
        limit_per_year: Optional[int] = None,
    ):
        """Scrape all Hansard records across all houses and years."""
        for house in HOUSES:
            logger.info(f"=== {house['name']} Hansard ===")
            for year in range(start_year, end_year - 1, -1):
                await self.scrape_year(house, year, limit=limit_per_year)
                await asyncio.sleep(3)

        logger.info(f"Hansard ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_hansard_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = HansardScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Hansard ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test: only 1 debate per year for the most recent year
    asyncio.run(HansardScraper().run_bulk_ingestion(start_year=2024, end_year=2024, limit_per_year=1))
