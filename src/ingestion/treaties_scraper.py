"""
Kenya Legal AI — Treaties Database Scraper
===========================================
Scrapes Kenya's Treaties Database from kenyalaw.org/kl.

Constitutional basis: Article 2(6) — treaties ratified by Kenya
form part of the law of Kenya.

Coverage: All treaties in the Kenya Law Treaties Database.
Saves to: data/raw/kenya_law/treaties/
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
TREATIES_INDEX_URL = "http://kenyalaw.org/kl/index.php?id=treaties-database"


@dataclass
class TreatyRecord:
    """Metadata for an international treaty."""
    title: str
    treaty_number: str
    date_signed: str
    date_ratified: str
    parties: List[str]
    subject: str
    url: str
    source_file: Optional[str] = None


class TreatiesScraper:
    """Scraper for Kenya's Treaties Database."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "treaties"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "treaties_checkpoint.json"
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
        return {"visited": [], "total": 0}

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

    def _parse_treaty_links(self, html: str) -> List[dict]:
        """Parse the treaties index page for individual treaty links."""
        soup = BeautifulSoup(html, "lxml")
        treaties = []

        # Treaties are usually in table rows or definition list
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 8:
                continue
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue

            # Skip nav links
            if any(skip in text.lower() for skip in ["home", "back", "next", "previous", "search"]):
                continue

            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            treaties.append({"title": text, "url": full_url})

        return treaties

    def _parse_treaty_page(self, html: str, url: str) -> tuple:
        """Extract treaty metadata and text from a single treaty page."""
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("h1") or soup.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Treaty"

        # Try to extract metadata from a definition list or table
        signed = ""
        ratified = ""
        parties = []
        subject = ""
        treaty_number = ""

        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            val = dd.get_text(strip=True) if dd else ""
            if "sign" in label:
                signed = val
            elif "ratif" in label or "deposit" in label:
                ratified = val
            elif "part" in label or "state" in label:
                parties = [p.strip() for p in val.split(",")]
            elif "subject" in label or "topic" in label:
                subject = val
            elif "number" in label or "no." in label:
                treaty_number = val

        # Also try table format
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) == 2:
                label = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                if "sign" in label and not signed:
                    signed = val
                elif "ratif" in label and not ratified:
                    ratified = val

        content_div = soup.select_one(".document-content, .akn-body, #content, .field-item")
        text = content_div.get_text(separator="\n", strip=True) if content_div else ""

        metadata = TreatyRecord(
            title=title,
            treaty_number=treaty_number,
            date_signed=signed,
            date_ratified=ratified,
            parties=parties,
            subject=subject,
            url=url,
        )
        return metadata, text

    async def scrape_treaty(self, treaty_info: dict) -> Optional[dict]:
        """Scrape a single treaty record."""
        async with self.semaphore:
            url = treaty_info["url"]
            if url in self.checkpoint.get("visited", []):
                return None
            try:
                html = await self._fetch(url)
                metadata, text = self._parse_treaty_page(html, url)

                safe_title = re.sub(r"[^\w\-]", "_", metadata.title)[:100]
                doc_dir = self.output_dir / safe_title
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    soup = BeautifulSoup(html, "lxml")
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="/source"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "treaty.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF failed: {e}")

                (doc_dir / "metadata.json").write_text(
                    json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
                )
                self.checkpoint.setdefault("visited", []).append(url)
                self.checkpoint["total"] = self.checkpoint.get("total", 0) + 1
                self._save_checkpoint()
                logger.info(f"Scraped treaty: {metadata.title[:60]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed treaty {url}: {e}")
                return None

    async def run_bulk_ingestion(self, limit: Optional[int] = None):
        """Scrape all treaties from the database."""
        html = await self._fetch(TREATIES_INDEX_URL)
        treaties = self._parse_treaty_links(html)
        if limit:
            treaties = treaties[:limit]

        logger.info(f"Treaties Database: {len(treaties)} treaties found")
        for treaty in treaties:
            await self.scrape_treaty(treaty)
            await asyncio.sleep(2)

        logger.info(f"Treaties ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_treaties_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = TreatiesScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Treaties ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_treaties_ingestion())
