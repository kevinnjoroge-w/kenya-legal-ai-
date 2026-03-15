"""
Kenya Legal AI — Kenya Gazette Online Archive Scraper
======================================================
Scrapes the historical Kenya Gazette Online Archive from kenyalaw.org/kl.
This is the *older* gazette archive (distinct from new.kenyalaw.org/gazettes)
and covers historical gazettes extending back toward independence (1963).

Saves to: data/raw/kenya_law/gazette_archive/{year}/{volume_issue}/
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
GAZETTE_ARCHIVE_URL = "http://kenyalaw.org/kl/index.php?id=gazette-online-archive"

START_YEAR = 2024
END_YEAR = 1963


@dataclass
class GazetteArchiveRecord:
    """Metadata for a historical Kenya Gazette."""
    year: str
    volume: str
    issue: str
    date: str
    title: str
    url: str
    source_file: Optional[str] = None


class KenyaGazetteScraper:
    """Scraper for the Kenya Gazette Online Archive (kenyalaw.org/kl)."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "gazette_archive"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "gazette_archive_checkpoint.json"
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
        return {"current_year": START_YEAR, "visited": [], "total": 0}

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

    def _year_url(self, year: int) -> str:
        return f"{GAZETTE_ARCHIVE_URL}&year={year}"

    def _parse_gazette_links(self, html: str, year: int) -> List[dict]:
        """Parse a year's gazette listing page."""
        soup = BeautifulSoup(html, "lxml")
        gazettes = []

        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 3:
                continue
            # Gazette links contain volume/issue patterns
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue
            if any(nav in text.lower() for nav in ["home", "back", "index", "search"]):
                continue

            # Try to extract volume and issue
            vol_m = re.search(r"Vol(?:ume)?\.?\s*(\w+)", text, re.I)
            iss_m = re.search(r"No\.?\s*(\d+)", text, re.I)
            date_m = re.search(
                r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}",
                text
            )

            gazettes.append({
                "title": text,
                "url": urljoin(BASE_URL, href) if not href.startswith("http") else href,
                "volume": vol_m.group(1) if vol_m else "",
                "issue": iss_m.group(1) if iss_m else "",
                "date": date_m.group() if date_m else "",
                "year": str(year),
            })

        return gazettes

    async def scrape_gazette(self, gazette_info: dict) -> Optional[dict]:
        """Scrape a single gazette entry."""
        async with self.semaphore:
            url = gazette_info["url"]
            if url in self.checkpoint.get("visited", []):
                return None

            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title_tag = soup.find("h1") or soup.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else gazette_info["title"]

                content_div = soup.select_one(".document-content, .akn-body, #content")
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = GazetteArchiveRecord(
                    year=gazette_info["year"],
                    volume=gazette_info.get("volume", ""),
                    issue=gazette_info.get("issue", ""),
                    date=gazette_info.get("date", ""),
                    title=title,
                    url=url,
                )

                safe_name = re.sub(r"[^\w\-]", "_", f"{gazette_info['year']}_{title}")[:80]
                doc_dir = self.output_dir / gazette_info["year"] / safe_name
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 200:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    # Download PDF
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="/source"], a[href*="download"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "gazette.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF failed {pdf_url}: {e}")

                (doc_dir / "metadata.json").write_text(
                    json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
                )
                self.checkpoint.setdefault("visited", []).append(url)
                self.checkpoint["total"] = self.checkpoint.get("total", 0) + 1
                self._save_checkpoint()
                logger.info(f"Scraped gazette: [{gazette_info['year']}] {title[:50]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed gazette {url}: {e}")
                return None

    async def run_bulk_ingestion(
        self,
        start_year: int = START_YEAR,
        end_year: int = END_YEAR,
        limit_per_year: Optional[int] = None,
    ):
        """Scrape all gazettes from start_year down to end_year."""
        # Resume from checkpoint
        resume_year = self.checkpoint.get("current_year", start_year)

        for year in range(resume_year, end_year - 1, -1):
            logger.info(f"--- Gazette Archive {year} ---")
            try:
                html = await self._fetch(self._year_url(year))
                gazettes = self._parse_gazette_links(html, year)
                if limit_per_year:
                    gazettes = gazettes[:limit_per_year]

                logger.info(f"  Found {len(gazettes)} gazette entries for {year}")
                for g in gazettes:
                    await self.scrape_gazette(g)
                    await asyncio.sleep(2)

                self.checkpoint["current_year"] = year - 1
                self._save_checkpoint()

            except Exception as e:
                logger.error(f"Error fetching gazette archive for {year}: {e}")

            await asyncio.sleep(3)

        logger.info(f"Gazette Archive ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_kenya_gazette_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = KenyaGazetteScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Kenya Gazette Archive ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test: 1 gazette from 2024
    asyncio.run(KenyaGazetteScraper().run_bulk_ingestion(start_year=2024, end_year=2024, limit_per_year=1))
