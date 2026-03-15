"""
Kenya Legal AI — County Legislation Scraper
============================================
Scrapes Acts, Bills, and Legal Notices from the 9 counties with
available legislation on kenyalaw.org:

  Baringo, Kitui, Laikipia, Machakos, Makueni,
  Turkana, Uasin Gishu, Wajir, West Pokot

Coverage: 2013–2021 (per-county, per-doc-type)
Saves to: data/raw/kenya_law/county/{county}/{doc_type}/{year}/
"""

import asyncio
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

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "http://kenyalaw.org"

COUNTIES = [
    {"name": "Baringo County", "slug": "baringo"},
    {"name": "Kitui County", "slug": "kitui"},
    {"name": "Laikipia County", "slug": "laikipia"},
    {"name": "Machakos County", "slug": "machakos"},
    {"name": "Makueni County", "slug": "makueni"},
    {"name": "Turkana County", "slug": "turkana"},
    {"name": "Uasin Gishu County", "slug": "uasin_gishu"},
    {"name": "Wajir County", "slug": "wajir"},
    {"name": "West Pokot County", "slug": "west_pokot"},
]

DOC_TYPES = ["acts", "bills", "legal_notices"]
COUNTY_YEARS = list(range(2021, 2012, -1))  # 2013–2021


@dataclass
class CountyLegislation:
    """Metadata for a County Government legal document."""
    county: str
    county_slug: str
    doc_type: str   # "acts" | "bills" | "legal_notices"
    year: str
    title: str
    number: str
    url: str
    source_file: Optional[str] = None


class CountyLegislationScraper:
    """Scraper for County Government legislation from kenyalaw.org."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "county"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "county_legislation_checkpoint.json"
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
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(
            timeout=30, headers=self.headers, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _county_index_url(self, county_slug: str, doc_type: str, year: int) -> str:
        """Construct the URL for a county's doc-type year index."""
        # Kenya Law county section URL pattern
        return (
            f"http://kenyalaw.org/kl/index.php"
            f"?id=county-{county_slug}-{doc_type}-{year}"
        )

    def _parse_docs(self, html: str) -> List[dict]:
        """Parse an index page and extract document links."""
        soup = BeautifulSoup(html, "lxml")
        docs = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 5:
                continue
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue
            num_m = re.search(r"No\.?\s*(\d+)\s+of\s+(\d{4})", text, re.I)
            docs.append({
                "title": text,
                "url": urljoin(BASE_URL, href) if not href.startswith("http") else href,
                "number": f"{num_m.group(1)}/{num_m.group(2)}" if num_m else "",
            })
        return docs

    async def scrape_doc(
        self, doc_info: dict, county: dict, doc_type: str, year: str
    ) -> Optional[dict]:
        """Scrape a single county legislation document."""
        async with self.semaphore:
            url = doc_info["url"]
            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title_tag = soup.find("h1") or soup.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else doc_info["title"]

                content_div = soup.select_one(".document-content, .akn-body, #content")
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = CountyLegislation(
                    county=county["name"],
                    county_slug=county["slug"],
                    doc_type=doc_type,
                    year=year,
                    title=title,
                    number=doc_info.get("number", ""),
                    url=url,
                )

                safe_title = re.sub(r"[^\w\-]", "_", title)[:80]
                doc_dir = self.output_dir / county["slug"] / doc_type / year / safe_title
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="/source"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "document.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF failed {pdf_url}: {e}")

                (doc_dir / "metadata.json").write_text(
                    json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
                )
                logger.info(f"Scraped county doc: [{county['slug']}/{doc_type}/{year}] {title[:50]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed {url}: {e}")
                return None

    async def scrape_county_type_year(
        self, county: dict, doc_type: str, year: int, limit: Optional[int] = None
    ) -> int:
        """Scrape all docs for one county / doc_type / year combination."""
        key = f"{county['slug']}_{doc_type}_{year}"
        if key in self.checkpoint.get("completed", []):
            return 0

        url = self._county_index_url(county["slug"], doc_type, year)
        try:
            html = await self._fetch(url)
            docs = self._parse_docs(html)
            if limit:
                docs = docs[:limit]

            count = 0
            for doc in docs:
                result = await self.scrape_doc(doc, county, doc_type, str(year))
                if result:
                    count += 1
                await asyncio.sleep(2)

            self.checkpoint.setdefault("completed", []).append(key)
            self.checkpoint["total"] = self.checkpoint.get("total", 0) + count
            self._save_checkpoint()
            return count

        except Exception as e:
            logger.error(f"Error {key}: {e}")
            return 0

    async def run_bulk_ingestion(self, limit_per_batch: Optional[int] = None):
        """Scrape all 9 counties × 3 doc types × years."""
        for county in COUNTIES:
            for doc_type in DOC_TYPES:
                for year in COUNTY_YEARS:
                    await self.scrape_county_type_year(county, doc_type, year, limit=limit_per_batch)
                    await asyncio.sleep(2)
            logger.info(f"Done county: {county['name']}")
            await asyncio.sleep(4)

        logger.info(f"County legislation ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_county_legislation_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = CountyLegislationScraper()
    await scraper.run_bulk_ingestion()
    logger.info("County legislation ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_county_legislation_ingestion())
