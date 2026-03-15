"""
Kenya Legal AI — Practice Notes & Directions Scraper
=====================================================
Scrapes Practice Directions and Practice Notes from kenyalaw.org/kl.

Coverage: 1961, 1978, 1982, 1984, 1997, 2007, 2008, 2009, 2011,
          2012, 2013, 2014, 2015, 2016, 2020, 2022
Includes: Gazette Notices, Court Circulars, Practice Directions

Saves to: data/raw/kenya_law/practice_notes/{year}/{slug}/
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

# Mapping of year → sitemap URL structure from the kenyalaw.org sitemap
# These are the known named sections from the sitemap
PRACTICE_NOTES_SECTIONS = [
    {"year": "2022", "label": "Practice Directions 2022",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-directions-2022"},
    {"year": "2020", "label": "Practice Directions 2020",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-directions-2020"},
    {"year": "2016", "label": "Practice Directions 2016",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-directions-2016"},
    {"year": "2015", "label": "Practice Directions 2015",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-directions-2015"},
    {"year": "2014", "label": "Practice Notes 2014",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2014"},
    {"year": "2013", "label": "Practice Notes 2013",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2013"},
    {"year": "2012", "label": "Practice Notes 2012",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2012"},
    {"year": "2011", "label": "Practice Notes 2011",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2011"},
    {"year": "2009", "label": "Practice Notes 2009",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2009"},
    {"year": "2008", "label": "Practice Notes 2008",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2008"},
    {"year": "2007", "label": "Practice Notes 2007",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-2007"},
    {"year": "1997", "label": "Practice Notes 1997",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-1997"},
    {"year": "1984", "label": "Practice Notes 1984",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-1984"},
    {"year": "1982", "label": "Practice Notes 1982",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-1982"},
    {"year": "1978", "label": "Practice Notes 1978",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-1978"},
    {"year": "1961", "label": "Practice Notes 1961",
     "url": "http://kenyalaw.org/kl/index.php?id=practice-notes-1961"},
]

# Main index page (parent of all Practice Notes)
PRACTICE_NOTES_INDEX = "http://kenyalaw.org/kl/index.php?id=3521"


@dataclass
class PracticeNoteMetadata:
    """Metadata for a Practice Note/Direction."""
    year: str
    label: str
    title: str
    gazette_notice: str   # e.g. "Gazette Notice No. 5178"
    url: str
    source_file: Optional[str] = None


class PracticeNotesScraper:
    """Scraper for Kenya Law Practice Notes and Practice Directions."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "practice_notes"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "practice_notes_checkpoint.json"
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

    def _parse_section_links(self, html: str, section_url: str) -> List[dict]:
        """Parse a section index page and return individual document links."""
        soup = BeautifulSoup(html, "lxml")
        docs = []

        # Look for links to specific practice directions/notes
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 5:
                continue
            # Skip navigation and category links
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue
            if href == section_url:
                continue

            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href

            # Extract gazette notice number if present
            gn_match = re.search(r"Gazette\s+Notice\s+No\.?\s*([\d,]+)", text, re.I)
            gazette_notice = gn_match.group(0) if gn_match else ""

            docs.append({
                "title": text,
                "url": full_url,
                "gazette_notice": gazette_notice,
            })

        return docs

    async def scrape_document(self, doc_info: dict, year: str, label: str) -> Optional[dict]:
        """Scrape a single practice note/direction document."""
        async with self.semaphore:
            url = doc_info["url"]
            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title = soup.find("h1")
                title_text = title.get_text(strip=True) if title else doc_info["title"]

                # Extract body text
                content_div = soup.select_one(
                    ".document-content, .akn-body, #content, .field-items, .field-item"
                )
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = PracticeNoteMetadata(
                    year=year,
                    label=label,
                    title=title_text,
                    gazette_notice=doc_info.get("gazette_notice", ""),
                    url=url,
                )

                safe_title = re.sub(r"[^\w\-]", "_", title_text)[:80]
                doc_dir = self.output_dir / year / safe_title
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    # Try PDF
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="download"]')
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
                            logger.warning(f"PDF failed for {pdf_url}: {e}")

                meta_path = doc_dir / "metadata.json"
                meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
                logger.info(f"Scraped practice note: {title_text[:60]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                return None

    async def run_bulk_ingestion(self, limit: Optional[int] = None):
        """Scrape all practice note sections."""
        sections = PRACTICE_NOTES_SECTIONS[:limit] if limit else PRACTICE_NOTES_SECTIONS

        for section in sections:
            year = section["year"]
            label = section["label"]
            key = f"practice_notes_{year}"

            if key in self.checkpoint.get("completed", []):
                logger.info(f"Skipping {key} (already done)")
                continue

            logger.info(f"--- {label} ---")
            try:
                html = await self._fetch(section["url"])
                docs = self._parse_section_links(html, section["url"])
                logger.info(f"  Found {len(docs)} documents")

                count = 0
                for doc in docs:
                    result = await self.scrape_document(doc, year, label)
                    if result:
                        count += 1
                    await asyncio.sleep(2)

                self.checkpoint.setdefault("completed", []).append(key)
                self.checkpoint["total"] = self.checkpoint.get("total", 0) + count
                self._save_checkpoint()
                logger.info(f"  Scraped {count}/{len(docs)} documents for {year}")

            except Exception as e:
                logger.error(f"Error scraping section {label}: {e}")

            await asyncio.sleep(3)

        logger.info(f"Practice Notes ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_practice_notes_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = PracticeNotesScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Practice Notes ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_practice_notes_ingestion())
